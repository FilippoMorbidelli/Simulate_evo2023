# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.Engine.settings import powers
from numba import uint8
from numba import float32
from numba import njit

import numpy as np

# World generator ------------------------------|
@njit
def get_ao(local_pos, world_pos, world_voxels, plane, stg):
    x, y, z = local_pos
    wx, wy, wz = world_pos

    if plane == 'Y':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x    , y, z - 1), (wx    , wy, wz - 1), world_voxels, stg=stg)
        b = is_void((x - 1, y, z - 1), (wx - 1, wy, wz - 1), world_voxels, stg=stg)
        c = is_void((x - 1, y, z    ), (wx - 1, wy, wz    ), world_voxels, stg=stg)
        d = is_void((x - 1, y, z + 1), (wx - 1, wy, wz + 1), world_voxels, stg=stg)
        e = is_void((x    , y, z + 1), (wx    , wy, wz + 1), world_voxels, stg=stg)
        f = is_void((x + 1, y, z + 1), (wx + 1, wy, wz + 1), world_voxels, stg=stg)
        g = is_void((x + 1, y, z    ), (wx + 1, wy, wz    ), world_voxels, stg=stg)
        h = is_void((x + 1, y, z - 1), (wx + 1, wy, wz - 1), world_voxels, stg=stg)
    elif plane == 'X':  # Valid for Top and Bottom faces (Y axis)
        a = is_void((x, y    , z - 1), (wx, wy          , wz - 1), world_voxels, stg=stg)
        b = is_void((x, y - 1, z - 1), (wx, wy - stg.v_y, wz - 1), world_voxels, stg=stg)
        c = is_void((x, y - 1, z    ), (wx, wy - stg.v_y, wz    ), world_voxels, stg=stg)
        d = is_void((x, y - 1, z + 1), (wx, wy - stg.v_y, wz + 1), world_voxels, stg=stg)
        e = is_void((x, y    , z + 1), (wx, wy          , wz + 1), world_voxels, stg=stg)
        f = is_void((x, y + 1, z + 1), (wx, wy + stg.v_y, wz + 1), world_voxels, stg=stg)
        g = is_void((x, y + 1, z    ), (wx, wy + stg.v_y, wz    ), world_voxels, stg=stg)
        h = is_void((x, y + 1, z - 1), (wx, wy + stg.v_y, wz - 1), world_voxels, stg=stg)
    else:
        a = is_void((x - 1, y    , z), (wx - 1, wy          , wz), world_voxels, stg=stg)
        b = is_void((x - 1, y - 1, z), (wx - 1, wy - stg.v_y, wz), world_voxels, stg=stg)
        c = is_void((x    , y - 1, z), (wx    , wy - stg.v_y, wz), world_voxels, stg=stg)
        d = is_void((x + 1, y - 1, z), (wx + 1, wy - stg.v_y, wz), world_voxels, stg=stg)
        e = is_void((x + 1, y    , z), (wx + 1, wy          , wz), world_voxels, stg=stg)
        f = is_void((x + 1, y + 1, z), (wx + 1, wy + stg.v_y, wz), world_voxels, stg=stg)
        g = is_void((x    , y + 1, z), (wx    , wy + stg.v_y, wz), world_voxels, stg=stg)
        h = is_void((x - 1, y + 1, z), (wx - 1, wy + stg.v_y, wz), world_voxels, stg=stg)

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
def get_chunk_index(world_voxel_pos, stg):
    # Unpack voxel position in world coordinates
    wx, wy, wz = world_voxel_pos
    wx = wx / stg.v_x + stg.off_x * stg.c_size
    wy = wy / stg.v_y + stg.off_y * stg.c_size
    wz = wz / stg.v_z + stg.off_z * stg.c_size
    # Compute region index
    rx = wx // stg.rc_size
    ry = wy // stg.rc_size
    rz = wz // stg.rc_size
    # Compute chunk index
    cx = (wx - rx * stg.rc_size) // stg.c_size
    cy = (wy - ry * stg.rc_size) // stg.c_size
    cz = (wz - rz * stg.rc_size) // stg.c_size
    if not (0 <= rx < stg.width_rn and 0 <= ry < stg.height_rn and 0 <= rz < stg.depth_rn):
        return - 1, -1

    r_index = rx + stg.width_rn * rz + stg.depth_rn * stg.width_rn * ry
    index = cx + stg.r_size * cz + stg.r_area * cy
    return int(r_index), int(index)


