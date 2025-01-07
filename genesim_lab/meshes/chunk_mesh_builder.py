# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from numba import uint8
from numba import float32
from numba import njit

import numpy as np
import numpy.ma as ma

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
    # x: 6bit, y: 6bit, z: 6bit, voxel_id: 8bit, face_id: 3bit, ao_id: 2bit, flip_id: 1bit
    a, b, c, d, e, f, g = x, y, z, voxel_id, face_id, ao_id, flip_id

    b_bit, c_bit, d_bit, e_bit, f_bit, g_bit = 6, 6, 8, 3, 2, 1
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
def greedy_pack_data(x, y, z, voxel_id, face_id):
    # x: 6bit, y: 6bit, z: 6bit, voxel_id: 8bit, face_id: 3bit, void --> 3bit
    a, b, c, d, e = x, y, z, voxel_id, face_id

    b_bit, c_bit, d_bit, e_bit = 6, 6, 8, 3
    de_bit = d_bit + e_bit
    cde_bit = c_bit + de_bit
    bcde_bit = b_bit + cde_bit

    packed_data = (
        a << bcde_bit |
        b << cde_bit |
        c << de_bit |
        d << e_bit | e
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
def bit_length(v):
    r =     (v > 0xFFFFFFFF) << 5; v >>= r
    shift = (v > 0xFFFF) << 4; v >>= shift; r |= shift
    shift = (v > 0xFF  ) << 3; v >>= shift; r |= shift
    shift = (v > 0xF   ) << 2; v >>= shift; r |= shift
    shift = (v > 0x3   ) << 1; v >>= shift; r |= shift

    return  r | (v >> 1)


@njit
def greedy_mesh_builder(v_mask, face, voxel, level, gvd, indexGreedy):
    row_length = c_size

    for row in range(row_length):
        h = 0
        while h < row_length:
            # Find the first solid bit (non-zero bit)
            tmp_trl_zeros = bit_length(v_mask[row] >> h & - v_mask[row] >> h) - 1
            h += tmp_trl_zeros + 1 if tmp_trl_zeros >= 0 else row_length
            if h >= row_length:
                continue  # Reached the top

            # Find the height of contiguous ones starting at `h`
            tmp_trl_ones = bit_length(~(v_mask[row] >> h) & - ~(v_mask[row] >> h)) - 1
            trailing_ones = tmp_trl_ones + 1 if tmp_trl_ones >= 0 else 0

            # Create a mask for the height
            h_as_mask = (1 << trailing_ones) - 1 if trailing_ones > 0 else 0
            mask = h_as_mask << h

            # Grow horizontally
            w = 1
            while row + w < row_length:
                # Fetch bits spanning height in the next row
                next_row_h = (v_mask[row + w] >> h) & h_as_mask
                if next_row_h != h_as_mask:
                    break  # Can no longer expand horizontally

                # Remove the bits we expanded into
                v_mask[row + w] &= ~mask

                w += 1

            # Compute the two triangles and append them
            match face:
                case 0:  # Top
                    v0 = greedy_pack_data(row, level + 1, h, voxel, face)
                    v1 = greedy_pack_data(row + w, level + 1, h, voxel, face)
                    v2 = greedy_pack_data(row + w, level + 1, h + trailing_ones, voxel, face)
                    v3 = greedy_pack_data(row, level + 1, h + trailing_ones, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 1:  # Bottom
                    v0 = greedy_pack_data(row, level, h, voxel, face)
                    v1 = greedy_pack_data(row + w, level, h, voxel, face)
                    v2 = greedy_pack_data(row + w, level, h + trailing_ones, voxel, face)
                    v3 = greedy_pack_data(row, level, h + trailing_ones, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 2:  # Right
                    v0 = greedy_pack_data(level + 1, h, row, voxel, face)
                    v1 = greedy_pack_data(level + 1, h + trailing_ones, row, voxel, face)
                    v2 = greedy_pack_data(level + 1, h + trailing_ones, row + w, voxel, face)
                    v3 = greedy_pack_data(level + 1, h, row + w, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 3:  # Left
                    v0 = greedy_pack_data(level, h, row, voxel, face)
                    v1 = greedy_pack_data(level, h + trailing_ones, row, voxel, face)
                    v2 = greedy_pack_data(level, h + trailing_ones, row + w, voxel, face)
                    v3 = greedy_pack_data(level, h, row + w, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 4:  # Forward
                    v0 = greedy_pack_data(row, h, level + 1, voxel, face)
                    v1 = greedy_pack_data(row, h + trailing_ones, level + 1, voxel, face)
                    v2 = greedy_pack_data(row + w, h + trailing_ones, level + 1, voxel, face)
                    v3 = greedy_pack_data(row + w, h, level + 1, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 5:  # Backward
                    v0 = greedy_pack_data(row, h, level, voxel, face)
                    v1 = greedy_pack_data(row, h + trailing_ones, level, voxel, face)
                    v2 = greedy_pack_data(row + w, h + trailing_ones, level, voxel, face)
                    v3 = greedy_pack_data(row + w, h, level, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

            h += trailing_ones

    return indexGreedy


@njit
def build_chunk_mesh(chunk_voxels, format_size, chunk_pos, world_voxels):
    # Array containing additional properties [Voxel_ID, Face_ID] - type: uint8 to reduce memory size
    vertex_data = np.empty(c_vol * 18 * format_size, dtype='uint32')
    # Array containing voxel type per face, after culling (used by greedy meshing algo)
    greedy_raw_data = np.zeros((c_vol, 6), dtype = 'uint8')
    greedy_vertex_data = np.empty(c_vol * 18 * format_size, dtype='uint32')
    # Init index to extract actual size of matrix
    index = 0
    indexGreedy = 0

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[x_ind + c_size * z_ind + c_area * y_ind, 0] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 0)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 0)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 0)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 0)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[x_ind + c_size * z_ind + c_area * y_ind, 1] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 1)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 1)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 1)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 1)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[z_ind + c_size * y_ind + c_area * x_ind, 2] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 2)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 2)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 2)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 2)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[z_ind + c_size * y_ind + c_area * x_ind, 3] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 3)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 3)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 3)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 3)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[x_ind + c_size * y_ind + c_area * z_ind, 4] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 4)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 4)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 4)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 4)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

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

                    # save data for greedy meshing
                    if voxel_id < 2: # To Be Defined (value of id that can be greedy meshed)
                        greedy_raw_data[x_ind + c_size * y_ind + c_area * z_ind, 5] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 5)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 5)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 5)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 5)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

    # Build fast greedy mesh
    new_mask = np.zeros(c_size, dtype = "int64")
    for v_type in range(1, 2): # Iterate over each meshable voxel type
        for face in range(6):
            for cut in range(c_size):
                raw_mask = greedy_raw_data[cut * c_area : (cut + 1) * c_area, face] == v_type
                if raw_mask.any():
                    for it_m in range(c_size):
                        new_mask[it_m] = np.sum(powers * raw_mask[it_m * c_size : (it_m + 1) * c_size])
                    indexGreedy = greedy_mesh_builder(new_mask, face, v_type, cut, greedy_vertex_data, indexGreedy)

    # Truncate Vertex Data array
    if not index:
        vertex_data = vertex_data[:index + 1]
    else:
        vertex_data = vertex_data[:index]

    if not indexGreedy:
        greedy_vertex_data = greedy_vertex_data[:indexGreedy + 1]
    else:
        greedy_vertex_data = greedy_vertex_data[:indexGreedy]

    return vertex_data, greedy_vertex_data