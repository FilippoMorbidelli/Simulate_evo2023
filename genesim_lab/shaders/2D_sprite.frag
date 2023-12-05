#version 330
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

void main()
{
    v_uv = in_uv;
    gl_Position = vec4(in_position, 0.0, 1.0);
}