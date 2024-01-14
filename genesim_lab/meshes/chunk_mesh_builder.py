# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


# World generator ------------------------------|
def get_chunk_index(world_voxel_pos, dim):
    wx, wy, wz = world_voxel_pos
    cx = wx // dim.c_size
    cy = wy // dim.c_size
    cz = wz // dim.c_size
    if not (0 <= cx < dim.w_width and 0 <= cy < dim.w_height and 0 <= cz < dim.w_depth):
        return - 1

    index = cx + dim.w_width * cz + dim.w_area * cy
    return index


def is_void(local_voxel_pos, world_voxel_pos, world_voxels, dim):
    chunk_index = get_chunk_index(world_voxel_pos, dim)
    if chunk_index == -1:
        return False
    chunk_voxels = world_voxels[chunk_index]

    x, y, z = local_voxel_pos
    voxel_index = x % dim.c_size + z % dim.c_size * dim.c_size + y % dim.c_size * dim.c_area

    if chunk_voxels[voxel_index]:
        return False
    return True


def add_data(vertex_data, extra_data, index, properties, *vertices):
    # Iterate over each vertex (6 total for a quad, 2 triangles)
    for vertex in vertices:
        vertex_data[index*3:index*3+3] = vertex  # Save vertex data to vert buffer array
        extra_data[index*2:index*2+2] = properties  # Save additional data to extra buffer array
        index += 1
    return index


def build_chunk_mesh(chunk_voxels, format_size, dim, chunk_pos, world_voxels):
    # Array containing each vertex to render (3 x N) - type: float16 to allow shape customization
    vertex_data = np.empty(dim.c_vol * 18 * format_size[0], dtype='float16')
    # Array containing additional properties [Voxel_ID, Face_ID] - type: uint8 to reduce memory size
    extra_data = np.empty(dim.c_vol * 18 * format_size[1], dtype='uint8')
    # Init index to extract actual size of matrix
    index = 0

    # Iterate over each dimension, compute the vertex of the only visible faces
    for x_ind in range(dim.c_size):
        x = x_ind * dim.v_x  # x coordinate modified with custom stretch
        x_plus = x + dim.v_x  # x plus coordinate
        for y_ind in range(dim.c_size):
            y = y_ind * dim.v_y  # y coordinate modified with custom stretch
            y_plus = y + dim.v_y   # y plus coordinate
            for z_ind in range(dim.c_size):
                z = z_ind * dim.v_z  # z coordinate modified with custom stretch
                z_plus = z + dim.v_z   # z plus coordinate

                # Retrieve Voxel_ID for the given quad to plot and verify that it is not Null
                voxel_id = chunk_voxels[x_ind + dim.c_size * z_ind + dim.c_area * y_ind]
                if not voxel_id:
                    continue

                # Voxels world position
                cx, cy, cz = chunk_pos
                wx = int(x_ind + cx / dim.v_x * dim.c_size)
                wy = int(y_ind + cy / dim.v_y * dim.c_size)
                wz = int(z_ind + cz / dim.v_z * dim.c_size)

                # top face
                if is_void((x_ind, y_ind + 1, z_ind), (wx, wy + 1, wz), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y_plus, z     )
                    v1 = (x_plus, y_plus, z     )
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x     , y_plus, z_plus)
                    properties = [voxel_id, 0]  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v3, v2, v0, v2, v1)

                # bottom face
                if is_void((x_ind, y_ind - 1, z_ind), (wx, wy - 1, wz), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y, z     )
                    v1 = (x_plus, y, z     )
                    v2 = (x_plus, y, z_plus)
                    v3 = (x     , y, z_plus)
                    properties = [voxel_id, 1]  # Voxel_ID and Face_ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v2, v3, v0, v1, v2)

                # right face
                if is_void((x_ind + 1, y_ind, z_ind), (wx + 1, wy, wz), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x_plus, y     , z     )
                    v1 = (x_plus, y_plus, z     )
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x_plus, y     , z_plus)
                    properties = [voxel_id, 2]  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v1, v2, v0, v2, v3)

                # left face
                if is_void((x_ind - 1, y_ind, z_ind), (wx - 1, wy, wz), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x, y     , z     )
                    v1 = (x, y_plus, z     )
                    v2 = (x, y_plus, z_plus)
                    v3 = (x, y     , z_plus)
                    properties = [voxel_id, 3]  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v2, v1, v0, v3, v2)

                # back face
                if is_void((x_ind, y_ind, z_ind - 1), (wx, wy, wz - 1), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y     , z)
                    v1 = (x     , y_plus, z)
                    v2 = (x_plus, y_plus, z)
                    v3 = (x_plus, y     , z)
                    properties = [voxel_id, 4]  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v1, v2, v0, v2, v3)

                # front face
                if is_void((x_ind, y_ind, z_ind + 1), (wx, wy, wz + 1), world_voxels, dim):
                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y     , z_plus)
                    v1 = (x     , y_plus, z_plus)
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x_plus, y     , z_plus)
                    properties = [voxel_id, 5]  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, v0, v2, v1, v0, v3, v2)

    return vertex_data[:index*3 + 1], extra_data[:index*2 + 1]