@njit
def is_void(local_voxel_pos, world_voxel_pos, world_voxels, stg):
    region_index, chunk_index = get_chunk_index(world_voxel_pos, stg)
    # Out of max world region
    if region_index == -1:
        return True # Put False to not show voxels at world borders TBD (Find a way to block mesh when adjacent chunk doesn't exist but regions yes)
    chunk_voxels = world_voxels.get(region_index)

    if chunk_voxels is not None:
        chunk_voxels = chunk_voxels[chunk_index]

        x, y, z = local_voxel_pos
        voxel_index = x % stg.c_size + z % stg.c_size * stg.c_size + y % stg.c_size * stg.c_area

        if chunk_voxels[voxel_index]:
            return False # Not void so don't create a mesh

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
    # Custom method to compute log2(v)
    # Used to find bit length of v in numba since bit_length method is not implemented
    r =     (v > 0xFFFFFFFF) << 5; v >>= r
    shift = (v > 0xFFFF) << 4; v >>= shift; r |= shift
    shift = (v > 0xFF  ) << 3; v >>= shift; r |= shift
    shift = (v > 0xF   ) << 2; v >>= shift; r |= shift
    shift = (v > 0x3   ) << 1; v >>= shift; r |= shift

    return  r | (v >> 1)


@njit
def greedy_mesh_builder(v_mask, face, voxel, level, gvd, indexGreedy, stg):
    row_length = stg.c_size

    for row in range(row_length):
        h = 0
        # Row is empty from start
        if v_mask[row] >> h == 0:
            continue
        while h < row_length:
            # Row is empty
            if v_mask[row] >> h == 0:
                break
            # Find the first solid bit (non-zero bit)
            h += bit_length(v_mask[row] >> h & ~ (v_mask[row] >> h) + 1)

            # Find the height of contiguous ones starting at `h`
            trailing_ones = bit_length(~(v_mask[row] >> h) & (v_mask[row] >> h) + 1)

            # Create a mask for the height
            h_as_mask = (1 << trailing_ones) - 1 if trailing_ones > 0 else 0
            mask = h_as_mask << h

            # Grow vertically
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
                    v0 = greedy_pack_data(h                , level + 1, row    , voxel, face)
                    v1 = greedy_pack_data(h + trailing_ones, level + 1, row    , voxel, face)
                    v2 = greedy_pack_data(h + trailing_ones, level + 1, row + w, voxel, face)
                    v3 = greedy_pack_data(h                , level + 1, row + w, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v3, v2, v0, v2, v1)

                case 1:  # Bottom
                    v0 = greedy_pack_data(h, level, row, voxel, face)
                    v1 = greedy_pack_data(h + trailing_ones, level, row, voxel, face)
                    v2 = greedy_pack_data(h + trailing_ones, level, row + w, voxel, face)
                    v3 = greedy_pack_data(h, level, row + w, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v2, v3, v0, v1, v2)

                case 2:  # Right
                    v0 = greedy_pack_data(level + 1, row, h, voxel, face)
                    v1 = greedy_pack_data(level + 1, row + w, h, voxel, face)
                    v2 = greedy_pack_data(level + 1, row + w, h + trailing_ones, voxel, face)
                    v3 = greedy_pack_data(level + 1, row, h + trailing_ones, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v1, v2, v0, v2, v3)

                case 3:  # Left
                    v0 = greedy_pack_data(level, row, h, voxel, face)
                    v1 = greedy_pack_data(level, row + w, h, voxel, face)
                    v2 = greedy_pack_data(level, row + w, h + trailing_ones, voxel, face)
                    v3 = greedy_pack_data(level, row, h + trailing_ones, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v2, v1, v0, v3, v2)

                case 4:  # Back
                    v0 = greedy_pack_data(h, row, level, voxel, face)
                    v1 = greedy_pack_data(h, row + w, level, voxel, face)
                    v2 = greedy_pack_data(h + trailing_ones, row + w, level, voxel, face)
                    v3 = greedy_pack_data(h + trailing_ones, row, level, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v1, v2, v0, v2, v3)

                case 5:  # Forward
                    v0 = greedy_pack_data(h, row, level + 1, voxel, face)
                    v1 = greedy_pack_data(h, row + w, level + 1, voxel, face)
                    v2 = greedy_pack_data(h + trailing_ones, row + w, level + 1, voxel, face)
                    v3 = greedy_pack_data(h + trailing_ones, row, level + 1, voxel, face)
                    indexGreedy = add_data(gvd, indexGreedy, v0, v2, v1, v0, v3, v2)

            h += trailing_ones

    return indexGreedy


