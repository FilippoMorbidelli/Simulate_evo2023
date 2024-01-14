# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from numba import uint8
from numba import float32


# World generator ------------------------------|
@njit
def get_ao(local_pos, world_pos, world_voxels, plane, c_size, c_area, w_width, w_height, w_depth, w_area):
    x, y, z = local_pos
    wx, wy, wz = world_pos

    if plane == 'Y':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x    , y, z - 1), (wx    , wy, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        b = is_void((x - 1, y, z - 1), (wx - 1, wy, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        c = is_void((x - 1, y, z    ), (wx - 1, wy, wz    ), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        d = is_void((x - 1, y, z + 1), (wx - 1, wy, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        e = is_void((x    , y, z + 1), (wx    , wy, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        f = is_void((x + 1, y, z + 1), (wx + 1, wy, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        g = is_void((x + 1, y, z    ), (wx + 1, wy, wz    ), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        h = is_void((x + 1, y, z - 1), (wx + 1, wy, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
    elif plane == 'X':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x, y, z - 1), (wx, wy, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        b = is_void((x, y - 1, z - 1), (wx, wy - 1, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        c = is_void((x, y - 1, z), (wx, wy - 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        d = is_void((x, y - 1, z + 1), (wx, wy - 1, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        e = is_void((x, y, z + 1), (wx, wy, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        f = is_void((x, y + 1, z + 1), (wx, wy + 1, wz + 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        g = is_void((x, y + 1, z), (wx, wy + 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        h = is_void((x, y + 1, z - 1), (wx, wy + 1, wz - 1), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
    else:
        a = is_void((x - 1, y, z), (wx - 1, wy, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        b = is_void((x - 1, y - 1, z), (wx - 1, wy - 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        c = is_void((x, y - 1, z), (wx, wy - 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        d = is_void((x + 1, y - 1, z), (wx + 1, wy - 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        e = is_void((x + 1, y, z), (wx + 1, wy, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        f = is_void((x + 1, y + 1, z), (wx + 1, wy + 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        g = is_void((x, y + 1, z), (wx, wy + 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)
        h = is_void((x - 1, y + 1, z), (wx - 1, wy + 1, wz), world_voxels,
                    c_size, c_area, w_width, w_height, w_depth, w_area)

    ao = (a + b + c), (g + h + a), (e + f + g), (c + d + e)
    return to_uint8_ao(ao)


@njit
def to_uint8(voxel_id, face_id):
    return uint8(voxel_id), uint8(face_id)


@njit
def to_uint8_ao(ao):
    return uint8(ao)


@njit
def get_chunk_index(world_voxel_pos, c_size, w_width, w_height, w_depth, w_area):
    wx, wy, wz = world_voxel_pos
    cx = wx // c_size
    cy = wy // c_size
    cz = wz // c_size
    if not (0 <= cx < w_width and 0 <= cy < w_height and 0 <= cz < w_depth):
        return - 1

    index = cx + w_width * cz + w_area * cy
    return index


@njit
def is_void(local_voxel_pos, world_voxel_pos, world_voxels, c_size, c_area, w_width, w_height, w_depth, w_area):
    chunk_index = get_chunk_index(world_voxel_pos, c_size, w_width, w_height, w_depth, w_area)
    if chunk_index == -1:
        return False
    chunk_voxels = world_voxels[chunk_index]

    x, y, z = local_voxel_pos
    voxel_index = x % c_size + z % c_size * c_size + y % c_size * c_area

    if chunk_voxels[voxel_index]:
        return False
    return True


@njit
def add_data(vertex_data, extra_data, index, properties, ao, *vertices):
    # Iterate over each vertex (6 total for a quad, 2 triangles)
    for vertex, ao_value in zip(vertices, ao):
        vertex_data[index*3:index*3+3] = vertex  # Save vertex data to vert buffer array
        extra_data[index*3:index*3+2] = properties  # Save additional data to extra buffer array
        extra_data[index*3+2] = ao_value
        index += 1
    return index


@njit
def build_chunk_mesh(chunk_voxels, format_size, chunk_pos, world_voxels, c_size, c_area, c_vol, v_x, v_y, v_z, w_width,
                     w_height, w_depth, w_area):
    # Array containing each vertex to render (3 x N) - type: float32 to allow shape customization
    vertex_data = np.empty(c_vol * 18 * format_size[0], dtype='float32')
    # Array containing additional properties [Voxel_ID, Face_ID] - type: uint8 to reduce memory size
    extra_data = np.empty(c_vol * 18 * format_size[1], dtype='uint8')
    # Init index to extract actual size of matrix
    index = 0

    # Iterate over each dimension, compute the vertex of the only visible faces
    for x_ind in range(c_size):
        x = x_ind * v_x  # x coordinate modified with custom stretch
        x_plus = x + v_x  # x plus coordinate
        for y_ind in range(c_size):
            y = y_ind * v_y  # y coordinate modified with custom stretch
            y_plus = y + v_y   # y plus coordinate
            for z_ind in range(c_size):
                z = z_ind * v_z  # z coordinate modified with custom stretch
                z_plus = z + v_z   # z plus coordinate

                # Retrieve Voxel_ID for the given quad to plot and verify that it is not Null
                voxel_id = chunk_voxels[x_ind + c_size * z_ind + c_area * y_ind]
                if not voxel_id:
                    continue

                # Voxels world position
                cx, cy, cz = chunk_pos
                wx = int(x_ind + cx / v_x * c_size)
                wy = int(y_ind + cy / v_y * c_size)
                wz = int(z_ind + cz / v_z * c_size)

                # top face
                if is_void((x_ind, y_ind + 1, z_ind), (wx, wy + 1, wz), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind + 1, z_ind), (wx, wy + 1, wz), world_voxels, 'Y',
                           c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[3], ao[2], ao[0], ao[2], ao[1]]

                    # format: [x, y, z, ao_id] - [voxel_id, face_id]
                    v0 = (x     , y_plus, z     )
                    v1 = (x_plus, y_plus, z     )
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x     , y_plus, z_plus)
                    properties = to_uint8(voxel_id, 0)  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v3, v2, v0, v2, v1)

                # bottom face
                if is_void((x_ind, y_ind - 1, z_ind), (wx, wy - 1, wz), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind - 1, z_ind), (wx, wy - 1, wz), world_voxels, 'Y',
                                c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[2], ao[3], ao[0], ao[1], ao[2]]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y, z     )
                    v1 = (x_plus, y, z     )
                    v2 = (x_plus, y, z_plus)
                    v3 = (x     , y, z_plus)
                    properties = to_uint8(voxel_id, 1)  # Voxel_ID and Face_ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v2, v3, v0, v1, v2)

                # right face
                if is_void((x_ind + 1, y_ind, z_ind), (wx + 1, wy, wz), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind + 1, y_ind, z_ind), (wx + 1, wy, wz), world_voxels, 'X',
                                c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[1], ao[2], ao[0], ao[2], ao[3]]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x_plus, y     , z     )
                    v1 = (x_plus, y_plus, z     )
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x_plus, y     , z_plus)
                    properties = to_uint8(voxel_id, 2)  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v1, v2, v0, v2, v3)

                # left face
                if is_void((x_ind - 1, y_ind, z_ind), (wx - 1, wy, wz), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind - 1, y_ind, z_ind), (wx - 1, wy, wz), world_voxels, 'X',
                                c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[2], ao[1], ao[0], ao[3], ao[2]]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x, y     , z     )
                    v1 = (x, y_plus, z     )
                    v2 = (x, y_plus, z_plus)
                    v3 = (x, y     , z_plus)
                    properties = to_uint8(voxel_id, 3)  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v2, v1, v0, v3, v2)

                # back face
                if is_void((x_ind, y_ind, z_ind - 1), (wx, wy, wz - 1), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind - 1), (wx, wy, wz - 1), world_voxels, 'Z',
                                c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[1], ao[2], ao[0], ao[2], ao[3]]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y     , z)
                    v1 = (x     , y_plus, z)
                    v2 = (x_plus, y_plus, z)
                    v3 = (x_plus, y     , z)
                    properties = to_uint8(voxel_id, 4)  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v1, v2, v0, v2, v3)

                # front face
                if is_void((x_ind, y_ind, z_ind + 1), (wx, wy, wz + 1), world_voxels,
                           c_size, c_area, w_width, w_height, w_depth, w_area):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind + 1), (wx, wy, wz + 1), world_voxels,  'Z',
                                c_size, c_area, w_width, w_height, w_depth, w_area)
                    ao = [ao[0], ao[2], ao[1], ao[0], ao[3], ao[2]]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = (x     , y     , z_plus)
                    v1 = (x     , y_plus, z_plus)
                    v2 = (x_plus, y_plus, z_plus)
                    v3 = (x_plus, y     , z_plus)
                    properties = to_uint8(voxel_id, 5)  # Voxel ID and Face ID

                    index = add_data(vertex_data, extra_data, index, properties, ao, v0, v2, v1, v0, v3, v2)

    return vertex_data[:index*3 + 1], extra_data[:index*3 + 1]
