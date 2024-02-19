#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) in uvec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform vec3 scale;

void main() {
    gl_Position = m_proj * m_view * m_model * vec4(in_position * scale, 1.0);
}