# Evolution simulation project - chunk mesh generation module
# Author: Filippo Morbidelli
# Created on: 16/07/2025
# Last update: 16/07/2025

# Import packages ------------------------------|
from src.Meshes.chunk_mesh_utils import *

from numpy.typing import NDArray
from numba.typed import Dict as nDict
from numba import types
from typing import List, Optional

# World generator ------------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)

@njit(fastmath=True, cache=True, nogil=True)
def build_chunk_mesh_greedy(chunk_voxels: np.ndarray,
                            neighbors: np.ndarray,
                            format_s: int32,
                            lod: int = 32) -> Optional[np.ndarray]:

    # If Chunk is empty exit
    assert len(chunk_voxels) == CHUNK_SIZE3 or len(chunk_voxels) == 1
    if not np.any(chunk_voxels):
        return np.empty(1, dtype='uint32')

    # Array containing mesh vertices already packed for GPU
    vertices = np.empty(CHUNK_SIZE3 * 18 * format_s, dtype='uint32')

    # solid binary for each x,y,z axis (3)
    axis_cols: NDArray[np.uint64] = np.zeros((3, PADDED_SIZE, PADDED_SIZE), dtype='uint64')

    # cull mask to perform greedy slicing
    col_face_masks: NDArray[np.uint64] = np.zeros((6, PADDED_SIZE, PADDED_SIZE), dtype='uint64')

    # Chunk voxels
    for y in range(CHUNK_SIZE):
        y_index = y * CHUNK_SIZE2

        for z in range(CHUNK_SIZE):
            z_index = z * CHUNK_SIZE

            for x in range(CHUNK_SIZE):
                i = y_index + z_index + x

                add_voxel_to_axis_cols(chunk_voxels[i], x + 1, y + 1, z + 1, axis_cols)

    # Neighbouring Chunks voxels
    # Along z axis
    for z in [0, PADDED_SIZE - 1]:
        neighbor_id = 5 if z else 4 # Back and Forward
        z_index = (0 if z else 31) * CHUNK_SIZE

        for y in range(CHUNK_SIZE):
            y_index = y * CHUNK_SIZE2

            for x in range(CHUNK_SIZE):
                i = y_index + z_index + x

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x + 1, y + 1, z, axis_cols)

    # Along y axis
    for y in [0, PADDED_SIZE - 1]:
        neighbor_id = 1 if y else 0 # Up and Down
        y_index = (0 if y else 31) * CHUNK_SIZE2

        for z in range(CHUNK_SIZE):
            z_index = z * CHUNK_SIZE

            for x in range(CHUNK_SIZE):
                i = y_index + z_index + x

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x + 1, y, z + 1, axis_cols)

    # Along x axis
    for x in [0, PADDED_SIZE - 1]:
        neighbor_id = 3 if x else 2 # Right and Left
        x_index = (0 if x else 31)

        for z in range(CHUNK_SIZE):
            z_index = z * CHUNK_SIZE

            for y in range(CHUNK_SIZE):
                y_index = y * CHUNK_SIZE2
                i = y_index + z_index + x_index

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x, y + 1, z + 1, axis_cols)

    # Face culling
    for axis in range(3):
        for z in range(PADDED_SIZE):
            for x in range(PADDED_SIZE):
                col = axis_cols[axis, z, x]
                col_face_masks[2 * axis + 0, z, x] = col & ~(col << 1)
                col_face_masks[2 * axis + 1, z, x] = col & ~(col >> 1)

    # Greedy meshing planes for every axis (6)
    # cannot use List[Dict[int, Dict[int, np.ndarray]]] due to Numba so trying with NumbaDict but may be a bottleneck!!
    data = [nDict.empty(key_type=types.uint32, value_type=types.uint32[:]) for _ in range(6)]

    # Compute Ambient Occlusion
    for axis in range(6):
        for z in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                # skip padded by adding 1(for x padding) and (z+1) for (z padding)
                col = col_face_masks[axis, z + 1, x + 1]
                # removes the right most and left most padding values, because they are invalid
                col >>= 1
                col &= ~(uint64(1) << CHUNK_SIZE)

                while col != 0:
                    # py implementation of trailing zeros (uint32)
                    y = bit_length(col & ~col + uint64(1))
                    col &= col - uint64(1) # clear least significant set bit

                    # get the voxel position based on axis
                    match axis:
                        case FaceDir.Up | FaceDir.Down:
                            voxel_pos: NDArray[int32] = np.array([x, y, z], dtype='int32')
                        case FaceDir.Left | FaceDir.Right:
                            voxel_pos: NDArray[int32] = np.array([y, z, x], dtype='int32')
                        case FaceDir.Forward | FaceDir.Back | _:
                            voxel_pos: NDArray[int32] = np.array([x, z, y], dtype='int32')

                    # compute ambient occlusion
                    ao_index = 0
                    for ao_i, ao_offset in enumerate(ADJACENT_AO_DIRS):
                        # ambient occlusion is sampled based on axis(ascent or descent)
                        match axis:
                            case FaceDir.Down:
                                ao_sample_offset = np.array([ao_offset[0], -1, ao_offset[1]], dtype='int32')
                            case FaceDir.Up:
                                ao_sample_offset = np.array([ao_offset[0],  1, ao_offset[1]], dtype='int32')
                            case FaceDir.Left:
                                ao_sample_offset = np.array([-1, ao_offset[1], ao_offset[0]], dtype='int32')
                            case FaceDir.Right:
                                ao_sample_offset = np.array([ 1, ao_offset[1], ao_offset[0]], dtype='int32')
                            case FaceDir.Forward:
                                ao_sample_offset = np.array([ao_offset[0], ao_offset[1], -1], dtype='int32')
                            case FaceDir.Back | _:
                                ao_sample_offset = np.array([ao_offset[0], ao_offset[1],  1], dtype='int32')

                        ao_voxel_pos = voxel_pos + ao_sample_offset

                        # Find if neighbor voxel is solid or not to count for AO
                        is_valid_neighbor = np.sum((ao_voxel_pos < 0) | (ao_voxel_pos > 31))
                        if not is_valid_neighbor:
                            ao_block = chunk_voxels[ao_voxel_pos[2] * CHUNK_SIZE + ao_voxel_pos[1] * CHUNK_SIZE2 + ao_voxel_pos[0]]
                        elif is_valid_neighbor == 1:
                            face = bound_to_face(np.concatenate((ao_voxel_pos < 0, ao_voxel_pos > 31)))
                            ao_block = neighbors[face, (ao_voxel_pos[2] & 0b11111) * CHUNK_SIZE + (ao_voxel_pos[1] & 0b11111) * CHUNK_SIZE2 + (ao_voxel_pos[0] & 0b11111)]
                        else :
                            ao_block = 0

                        if ao_block != BlockType.Air:
                            ao_index |= 1 << ao_i

                    current_voxel = np.uint32(chunk_voxels[voxel_pos[2] * CHUNK_SIZE + voxel_pos[1] * CHUNK_SIZE2 + voxel_pos[0]])
                    block_hash = ao_index | (current_voxel << 9)
                    composite_block_hash = block_hash | (y << 17)

                    if composite_block_hash not in data[axis]:
                        data[axis][composite_block_hash] = np.zeros(32, dtype='uint32')

                    data[axis][composite_block_hash][x] |= np.uint32(1) << np.uint32(z)

    # Sample planes for greedy meshing
    index = 0
    for axis, block_ao_data in enumerate(data):
        for comp_block_hash, plane in block_ao_data.items():
            ao         = comp_block_hash & 0b111111111
            block_type = (comp_block_hash >> 9) & 0b11111111
            axis_pos   = comp_block_hash >> 17

            quads_from_axis = greedy_mesh_binary_plane(plane, lod)

            for q in quads_from_axis:
                index = append_vertices(vertices, index, q, axis, axis_pos, ao, block_type, lod)

    return vertices[:index] if index else vertices[:1]

