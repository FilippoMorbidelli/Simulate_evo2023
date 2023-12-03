#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) out vec4 fragColor;

in vec3 color;

void main() {
    fragColor = vec4(color, 1.0);
}