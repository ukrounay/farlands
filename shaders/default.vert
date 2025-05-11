//#version 330 core
//layout(location = 0) in vec2 inPosition;  // Vertex position (0-1 range)
//layout(location = 1) in vec2 inTexCoord;  // Texture coordinates
//
//uniform vec2 screenSize;
//uniform mat4 modelMatrix;
//uniform mat4 projectionMatrix;
//
//out vec2 vTexCoord;
//
//void main() {
//    // Apply model transformation
//    vec4 worldPos = modelMatrix * vec4(inPosition, 0.0, 1.0);
//    vec4 screenPos = projectionMatrix * worldPos;
//
//    gl_Position = vec4(screenPos.x, screenPos.y, 0.0, 1.0);
//
//    vTexCoord = inTexCoord;
//}

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