@njit(fastmath=True, cache=True, nogil=True)
def greedy_mesh_binary_plane(voxel_mask,
                             lod: int) -> List[int32]:
    row_length = CHUNK_SIZE
    greedy_quads = []

    for row in range(row_length):
        h = 0
        # Row is empty from start
        if voxel_mask[row] >> h == 0:
            continue
        while h < row_length:
            # Row is empty
            if voxel_mask[row] >> h == 0:
                break
            # Find the first solid bit (non-zero bit)
            h += bit_length(voxel_mask[row] >> h & ~ (voxel_mask[row] >> h) + 1)

            # Find the height of contiguous ones starting at `h`
            trailing_ones = bit_length(~(voxel_mask[row] >> h) & (voxel_mask[row] >> h) + 1)

            # Create a mask for the height
            h_as_mask = (1 << trailing_ones) - 1 if trailing_ones < 32 else 0xFFFFFFFF
            mask = h_as_mask << h

            # Grow vertically
            w = 1
            while row + w < row_length:
                # Fetch bits spanning height in the next row
                next_row_h = (voxel_mask[row + w] >> h) & h_as_mask
                if next_row_h != h_as_mask:
                    break  # Can no longer expand horizontally

                # Remove the bits we expanded into
                voxel_mask[row + w] &= ~mask

                w += 1

            # Append Quads
            greedy_quads.append([row, h, w, trailing_ones]) #[h, row, trailing_ones, w])

            h += trailing_ones

    return greedy_quads

