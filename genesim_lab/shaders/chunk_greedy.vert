#version 330 core
#extension GL_ARB_enhanced_layouts : require
#extension GL_ARB_separate_shader_objects : require
#extension GL_ARB_explicit_uniform_location : require

layout (location = 0) in uint packed_data;

int x, y, z;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform vec3 scale;

flat out int voxel_id;
flat out int face_id;

out vec3 voxel_color;
out vec2 uv;

const vec2 uv_coords[4] = vec2[4](
    vec2(0, 0), vec2(0, 1),
    vec2(1, 0), vec2(1, 1)
);

const int uv_indices[12] = int[12](
    1, 0, 2, 1, 2, 3,  // tex coords indices for vertices of an even face
    3, 0, 2, 3, 1, 0   // odd face
);

void unpack(uint packed_data) {
    // a, b, c, d, e = x, y, z, voxel_id, face_id
    uint b_bit = 6u, c_bit = 6u, d_bit = 8u, e_bit = 3u;
    uint b_mask = 63u, c_mask = 63u, d_mask = 255u, e_mask = 7u;
    //
    uint de_bit = d_bit + e_bit;
    uint cde_bit = c_bit + de_bit;
    uint bcde_bit = b_bit + cde_bit;
    // unpacking vertex data
    x = int(packed_data >> bcde_bit);
    y = int((packed_data >> cde_bit) & b_mask);
    z = int((packed_data >> de_bit) & c_mask);
    //
    voxel_id = int((packed_data >> e_bit) & d_mask);
    face_id = int(packed_data & e_mask);
}

void main() {
    unpack(packed_data);

    vec3 in_position = vec3(x, y, z);
    gl_Position = m_proj * m_view * m_model * vec4(in_position * scale, 1.0);

    int uv_index = gl_VertexID % 6 + (face_id & 1) * 6;

    uv = uv_coords[uv_indices[uv_index]];
}