@njit
def build_chunk_mesh(chunk_voxels, format_size, chunk_pos, world_voxels, region_pos, stg):
    # Array containing additional properties [Voxel_ID, Face_ID] - type: uint8 to reduce memory size
    vertex_data = np.empty(stg.c_vol * 36 * format_size, dtype='uint32')
    # Array containing voxel type per face, after culling (used by greedy meshing algo)
    greedy_raw_data = np.zeros((stg.c_vol, 6), dtype = 'uint8')
    greedy_vertex_data = np.empty(stg.c_vol * 36 * format_size, dtype='uint32')
    # Init index to extract actual size of matrix
    index = 0
    indexGreedy = 0

    # Iterate over each dimension, compute the vertex of the only visible faces
    for x_ind in range(stg.c_size):
        x_plus = x_ind + 1  # x plus coordinate
        for y_ind in range(stg.c_size):
            y_plus = y_ind + 1   # y plus coordinate
            for z_ind in range(stg.c_size):
                z_plus = z_ind + 1   # z plus coordinate

                # Retrieve Voxel_ID for the given quad to plot and verify that it is not Null
                voxel_id = chunk_voxels[x_ind + stg.c_size * z_ind + stg.c_area * y_ind]
                if not voxel_id:
                    continue

                # Voxels world position
                cx, cy, cz = chunk_pos
                rx, ry, rz = region_pos
                wx = (x_ind + (rx * stg.r_size + cx - stg.off_x) * stg.c_size) * stg.v_x
                wy = (y_ind + (ry * stg.r_size + cy - stg.off_y) * stg.c_size) * stg.v_y
                wz = (z_ind + (rz * stg.r_size + cz - stg.off_z) * stg.c_size) * stg.v_z

                # top face
                if is_void((x_ind, y_ind + 1, z_ind), (wx, wy + stg.v_y, wz), world_voxels, stg):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind + 1, z_ind), (wx, wy + stg.v_y, wz), world_voxels, plane='Y', stg=stg)
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
                        greedy_raw_data[x_ind + stg.c_size * z_ind + stg.c_area * y_ind, 0] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 0)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 0)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 0)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 0)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

                # bottom face
                if is_void((x_ind, y_ind - 1, z_ind), (wx, wy - stg.v_y, wz), world_voxels, stg=stg):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind - 1, z_ind), (wx, wy - stg.v_y, wz), world_voxels, plane='Y', stg=stg)
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
                        greedy_raw_data[x_ind + stg.c_size * z_ind + stg.c_area * y_ind, 1] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 1)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 1)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 1)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 1)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

                # right face
                if is_void((x_ind + 1, y_ind, z_ind), (wx + stg.v_x, wy, wz), world_voxels, stg=stg):
                    # Get ao values
                    ao = get_ao((x_ind + 1, y_ind, z_ind), (wx + stg.v_x, wy, wz), world_voxels, plane='X', stg=stg)
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
                        greedy_raw_data[z_ind + stg.c_size * y_ind + stg.c_area * x_ind, 2] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 2)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 2)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 2)
                        v3 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 2)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

                # left face
                if is_void((x_ind - 1, y_ind, z_ind), (wx - stg.v_x, wy, wz), world_voxels, stg=stg):
                    # Get ao values
                    ao = get_ao((x_ind - 1, y_ind, z_ind), (wx - stg.v_x, wy, wz), world_voxels, plane='X', stg=stg)
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
                        greedy_raw_data[z_ind + stg.c_size * y_ind + stg.c_area * x_ind, 3] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_ind, z_ind, voxel_id, 3)
                        v1 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 3)
                        v2 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 3)
                        v3 = greedy_pack_data(x_ind, y_ind, z_plus, voxel_id, 3)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

                # back face
                if is_void((x_ind, y_ind, z_ind - 1), (wx, wy, wz - stg.v_z), world_voxels, stg=stg):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind - 1), (wx, wy, wz - stg.v_z), world_voxels, plane='Z', stg=stg)
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
                        greedy_raw_data[x_ind + stg.c_size * y_ind + stg.c_area * z_ind, 4] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 4)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 4)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 4)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 4)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

                # front face
                if is_void((x_ind, y_ind, z_ind + 1), (wx, wy, wz + stg.v_z), world_voxels, stg=stg):
                    # Get ao values
                    ao = get_ao((x_ind, y_ind, z_ind + 1), (wx, wy, wz + stg.v_z), world_voxels, plane='Z', stg=stg)
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
                        greedy_raw_data[x_ind + stg.c_size * y_ind + stg.c_area * z_ind, 5] = voxel_id
                    else:
                        # voxel is meshed as is, no need for flip id check
                        v0 = greedy_pack_data(x_ind, y_plus, z_ind, voxel_id, 5)
                        v1 = greedy_pack_data(x_plus, y_plus, z_ind, voxel_id, 5)
                        v2 = greedy_pack_data(x_plus, y_plus, z_plus, voxel_id, 5)
                        v3 = greedy_pack_data(x_ind, y_plus, z_plus, voxel_id, 5)
                        indexGreedy = add_data(greedy_vertex_data, indexGreedy, v0, v3, v2, v0, v2, v1)

    # Build fast greedy mesh
    new_mask = np.zeros(stg.c_size, dtype = "uint64")
    for v_type in range(1, 2): # Iterate over each meshable voxel type
        for face in range(6):
            for cut in range(stg.c_size):
                raw_mask = greedy_raw_data[cut * stg.c_area : (cut + 1) * stg.c_area, face] == v_type
                if raw_mask.any():
                    for it_m in range(stg.c_size):
                        new_mask[it_m] = np.sum(powers * raw_mask[it_m * stg.c_size : (it_m + 1) * stg.c_size])
                    indexGreedy = greedy_mesh_builder(new_mask, face, v_type, cut, greedy_vertex_data, indexGreedy, stg)

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