@njit(fastmath=True, cache=True, nogil=True)
def append_vertices(vertices: np.ndarray,
                    index: int,
                    quad: List[int32],
                    face: int,
                    section: int,
                    ao: int,
                    block_type: int,
                    lod: int) -> int:

    # retrieve Lod level
    #jump = lod.jump_index()
    h, row, tr_ones, w = quad

    # pack ambient occlusion
    v1ao = ((ao >> 0) & 1) + ((ao >> 1) & 1) + ((ao >> 3) & 1)
    v2ao = ((ao >> 3) & 1) + ((ao >> 6) & 1) + ((ao >> 7) & 1)
    v3ao = ((ao >> 5) & 1) + ((ao >> 8) & 1) + ((ao >> 7) & 1)
    v4ao = ((ao >> 1) & 1) + ((ao >> 2) & 1) + ((ao >> 5) & 1)

    flip = (v1ao > 0) ^ (v3ao > 0)

    # compute each vertex
    if face == FaceDir.Up:
        v0 = pack_data(h          , section + 1, row    , block_type, face, v1ao, flip)
        v1 = pack_data(h + tr_ones, section + 1, row    , block_type, face, v2ao, flip)
        v2 = pack_data(h + tr_ones, section + 1, row + w, block_type, face, v3ao, flip)
        v3 = pack_data(h          , section + 1, row + w, block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v3, v2, v1, v0] if flip else [v0, v3, v2, v1] # only for ascending faces
        new_vertices = [v1, v0, v3, v1, v3, v2] if flip else [v0, v3, v2, v0, v2, v1]
    elif face == FaceDir.Down:
        v0 = pack_data(h          , section    , row    , block_type, face, v1ao, flip)
        v1 = pack_data(h + tr_ones, section    , row    , block_type, face, v2ao, flip)
        v2 = pack_data(h + tr_ones, section    , row + w, block_type, face, v3ao, flip)
        v3 = pack_data(h          , section    , row + w, block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v1, v2, v3, v0] if flip else [v0, v1, v2, v3]  # only anisotropy flip
        new_vertices = [v1, v3, v0, v1, v2, v3] if flip else [v0, v2, v3, v0, v1, v2]
    elif face == FaceDir.Left:
        v0 = pack_data(section    , row    , h          , block_type, face, v1ao, flip)
        v1 = pack_data(section    , row + w, h          , block_type, face, v2ao, flip)
        v2 = pack_data(section    , row + w, h + tr_ones, block_type, face, v3ao, flip)
        v3 = pack_data(section    , row    , h + tr_ones, block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v1, v2, v3, v0] if flip else [v0, v1, v2, v3]  # only anisotropy flip
        new_vertices = [v3, v1, v0, v3, v2, v1] if flip else [v0, v2, v1, v0, v3, v2]
    elif face == FaceDir.Right:
        v0 = pack_data(section + 1, row    , h          , block_type, face, v1ao, flip)
        v1 = pack_data(section + 1, row + w, h          , block_type, face, v2ao, flip)
        v2 = pack_data(section + 1, row + w, h + tr_ones, block_type, face, v3ao, flip)
        v3 = pack_data(section + 1, row    , h + tr_ones, block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v3, v2, v1, v0] if flip else [v0, v3, v2, v1] # only for ascending faces
        new_vertices = [v3, v0, v1, v3, v1, v2] if flip else [v0, v1, v2, v0, v2, v3]
    elif face == FaceDir.Forward:
        v0 = pack_data(h          , row    , section    , block_type, face, v1ao, flip)
        v1 = pack_data(h          , row + w, section    , block_type, face, v2ao, flip)
        v2 = pack_data(h + tr_ones, row + w, section    , block_type, face, v3ao, flip)
        v3 = pack_data(h + tr_ones, row    , section    , block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v3, v2, v1, v0] if flip else [v0, v3, v2, v1] # only for ascending faces
        new_vertices = [v3, v1, v0, v3, v2, v1] if flip else [v0, v2, v1, v0, v3, v2]
    else:  # Back
        v0 = pack_data(h          , row    , section + 1, block_type, face, v1ao, flip)
        v1 = pack_data(h          , row + w, section + 1, block_type, face, v2ao, flip)
        v2 = pack_data(h + tr_ones, row + w, section + 1, block_type, face, v3ao, flip)
        v3 = pack_data(h + tr_ones, row    , section + 1, block_type, face, v4ao, flip)
        #v0, v1, v2, v3 = [v1, v2, v3, v0] if flip else [v0, v1, v2, v3]  # only anisotropy flip
        new_vertices = [v3, v0, v1, v3, v1, v2] if flip else [v0, v1, v2, v0, v2, v3]

    # Compute correct vertices and adds them to array
    index = add_data(vertices, index, new_vertices)

    return index
