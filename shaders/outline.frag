#version 330 core
in vec2 vTexCoord;
out vec4 FragColor;

uniform vec4 outlineColor;

uniform sampler2D ourTexture;
uniform mat4 uvTransform;
uniform vec4 fogColor;
uniform float transparency;

in float screenTexelSize; // (1.0 / screen_width, 1.0 / screen_height)
in vec2 texelSize;


bool isInBounds(vec2 coords) {
    return coords.x > 1 || coords.y > 1 || coords.x < 0 || coords.y < 0;
}

void main() {
    vec4 color = texture(ourTexture, vTexCoord);
    if (isInBounds(vTexCoord)) {
        color.a = 0;
    }
    if (color.a < 0.01) {
        // Check neighbors in screen space for non-transparent alpha
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                if (x == 0 && y == 0) continue;
                vec2 offset = vec2(x, y) * texelSize;
                vec2 o = vTexCoord + offset;
                float alpha = texture(ourTexture, o).a;
                if (isInBounds(o)) {
                    alpha = 0;
                }
                if (alpha > 0.01) {
                    FragColor = outlineColor; // outline
                    return;
                }
            }
        }
        discard;
    }
//    color.a *= (1.0 - transparency);

    FragColor = vec4(mix(color.rgb, fogColor.rgb, fogColor.a), color.a);

//    FragColor = color;
}
