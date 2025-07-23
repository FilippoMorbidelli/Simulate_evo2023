#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) out vec4 fragColor;

const vec3 gamma = vec3(2.2);
const vec3 inv_gamma = 1 / gamma;

uniform sampler2DArray u_texture_array_0;

in vec2 uv;
in float shading;
//in vec3 frag_pos;

flat in int voxel_id;
flat in int face_id;

void main() {
    //vec2 quad_scale = vec2(length(dFdx(frag_pos)), length(dFdy(frag_pos)));
    vec2 face_uv = uv * quad_scale;
    // face_uv.x = uv.x / 3.0 - min(face_id, 2) / 3.0;

    vec3 tex_col = texture(u_texture_array_0, vec3(face_uv, voxel_id * 3.0 + min(face_id, 2))).rgb;
    tex_col = pow(tex_col, gamma);

    tex_col *= shading;

    tex_col = pow(tex_col, inv_gamma);
    fragColor = vec4(tex_col, 1);
}