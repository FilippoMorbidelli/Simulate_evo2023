#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) out vec4 fragColor;

uniform sampler2D u_texture_0;

in vec3 voxel_color;
in vec2 uv;

void main() {
    vec3 tex_col = texture(u_texture_0, uv).rgb;
    fragColor = vec4(tex_col - voxel_color*0.5 + voxel_color*0.5, 1);
}