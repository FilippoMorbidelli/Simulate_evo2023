# Evolution simulation project - chunk mesh generation utilities module
# Author: Filippo Morbidelli
# Created on: 16/07/2025
# Last update: 16/07/2025

# Import packages ------------------------------|
from numba import njit, uint8, uint64, int32, uint32, types
from enum import Enum, IntEnum

import numpy as np

# Utils for mesh gen----------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)

# - Constants -
CHUNK_SIZE  : uint64 = 32
CHUNK_SIZE2 : uint64 = CHUNK_SIZE * CHUNK_SIZE
CHUNK_SIZE3 : uint64 = CHUNK_SIZE * CHUNK_SIZE * CHUNK_SIZE
PADDED_SIZE    : uint64 = CHUNK_SIZE + 2
PADDED_SIZE2   : uint64 = PADDED_SIZE * PADDED_SIZE
REG_SIZE    : uint64 = 4
REG_SIZE2   : uint64 = REG_SIZE * REG_SIZE

b_bit, c_bit, d_bit, e_bit, f_bit, g_bit = 6, 6, 8, 3, 2, 1 # Data Packing
INNER_DICT_TYPE = types.DictType(types.uint32, types.uint32[:]) # Numba type

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

# - Functions -
@njit(fastmath=True, cache=True, nogil=True)
def add_voxel_to_axis_cols(b: uint8, x: int, y: int, z: int, axis_cols: np.ndarray):
    if b != BlockType.Air:
        axis_cols[0, z, x] |= 1 << y
        axis_cols[1, y, z] |= 1 << x
        axis_cols[2, y, x] |= 1 << z

@njit(fastmath=True, cache=True, nogil=True)
def bound_to_face(bound_array: np.ndarray) -> Enum:
    for face in range(6):
        if bound_array[face]:
            match face:
                case 0: return FaceDir.Left
                case 1: return FaceDir.Down
                case 2: return FaceDir.Forward
                case 3: return FaceDir.Right
                case 4: return FaceDir.Up
                case 5: return FaceDir.Back
    return FaceDir.Down

@njit(fastmath=True, cache=True, nogil=True)
def face_to_vec3(face, section: int32, x: int32, y: int32) -> int32:
    if face == FaceDir.Up:
        return x, section + 1, y
    elif face == FaceDir.Down:
        return x, section, y
    elif face == FaceDir.Left:
        return section, y, x
    elif face == FaceDir.Right:
        return section + 1, y, x
    elif face == FaceDir.Forward:
        return x, y, section
    else:  # Back
        return x, y, section + 1

@njit(fastmath=True, cache=True, nogil=True)
def bit_length(v):
    # Custom method to compute log2(v)
    # Used to find bit length of v in numba since bit_length method is not implemented
    r =     np.uint32((v > 0xFFFFFFFF) << 5); v >>= r
    shift = (v > 0xFFFF) << 4; v >>= shift; r |= shift
    shift = (v > 0xFF  ) << 3; v >>= shift; r |= shift
    shift = (v > 0xF   ) << 2; v >>= shift; r |= shift
    shift = (v > 0x3   ) << 1; v >>= shift; r |= shift

    return  r | (v >> 1)

@njit(fastmath=True, cache=True, nogil=True)
def pack_data(x, y, z, voxel_id, face_id, ao_id, flip_id):
    # x: 6bit, y: 6bit, z: 6bit, voxel_id: 8bit, face_id: 3bit, ao_id: 2bit, flip_id: 1bit
    a, b, c, d, e, f, g = x, y, z, voxel_id, face_id, ao_id, flip_id

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

@njit(fastmath=True, cache=True, nogil=True)
def get_padded_chunk_optimized(voxels, region_pos, chunk_pos):
    # Init padded chunk
    padded = np.zeros((34, 34, 34), dtype=uint8)

    main_chunk = chunk_pos[0] + chunk_pos[1] * REG_SIZE2 + chunk_pos[2] * REG_SIZE
    #main_reg   =

    # Get the center chunk voxels
    for z in range(CHUNK_SIZE):
        z_id = z * CHUNK_SIZE
        pz_id = (z + 1) * PADDED_SIZE

        for y in range(CHUNK_SIZE):
            chunk_id = 0 + z_id + y * CHUNK_SIZE2
            padded_id = 1 + pz_id + (y + 1) * PADDED_SIZE2

            padded[padded_id : padded_id + CHUNK_SIZE] = voxels[main_chunk][chunk_id : chunk_id + CHUNK_SIZE]


#-----------------------------------------------------------------------------------------------------------

class Lod(Enum):
    L32 = 32
    L16 = 16
    L8 = 8
    L4 = 4
    L2 = 2

    def size(self) -> int:
        return self.value

    def jump_index(self) -> int:
        return 32 // self.value
