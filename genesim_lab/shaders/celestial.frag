#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) out vec4 fragColor;

uniform sampler2DArray u_texture_array_sky;

in vec2 uv;

flat in int face_id;
flat in int body_id;


void main() {
    vec2 face_uv = uv;
    face_uv.x = uv.x / 3.0 - min(face_id, 2) / 3.0;

    vec3 tex_col = texture(u_texture_array_sky, vec3(face_uv, body_id)).rgb;

    fragColor = vec4(tex_col, 1);
}