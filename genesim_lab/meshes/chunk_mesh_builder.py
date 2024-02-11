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
def get_ao(local_pos, world_pos, world_voxels, plane):
    x, y, z = local_pos
    wx, wy, wz = world_pos

    if plane == 'Y':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x    , y, z - 1), (wx    , wy, wz - 1), world_voxels)
        b = is_void((x - 1, y, z - 1), (wx - 1, wy, wz - 1), world_voxels)
        c = is_void((x - 1, y, z    ), (wx - 1, wy, wz    ), world_voxels)
        d = is_void((x - 1, y, z + 1), (wx - 1, wy, wz + 1), world_voxels)
        e = is_void((x    , y, z + 1), (wx    , wy, wz + 1), world_voxels)
        f = is_void((x + 1, y, z + 1), (wx + 1, wy, wz + 1), world_voxels)
        g = is_void((x + 1, y, z    ), (wx + 1, wy, wz    ), world_voxels)
        h = is_void((x + 1, y, z - 1), (wx + 1, wy, wz - 1), world_voxels)
    elif plane == 'X':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x, y, z - 1), (wx, wy, wz - 1), world_voxels)
        b = is_void((x, y - 1, z - 1), (wx, wy - v_y, wz - 1), world_voxels)
        c = is_void((x, y - 1, z), (wx, wy - v_y, wz), world_voxels)
        d = is_void((x, y - 1, z + 1), (wx, wy - v_y, wz + 1), world_voxels)
        e = is_void((x, y, z + 1), (wx, wy, wz + 1), world_voxels)
        f = is_void((x, y + 1, z + 1), (wx, wy + v_y, wz + 1), world_voxels)
        g = is_void((x, y + 1, z), (wx, wy + v_y, wz), world_voxels)
        h = is_void((x, y + 1, z - 1), (wx, wy + v_y, wz - 1), world_voxels)
    else:
        a = is_void((x - 1, y, z), (wx - 1, wy, wz), world_voxels)
        b = is_void((x - 1, y - 1, z), (wx - 1, wy - v_y, wz), world_voxels)
        c = is_void((x, y - 1, z), (wx, wy - v_y, wz), world_voxels)
        d = is_void((x + 1, y - 1, z), (wx + 1, wy - v_y, wz), world_voxels)
        e = is_void((x + 1, y, z), (wx + 1, wy, wz), world_voxels)
        f = is_void((x + 1, y + 1, z), (wx + 1, wy + v_y, wz), world_voxels)
        g = is_void((x, y + 1, z), (wx, wy + v_y, wz), world_voxels)
        h = is_void((x - 1, y + 1, z), (wx - 1, wy + v_y, wz), world_voxels)

    ao = (a + b + c), (g + h + a), (e + f + g), (c + d + e)
    return to_uint8_ao(ao)


@njit
def pack_data(x, y, z, voxel_id, face_id, flip_id, ao_id):
    # x: 6bit, y: 6bit, z: 6bit, voxel_id: 8bit, flip_id: 1bit, ao_id: 2bit, face_id: 3bit
    a, b, c, d, e, f, g = x, y, z, voxel_id, flip_id, ao_id, face_id

    b_bit, c_bit, d_bit, e_bit, f_bit, g_bit = 6, 6, 8, 1, 2, 3
    fg_bit = f_bit + g_bit
    efg_bit = e_bit + fg_bit
    defg_bit = d_bit + efg_bit
    cdefg_bit = c_bit + defg_bit
    bcdefg_bit = b_bit + cdefg_bit

    packed_data = (
        a << bcdefg_bit |
        b << cdefg_bit |
        c << defg_bit |
        d << efg_bit |
        e << fg_bit |
        f << g_bit | g
    )

    return packed_data


@njit
def to_uint8_ao(ao):
    return uint8(ao)


@njit
def get_chunk_index(world_voxel_pos):
    wx, wy, wz = world_voxel_pos
    cx = wx // c_size + w_width/2
    cy = wy // (c_size * v_y) + 0
    cz = wz // c_size + w_depth/2
    if not (0 <= cx < w_width and 0 <= cy < w_height and 0 <= cz < w_depth):
        return - 1

    index = cx + w_width * cz + w_area * cy
    return int(index)


@njit
def is_void(local_voxel_pos, world_voxel_pos, world_voxels):
    chunk_index = get_chunk_index(world_voxel_pos)
    if chunk_index == -1:
        return False
    chunk_voxels = world_voxels[chunk_index]

    x, y, z = local_voxel_pos
    voxel_index = x % c_size + z % c_size * c_size + y % c_size * c_area

    if chunk_voxels[voxel_index]:
        return False
    return True


@njit
def add_data(vertex_data, index, *vertices):
    # Iterate over each vertex (6 total for a quad, 2 triangles)
    for vertex in vertices:
        vertex_data[index] = vertex  # Save vertex data to vert buffer array
        index += 1
    return index


