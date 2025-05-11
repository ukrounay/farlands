#version 330 core
out vec4 FragColor;
in vec2 TexCoord;

uniform sampler2D screenTexture;  // Input texture to blur
uniform vec2 screenSize; // (window_width, window_height)
uniform float Size;               // Blur size (radius)

void main()
{
    float Quality = 1;
    float Directions = 2;
    float Pi = 6.28318530718;  // Pi * 2
    vec2 Radius = Size / screenSize;

    // Pixel coordinates
    vec4 Color = texture(screenTexture, TexCoord);

    // Gaussian blur loop
    for (float d = 0.0; d < Pi; d += Pi / Directions) {
        for (float i = 1.0 / Quality; i <= 1.0; i += 1.0 / Quality) {
            Color += texture(screenTexture, TexCoord + vec2(cos(d), sin(d)) * Radius * i);
        }
    }

    // Normalize the color
    Color /= Quality * Directions - 15.0;

    FragColor = Color;
}
