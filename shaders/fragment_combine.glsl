#version 330 core
in vec2 vTexCoord;
out vec4 FragColor;

uniform sampler2D scene;
uniform sampler2D bloom;

void main() {
    vec3 sceneColor = texture(scene, vTexCoord).rgb;
    vec3 bloomColor = texture(bloom, vTexCoord).rgb;
    FragColor = vec4(sceneColor + bloomColor * 1.2, 1.0);  // simple additive blend
}