@njit
def build_chunk_mesh(chunk_voxels, format_size, chunk_pos, world_voxels):
    # Array containing additional properties [Voxel_ID, Face_ID] - type: uint8 to reduce memory size
    vertex_data = np.empty(c_vol * 18 * format_size, dtype='uint32')
    # Init index to extract actual size of matrix
    index = 0

    # Iterate over each dimension, compute the vertex of the only visible faces
    for x_ind in range(c_size):
        x_plus = x_ind + 1  # x plus coordinate
        for y_ind in range(c_size):
            y_plus = y_ind + 1   # y plus coordinate
            for z_ind in range(c_size):
                z_plus = z_ind + 1   # z plus coordinate

                # Retrieve Voxel_ID for the given quad to plot and verify that it is not Null
                voxel_id = chunk_voxels[x_ind + c_size * z_ind + c_area * y_ind]
                if not voxel_id:
                    continue

                # Voxels world position
                cx, cy, cz = chunk_pos
                wx = x_ind + (cx - w_width/2) * c_size
                wy = y_ind * v_y + (cy - 0) * v_y * c_size
                wz = z_ind + (cz - w_depth/2) * c_size

                # top face
                if is_void((x_ind, y_ind + 1, z_ind), (wx, wy + v_y, wz), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind + 1, z_ind), (wx, wy + v_y, wz), world_voxels, plane='Y')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z, ao_id] - [voxel_id, face_id]
                    v0 = pack_data(x_ind , y_plus, z_ind , voxel_id, 0, flip_id, ao[0])
                    v1 = pack_data(x_plus, y_plus, z_ind , voxel_id, 0, flip_id, ao[1])
                    v2 = pack_data(x_plus, y_plus, z_plus, voxel_id, 0, flip_id, ao[2])
                    v3 = pack_data(x_ind , y_plus, z_plus, voxel_id, 0, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v1, v0, v3, v1, v3, v2)
                    else:
                        index = add_data(vertex_data, index, v0, v3, v2, v0, v2, v1)

                # bottom face
                if is_void((x_ind, y_ind - 1, z_ind), (wx, wy - v_y, wz), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind - 1, z_ind), (wx, wy - v_y, wz), world_voxels, plane='Y')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = pack_data(x_ind , y_ind, z_ind , voxel_id, 1, flip_id, ao[0])
                    v1 = pack_data(x_plus, y_ind, z_ind , voxel_id, 1, flip_id, ao[1])
                    v2 = pack_data(x_plus, y_ind, z_plus, voxel_id, 1, flip_id, ao[2])
                    v3 = pack_data(x_ind , y_ind, z_plus, voxel_id, 1, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v1, v3, v0, v1, v2, v3)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v3, v0, v1, v2)

                # right face
                if is_void((x_ind + 1, y_ind, z_ind), (wx + 1, wy, wz), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind + 1, y_ind, z_ind), (wx + 1, wy, wz), world_voxels, plane='X')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = pack_data(x_plus, y_ind , z_ind , voxel_id, 2, flip_id, ao[0])
                    v1 = pack_data(x_plus, y_plus, z_ind , voxel_id, 2, flip_id, ao[1])
                    v2 = pack_data(x_plus, y_plus, z_plus, voxel_id, 2, flip_id, ao[2])
                    v3 = pack_data(x_plus, y_ind , z_plus, voxel_id, 2, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v0, v1, v3, v1, v2)
                    else:

                        index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                # left face
                if is_void((x_ind - 1, y_ind, z_ind), (wx - 1, wy, wz), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind - 1, y_ind, z_ind), (wx - 1, wy, wz), world_voxels, plane='X')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = pack_data(x_ind, y_ind , z_ind , voxel_id, 3, flip_id, ao[0])
                    v1 = pack_data(x_ind, y_plus, z_ind , voxel_id, 3, flip_id, ao[1])
                    v2 = pack_data(x_ind, y_plus, z_plus, voxel_id, 3, flip_id, ao[2])
                    v3 = pack_data(x_ind, y_ind , z_plus, voxel_id, 3, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v1, v0, v3, v2, v1)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

                # back face
                if is_void((x_ind, y_ind, z_ind - 1), (wx, wy, wz - 1), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind - 1), (wx, wy, wz - 1), world_voxels, plane='Z')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = pack_data(x_ind , y_ind , z_ind, voxel_id, 4, flip_id, ao[0])
                    v1 = pack_data(x_ind , y_plus, z_ind, voxel_id, 4, flip_id, ao[1])
                    v2 = pack_data(x_plus, y_plus, z_ind, voxel_id, 4, flip_id, ao[2])
                    v3 = pack_data(x_plus, y_ind , z_ind, voxel_id, 4, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v0, v1, v3, v1, v2)
                    else:

                        index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                # front face
                if is_void((x_ind, y_ind, z_ind + 1), (wx, wy, wz + 1), world_voxels):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind + 1), (wx, wy, wz + 1), world_voxels, plane='Z')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    # format: [x, y, z] - [voxel_id, face_id]
                    v0 = pack_data(x_ind , y_ind , z_plus, voxel_id, 5, flip_id, ao[0])
                    v1 = pack_data(x_ind , y_plus, z_plus, voxel_id, 5, flip_id, ao[1])
                    v2 = pack_data(x_plus, y_plus, z_plus, voxel_id, 5, flip_id, ao[2])
                    v3 = pack_data(x_plus, y_ind , z_plus, voxel_id, 5, flip_id, ao[3])

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v1, v0, v3, v2, v1)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

    return vertex_data[:index + 1]
