#version 330 core
in vec2 vTexCoord;
out vec4 FragColor;

uniform sampler2D ourTexture;
uniform mat4 uvTransform;
uniform vec4 fogColor;
uniform float transparency;

void main() {
    vec4 color = texture(ourTexture, vTexCoord);
    color.a *= (1-transparency);
    if(color.a < 0.01)
        discard;

    FragColor = vec4(mix(color.rgb, fogColor.rgb, fogColor.a), color.a);
}