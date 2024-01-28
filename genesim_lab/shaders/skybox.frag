#version 330 core

out vec4 fragColor;

in vec3 texCubeCoords;

uniform samplerCube u_texture_cubemap_skybox;

void main() {
    fragColor = texture(u_texture_cubemap_skybox, texCubeCoords);
}