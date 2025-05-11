#version 330 core
layout(location = 0) in vec2 inPosition;
layout(location = 1) in vec2 inTexCoord;

uniform mat4 modelMatrix;
uniform mat4 projectionMatrix;
uniform mat4 uvTransform;

out vec2 vTexCoord;

void main() {
    gl_Position = projectionMatrix * modelMatrix * vec4(inPosition, 0.0, 1.0);
    vTexCoord = (uvTransform * vec4(inTexCoord.x, 1-inTexCoord.y,0,1)).xy;
}
