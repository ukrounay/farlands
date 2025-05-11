#version 330 core
in vec2 vTexCoord;
out vec4 FragColor;

uniform sampler2D image;
uniform vec2 direction; // (1.0, 0.0)=horizontal, (0.0, 1.0)=vertical

void main() {
    float weight[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec2 tex_offset = 1.0 / textureSize(image, 0); // size dependent
    vec3 result = texture(image, vTexCoord).rgb * weight[0];

    for(int i = 1; i < 5; ++i) {
        result += texture(image, vTexCoord + direction * tex_offset * i).rgb * weight[i];
        result += texture(image, vTexCoord - direction * tex_offset * i).rgb * weight[i];
    }

    FragColor = vec4(result, 1.0);
}
