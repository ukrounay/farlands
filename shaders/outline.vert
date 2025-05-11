#version 330 core
layout(location = 0) in vec2 inPosition;
layout(location = 1) in vec2 inTexCoord;

uniform sampler2D ourTexture;

uniform float outlineThickness;

uniform mat4 modelMatrix;
uniform mat4 projectionMatrix;
uniform mat4 uvTransform;

out vec2 vTexCoord;
out vec2 texelSize;

void main() {


    texelSize = (1.0 / vec2(textureSize(ourTexture, 0))) * outlineThickness;
    vec2 scaleModifier = vec2(1,1) + texelSize * 2;

    vec2 pos = inPosition * scaleModifier - texelSize;
    vec2 txc = inTexCoord * scaleModifier - texelSize;
    gl_Position = projectionMatrix * modelMatrix * vec4(pos, 0.0, 1.0);
    vTexCoord = (uvTransform * vec4(txc.x, 1-txc.y,0,1)).xy;
}
