#version 330 core
in vec2 vTexCoord;
out vec4 FragColor;

uniform sampler2D ourTexture;
uniform mat4 uvTransform;
uniform float transparency;

void main() {
    vec4 color = texture(ourTexture, vTexCoord);
    color.a *= (1-transparency);
    if(color.a < 0.01)
        discard;

    FragColor = color;

//    vec3 color = texture(ourTexture, vTexCoord).rgb;
//    float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722));
//    if (brightness > 0.8) {
//        FragColor = vec4(color, 1.0);  // Keep bright parts
//    } else {
//        FragColor = vec4(0.0);
//    }
}