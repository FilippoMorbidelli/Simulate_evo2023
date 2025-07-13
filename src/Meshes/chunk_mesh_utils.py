# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from numba import njit, uint8, uint32, uint64, int32

import numpy as np
from typing import List, Tuple, Optional
from enum import Enum, IntEnum

# Utils for mesh gen----------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)

# - Constants -
CHUNK_SIZE  : uint64 = 32
CHUNK_SIZE2 : uint64 = CHUNK_SIZE * CHUNK_SIZE
CHUNK_SIZE3 : uint64 = CHUNK_SIZE * CHUNK_SIZE * CHUNK_SIZE
PAD_SIZE    : uint64 = CHUNK_SIZE + 2
PAD_SIZE2   : uint64 = PAD_SIZE * PAD_SIZE
REG_SIZE    : uint64 = 4
REG_SIZE2   : uint64 = REG_SIZE * REG_SIZE

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
], dtype = int32)

# - Classes -
class BlockType(IntEnum):
    Air = 0
    Grass = 1
    Dirt = 2

class FaceDir(Enum):
    Down = 0
    Up = 1
    Left = 2
    Right = 3
    Forward = 4
    Back = 5

# - Functions -
#@njit
def add_voxel_to_axis_cols(b: uint8, x: int, y: int, z: int, axis_cols: np.ndarray):
    if b != BlockType.Air:
        axis_cols[0, z, x] |= 1 << y
        axis_cols[1, y, z] |= 1 << x
        axis_cols[2, y, x] |= 1 << z

#@njit
def bound_to_face(bound_array: np.ndarray) -> Enum:
    match bound_array:
        case (1, 0, 0): return FaceDir.Left
        case (2, 0, 0): return FaceDir.Right
        case (0, 1, 0): return FaceDir.Down
        case (0, 2, 0): return FaceDir.Up
        case (0, 0, 1): return FaceDir.Back
        case (0, 0, 2): return FaceDir.Forward

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
def get_padded_chunk_optimized(voxels, region_pos, chunk_pos):
    # Init padded chunk
    padded = np.zeros((34, 34, 34), dtype=uint8)

    main_chunk = chunk_pos[0] + chunk_pos[1] * REG_SIZE2 + chunk_pos[2] * REG_SIZE
    #main_reg   =

    # Get the center chunk voxels
    for z in range(CHUNK_SIZE):
        z_id = z * CHUNK_SIZE
        pz_id = (z + 1) * PAD_SIZE

        for y in range(CHUNK_SIZE):
            chunk_id = 0 + z_id + y * CHUNK_SIZE2
            padded_id = 1 + pz_id + (y + 1) * PAD_SIZE2

            padded[padded_id : padded_id + CHUNK_SIZE] = voxels[main_chunk][chunk_id : chunk_id + CHUNK_SIZE]


#-----------------------------------------------------------------------------------------------------------
    def world_to_sample(self, axis: int, x: int, y: int, lod) -> np.ndarray:
        if self == FaceDir.Up:
            return np.array([x, axis + 1, y], dtype=int32)
        elif self == FaceDir.Down:
            return np.array([x, axis, y], dtype=int32)
        elif self == FaceDir.Left:
            return np.array([axis, y, x], dtype=int32)
        elif self == FaceDir.Right:
            return np.array([axis + 1, y, x], dtype=int32)
        elif self == FaceDir.Forward:
            return np.array([x, y, axis], dtype=int32)
        else:  # Back
            return np.array([x, y, axis + 1], dtype=int32)

    def reverse_order(self) -> bool:
        return self in [FaceDir.Up, FaceDir.Right, FaceDir.Forward]

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

    def append_vertices(self, vertices: List[uint32], face_dir: FaceDir, axis: int, lod: Lod, ao: int, block_type: int):
        axis = axis
        jump = lod.jump_index()

        # pack ambient occlusion
        v1ao = ((ao >> 0) & 1) + ((ao >> 1) & 1) + ((ao >> 3) & 1)
        v2ao = ((ao >> 3) & 1) + ((ao >> 6) & 1) + ((ao >> 7) & 1)
        v3ao = ((ao >> 5) & 1) + ((ao >> 8) & 1) + ((ao >> 7) & 1)
        v4ao = ((ao >> 1) & 1) + ((ao >> 2) & 1) + ((ao >> 5) & 1)

        v1 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x, self.y, lod) * jump,
            v1ao,
            face_dir.normal_index(),
            block_type
        )
        v2 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x + self.w, self.y, lod) * jump,
            v2ao,
            face_dir.normal_index(),
            block_type
        )
        v3 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x + self.w, self.y + self.h, lod) * jump,
            v3ao,
            face_dir.normal_index(),
            block_type
        )
        v4 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x, self.y + self.h, lod) * jump,
            v4ao,
            face_dir.normal_index(),
            block_type
        )

        new_vertices = [v1, v2, v3, v4]

        if face_dir.reverse_order():
            new_vertices = [new_vertices[0]] + new_vertices[1:][::-1]

        if (v1ao > 0) ^ (v3ao > 0):
            new_vertices = new_vertices[1:] + [new_vertices[0]]

        vertices.extend(new_vertices)


