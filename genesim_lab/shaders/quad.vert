#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_color;

out vec3 color;

void main() {
    color = in_color;
    gl_Position = vec4(in_position, 1.0);
}