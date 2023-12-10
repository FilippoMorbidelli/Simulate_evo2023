#version 330
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

out vec4 fragColor;
uniform sampler2D u_texture;
in vec2 v_uv;

void main()
{
    fragColor = texture(u_texture, v_uv);
}