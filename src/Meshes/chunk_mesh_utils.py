# Evolution simulation project - chunk mesh generation utilities module
# Author: Filippo Morbidelli
# Created on: 16/07/2025
# Last update: 16/07/2025

# Import packages ------------------------------|
from numba import njit, uint8, uint64
from enum import IntEnum

import numpy as np

# Utils for mesh gen----------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher

# - Constants -
CHUNK_SIZE   : uint64 = 32
CHUNK_SIZE2  : uint64 = CHUNK_SIZE * CHUNK_SIZE
CHUNK_SIZE3  : uint64 = CHUNK_SIZE * CHUNK_SIZE * CHUNK_SIZE
PADDED_SIZE  : uint64 = CHUNK_SIZE + 2
PADDED_SIZE2 : uint64 = PADDED_SIZE * PADDED_SIZE
REG_SIZE     : uint64 = 4
REG_AREA     : uint64 = REG_SIZE * REG_SIZE

b_bit, c_bit, d_bit, e_bit, f_bit, g_bit = 6, 6, 8, 3, 2, 1 # Data Packing
#INNER_DICT_TYPE = types.DictType(types.uint32, types.uint32[:]) # Numba type

ADJACENT_AO_DIRS = np.array([
    [-1, -1],
    [-1,  0],
    [-1,  1],
    [ 0, -1],
    [ 0,  0],
    [ 0,  1],
    [ 1, -1],
    [ 1,  0],
    [ 1,  1]
], dtype = 'int32')

ADJACENT_CHUNK_DIRS = np.array([
    [0, -1, 0],
    [0,  1, 0],
    [-1, 0, 0],
    [ 1, 0, 0],
    [0, 0, -1],
    [0, 0,  1]
], dtype = 'int32')

# - Classes -
class BlockType(IntEnum):
    Air = 0
    Grass = 1
    Dirt = 2

class FaceDir(IntEnum):
    Down = 0
    Up = 1
    Left = 2
    Right = 3
    Forward = 4
    Back = 5

# - Meshing Functions -
@njit(fastmath=True, cache=True, nogil=True)
def add_voxel_to_axis_cols(b: uint8, x: int, y: int, z: int, axis_cols: np.ndarray):
    if b != BlockType.Air:
        axis_cols[0, z, x] |= 1 << y
        axis_cols[1, y, z] |= 1 << x
        axis_cols[2, y, x] |= 1 << z

@njit(fastmath=True, cache=True, nogil=True)
def bound_to_face(bound_array: np.ndarray) -> int:
    for face in range(6):
        if bound_array[face]:
            match face:
                case 0: return 2 # FaceDir.Left
                case 1: return 0 # FaceDir.Down
                case 2: return 4 # FaceDir.Forward
                case 3: return 3 # FaceDir.Right
                case 4: return 1 # FaceDir.Up
                case 5: return 5 # FaceDir.Back
    return 0 # FaceDir.Down

@njit(fastmath=True, cache=True, nogil=True)
def bit_length(v):
    # Custom method to compute log2(v)
    # Used to find bit length of v in numba since bit_length method is not implemented
    r = (v > 0xFFFFFFFF) << 5; v >>= r
    shift = (v > 0xFFFF) << 4; v >>= shift; r |= shift
    shift = (v > 0xFF  ) << 3; v >>= shift; r |= shift
    shift = (v > 0xF   ) << 2; v >>= shift; r |= shift
    shift = (v > 0x3   ) << 1; v >>= shift; r |= shift

    return  r | (v >> 1)

@njit(fastmath=True, cache=True, nogil=True)
def pack_data(x, y, z, voxel_id, face_id, ao_id, flip_id):
    # x: 6bit, y: 6bit, z: 6bit, voxel_id: 8bit, face_id: 3bit, ao_id: 2bit, flip_id: 1bit
    a, b, c, d, e, f, g = np.uint32(x), np.uint32(y), np.uint32(z), voxel_id, face_id, ao_id, flip_id

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

