#version 330 core
layout(location = 0) in vec2 inPosition;
layout(location = 1) in vec2 inTexCoord;

uniform sampler2D ourTexture;

uniform float outlineThickness;
uniform float centered;

uniform mat4 modelMatrix;
uniform mat4 projectionMatrix;
uniform vec4 uvTransform; // x0,y0,x1,y1

out vec2 vTexCoord;
out vec2 texelSize;

void main() {

    // Compute texel size for outline
    texelSize = (1.0 / vec2(textureSize(ourTexture, 0))) * outlineThickness;

    // Scale the quad for outline
    vec2 scaleModifier = vec2(1,1) + texelSize * 2.0;
    vec2 pos = inPosition * scaleModifier;

    // Transform UV like the Python transform function
    // uvTransform = vec4(x0, y0, x1, y1)
    // equivalent to: uv * (x1-x0, y1-y0) + (x0, y0)
    vec2 uv = inTexCoord * (uvTransform.zw - uvTransform.xy) + uvTransform.xy;

    // Scale UVs similarly for outline
    vec2 txc = uv * scaleModifier;

    if (centered == 0.0) {
        pos -= texelSize;
        txc -= texelSize;
    }

    gl_Position = projectionMatrix * modelMatrix * vec4(pos, 0.0, 1.0);
    vTexCoord = txc;

    // --- fallback standard render section, same transform ---
    // Commented out to avoid overwriting outline
    // gl_Position = projectionMatrix * modelMatrix * vec4(inPosition, 0.0, 1.0);
    // vTexCoord = inTexCoord*(uvTransform.ba - uvTransform.rg) + uvTransform.rg;
}
