#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) in vec2 in_tex_coord_0;
layout (location = 1) in vec3 in_position;
layout (location = 2) in int in_face_id;
layout (location = 3) in int in_body_id;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec2 uv;

flat out int face_id;
flat out int body_id;

const int scale[2] = int[2](
    75,   // Sun
    22    // Moon
);

void main() {
    uv = in_tex_coord_0;
    face_id = in_face_id;
    body_id = in_body_id;

    vec4 pos = m_proj * m_view * m_model * vec4(in_position * scale[body_id], 1.0);
    gl_Position = pos;
}