@njit(fastmath=True, cache=True, nogil=True)
def add_data(vertex_data, index, vertices):
    # Iterate over each vertex (6 total for a quad, 2 triangles)
    for vertex in vertices:
        vertex_data[index] = vertex  # Save vertex data to vert buffer array
        index += 1
    return index

# - Other utils functions -
#@njit(fastmath=True, cache=True, nogil=True)
def get_neighbors(voxels, reg_pos, chunk_pos, info):
    neighbors = np.zeros([6, info.c_vol], dtype="uint8")
    reg_list, chunk_list = find_neighbors_w_reg(reg_pos, chunk_pos, info)
    for index in range(6):
        if int(reg_list[index]) in voxels and reg_list[index] > 0 and chunk_list[index] > 0:
            neighbors[index] = voxels[int(reg_list[index])][chunk_list[index]]

    return neighbors


#@njit(fastmath=True, cache=True, nogil=True)
def find_neighbors_w_reg(reg_pos, chunk_pos, info):
    ChunkIDList = []
    RegionIDList = []
    RegionID = reg_pos[0] + info.width_rn * reg_pos[2] + info.width_rn * info.depth_rn * reg_pos[1]
    # Iterate over each of the 6 sides
    for _, cdir in enumerate(ADJACENT_CHUNK_DIRS):
        # compute adjacent chunk
        new_chunk = chunk_pos + np.array(cdir)
        if np.all(new_chunk >= 0) and np.all(new_chunk < 4):
            # Same region, different chunk
            new_chunk_index = new_chunk[0] + REG_SIZE * new_chunk[2] + REG_AREA * new_chunk[1]
            ChunkIDList.append(new_chunk_index)
            RegionIDList.append(RegionID)
        elif np.sum((new_chunk < 0) | (new_chunk > 4)) == 1:
            # different region, different chunk
            new_chunk_index = (new_chunk[0] & 0b11) + REG_SIZE * (new_chunk[2] & 0b11) + REG_AREA * (new_chunk[1] & 0b11)
            new_region = reg_pos + bound_to_region(np.concatenate((new_chunk < 0, new_chunk > 4)))
            new_region_index = new_region[0] + info.width_rn * new_region[2] + info.width_rn * info.depth_rn * new_region[1]
            ChunkIDList.append(new_chunk_index if new_region_index > 0 else 0)
            RegionIDList.append(new_region_index if new_region_index > 0 else 0)
        else:
            # Should not happen
            ChunkIDList.append(0)
            RegionIDList.append(0)

    return RegionIDList, ChunkIDList

def bound_to_region(bound_array: np.ndarray):
    for face in range(6):
        if bound_array[face]:
            match face:
                case 0: return [-1, 0, 0]
                case 1: return [0, -1, 0]
                case 2: return [0, 0, -1]
                case 3: return [1, 0, 0]
                case 4: return [0, 1, 0]
                case 5: return [0, 0, 1]
    return [0, 0, 0]

@njit(fastmath=True, cache=True, nogil=True)
def get_padded_chunk_optimized(voxels, region_pos, chunk_pos):
    pass

#@njit(fastmath=True, cache=True)
def get_chunk_index(info, world_voxel_pos):
    # Unpack voxel position in world coordinates
    wx, wy, wz = world_voxel_pos
    wx = int(wx + info.offset[0] * info.c_size)
    wy = int(wy + info.offset[1] * info.c_size)
    wz = int(wz + info.offset[2] * info.c_size)

    # Compute region index
    rx = wx >> info.rcSzBin
    ry = wy >> info.rcSzBin
    rz = wz >> info.rcSzBin

    # Compute chunk index
    cx = (wx & info.rcMask) >> info.cSizeBin
    cy = (wy & info.rcMask) >> info.cSizeBin
    cz = (wz & info.rcMask) >> info.cSizeBin

    # Out of region check
    if rx // info.width_rn or ry // info.height_rn or rz // info.depth_rn:
        return -1, -1

    r_index = rx + info.width_rn * rz + info.depth_rn * info.width_rn * ry
    index = cx + info.r_size * cz + info.r_area * cy
    return int(r_index), int(index)
