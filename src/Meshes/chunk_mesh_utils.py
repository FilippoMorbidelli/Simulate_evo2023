# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from numba import njit

import numpy as np
from typing import List, Tuple, Dict, Optional
from enum import Enum, IntEnum
from dataclasses import dataclass

# World generator ------------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)

# - Constants ----------------------------------|
CHUNK_SIZE     = 32
CHUNK_SIZE_I32 = 32
CHUNK_SIZE_P   = CHUNK_SIZE + 2
CHUNK_SIZE_P2  = CHUNK_SIZE_P * CHUNK_SIZE_P
CHUNK_SIZE_P3  = CHUNK_SIZE_P * CHUNK_SIZE_P * CHUNK_SIZE_P
CHUNK_SIZE2    = CHUNK_SIZE * CHUNK_SIZE
CHUNK_SIZE2_I32 = CHUNK_SIZE2
CHUNK_SIZE3    = CHUNK_SIZE * CHUNK_SIZE * CHUNK_SIZE

ADJACENT_CHUNK_DIRECTIONS = np.array([
    [ 0,  0,  0],
    [ 0, -1, -1],
    [-1,  0, -1],
    [-1,  0,  1],
    [-1, -1,  0],
    [-1, -1, -1],
    [-1,  1, -1],
    [-1, -1,  1],
    [-1,  1,  1],
    [ 1,  0, -1],
    [ 1, -1, -1],
    [ 0,  1, -1],
    [ 1,  1,  1],
    [ 1, -1,  1],
    [ 1,  1, -1],
    [ 1,  1,  0],
    [ 0,  1,  1],
    [ 1, -1,  0],
    [ 0, -1,  1],
    [ 1,  0,  1],
    [-1,  1,  0],
    [-1,  0,  0],
    [ 1,  0,  0],
    [ 0, -1,  0],
    [ 0,  1,  0],
    [ 0,  0, -1],
    [ 0,  0,  1]
], dtype=np.int32)

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
], dtype=np.int32)

# - Classes -
class BlockType(IntEnum):
    Air = 0
    Grass = 1
    Dirt = 2

MESHABLE_BLOCK_TYPES = [BlockType.Grass, BlockType.Dirt]

@dataclass
class BlockData: #
    block_type: BlockType = BlockType.Air

    def is_solid(self) -> bool:
        return self.block_type != BlockType.Air

    def is_air(self) -> bool:
        return not self.is_solid()


class FaceDir(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3
    Forward = 4
    Back = 5

    def normal_index(self) -> int:
        return self.value

    def air_sample_dir(self) -> np.ndarray:
        if self == FaceDir.Up:
            return np.array([0, 1, 0], dtype=np.int32)
        elif self == FaceDir.Down:
            return np.array([0, -1, 0], dtype=np.int32)
        elif self == FaceDir.Left:
            return np.array([-1, 0, 0], dtype=np.int32)
        elif self == FaceDir.Right:
            return np.array([1, 0, 0], dtype=np.int32)
        elif self == FaceDir.Forward:
            return np.array([0, 0, -1], dtype=np.int32)
        else:  # Back
            return np.array([0, 0, 1], dtype=np.int32)

    def world_to_sample(self, axis: int, x: int, y: int, lod) -> np.ndarray:
        if self == FaceDir.Up:
            return np.array([x, axis + 1, y], dtype=np.int32)
        elif self == FaceDir.Down:
            return np.array([x, axis, y], dtype=np.int32)
        elif self == FaceDir.Left:
            return np.array([axis, y, x], dtype=np.int32)
        elif self == FaceDir.Right:
            return np.array([axis + 1, y, x], dtype=np.int32)
        elif self == FaceDir.Forward:
            return np.array([x, y, axis], dtype=np.int32)
        else:  # Back
            return np.array([x, y, axis + 1], dtype=np.int32)

    def reverse_order(self) -> bool:
        return self in [FaceDir.Up, FaceDir.Right, FaceDir.Forward]

    def negate_axis(self) -> int:
        if self == FaceDir.Up:
            return -1
        elif self == FaceDir.Right:
            return -1
        elif self == FaceDir.Back:
            return 1
        else:
            return 0


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


class ChunkMesh:
    def __init__(self):
        self.indices = []
        self.vertices = []


class Direction(Enum):
    Left = 0
    Right = 1
    Down = 2
    Up = 3
    Back = 4
    Forward = 5

    def get_normal(self) -> int:
        return self.value

    def get_opposite(self) -> 'Direction':
        if self == Direction.Left:
            return Direction.Right
        elif self == Direction.Right:
            return Direction.Left
        elif self == Direction.Down:
            return Direction.Up
        elif self == Direction.Up:
            return Direction.Down
        elif self == Direction.Back:
            return Direction.Forward
        else:  # Forward
            return Direction.Back


class Quad:
    def __init__(self, color, direction: Direction, corners):
        self.color = color
        self.direction = direction
        self.corners = corners

    @classmethod
    def from_direction(cls, direction: Direction, pos: np.ndarray, color) -> 'Quad':
        x, y, z = pos
        if direction == Direction.Left:
            corners = [
                [x, y, z],
                [x, y, z + 1],
                [x, y + 1, z + 1],
                [x, y + 1, z]
            ]
        elif direction == Direction.Right:
            corners = [
                [x, y + 1, z],
                [x, y + 1, z + 1],
                [x, y, z + 1],
                [x, y, z]
            ]
        elif direction == Direction.Down:
            corners = [
                [x, y, z],
                [x + 1, y, z],
                [x + 1, y, z + 1],
                [x, y, z + 1]
            ]
        elif direction == Direction.Up:
            corners = [
                [x, y, z + 1],
                [x + 1, y, z + 1],
                [x + 1, y, z],
                [x, y, z]
            ]
        elif direction == Direction.Back:
            corners = [
                [x, y, z],
                [x, y + 1, z],
                [x + 1, y + 1, z],
                [x + 1, y, z]
            ]
        else:  # Forward
            corners = [
                [x + 1, y, z],
                [x + 1, y + 1, z],
                [x, y + 1, z],
                [x, y, z]
            ]

        return cls(color, direction, corners)

class ChunkData: # Class used to temporarily contain voxel
    def __init__(self, voxels=None):
        self.voxels = voxels if voxels is not None else [BlockData()] * CHUNK_SIZE3

    def get_block(self, index: int) -> BlockData:
        if len(self.voxels) == 1:
            return self.voxels[0]
        return self.voxels[index]

    def get_block_if_filled(self) -> Optional[BlockData]:
        if len(self.voxels) == 1:
            return self.voxels[0]
        return None


class ChunksRefs:
    def __init__(self, chunks: List[ChunkData]):
        self.chunks = chunks

    @classmethod
    def try_new(cls, world_data: Dict[Tuple[int, int, int], ChunkData],
                middle_chunk: np.ndarray) -> Optional['ChunksRefs']:
        chunks = []
        for i in range(3 * 3 * 3):
            offset = index_to_ivec3_bounds(i, 3) + np.array([-1, -1, -1], dtype=np.int32)
            chunk_pos = tuple((middle_chunk + offset).tolist())
            if chunk_pos in world_data:
                chunks.append(world_data[chunk_pos])
            else:
                return None
        return cls(chunks)

    def is_all_voxels_same(self) -> bool:
        first_block = self.chunks[0].get_block_if_filled()
        if first_block is None:
            return False

        for chunk in self.chunks[1:]:
            block = chunk.get_block_if_filled()
            if block is None or block.block_type != first_block.block_type:
                return False
        return True

    def get_block(self, pos: np.ndarray) -> BlockData:
        x = (pos[0] + 32) % (32 * 3)
        y = (pos[1] + 32) % (32 * 3)
        z = (pos[2] + 32) % (32 * 3)

        x_chunk, x = divmod(x, 32)
        y_chunk, y = divmod(y, 32)
        z_chunk, z = divmod(z, 32)

        chunk_index = vec3_to_index(np.array([x_chunk, y_chunk, z_chunk], dtype=np.int32), 3)
        chunk_data = self.chunks[chunk_index]
        i = vec3_to_index(np.array([x, y, z], dtype=np.int32), 32)
        return chunk_data.get_block(i)

    def get_block_no_neighbour(self, pos: np.ndarray) -> BlockData:
        chunk_data = self.chunks[13]
        i = vec3_to_index(pos, 32)
        return chunk_data.get_block(i)

    def get_adjacent_blocks(self, pos: np.ndarray) -> Tuple[BlockData, BlockData, BlockData, BlockData]:
        current = self.get_block(pos)
        back = self.get_block(pos + np.array([0, 0, -1], dtype=np.int32))
        left = self.get_block(pos + np.array([-1, 0, 0], dtype=np.int32))
        down = self.get_block(pos + np.array([0, -1, 0], dtype=np.int32))
        return (current, back, left, down)

    def get_von_neumann(self, pos: np.ndarray) -> Optional[List[Tuple[Direction, BlockData]]]:
        result = [
            (Direction.Back, self.get_block(pos + np.array([0, 0, -1], dtype=np.int32))),
            (Direction.Forward, self.get_block(pos + np.array([0, 0, 1], dtype=np.int32))),
            (Direction.Down, self.get_block(pos + np.array([0, -1, 0], dtype=np.int32))),
            (Direction.Up, self.get_block(pos + np.array([0, 1, 0], dtype=np.int32))),
            (Direction.Left, self.get_block(pos + np.array([-1, 0, 0], dtype=np.int32))),
            (Direction.Right, self.get_block(pos + np.array([1, 0, 0], dtype=np.int32))),
        ]
        return result

    def get_2(self, pos: np.ndarray, offset: np.ndarray) -> Tuple[BlockData, BlockData]:
        first = self.get_block(pos)
        second = self.get_block(pos + offset)
        return (first, second)


class GreedyQuad:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def append_vertices(self, vertices: List[int], face_dir: FaceDir, axis: int, lod: Lod, ao: int, block_type: int):
        axis = axis
        jump = lod.jump_index()

        # pack ambient occlusion
        v1ao = ((ao >> 0) & 1) + ((ao >> 1) & 1) + ((ao >> 3) & 1)
        v2ao = ((ao >> 3) & 1) + ((ao >> 6) & 1) + ((ao >> 7) & 1)
        v3ao = ((ao >> 5) & 1) + ((ao >> 8) & 1) + ((ao >> 7) & 1)
        v4ao = ((ao >> 1) & 1) + ((ao >> 2) & 1) + ((ao >> 5) & 1)

        v1 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x, self.y, lod),
            v1ao,
            face_dir.normal_index(),
            block_type
        )
        v2 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x + self.w, self.y, lod),
            v2ao,
            face_dir.normal_index(),
            block_type
        )
        v3 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x + self.w, self.y + self.h, lod),
            v3ao,
            face_dir.normal_index(),
            block_type
        )
        v4 = make_vertex_u32(
            face_dir.world_to_sample(axis, self.x, self.y + self.h, lod),
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


# - Utility functions -
def generate_indices(vertex_count: int) -> List[int]:
    indices_count = vertex_count // 4
    indices = []
    for vert_index in range(indices_count):
        base = vert_index * 4
        indices.extend([
            base, base + 1, base + 2,
            base, base + 2, base + 3
        ])
    return indices

def make_vertex_u32(pos: np.ndarray, ao: int, normal: int, block_type: int) -> int:
    return (
        (pos[0] & 0x3F) |
        ((pos[1] & 0x3F) << 6) |
        ((pos[2] & 0x3F) << 12) |
        (ao << 18) |
        (normal << 21) |
        (block_type << 25)
    )

@njit
def vec3_to_index(pos: np.ndarray, bounds: int) -> int:
    x_i = pos[0] % bounds
    y_i = pos[1] * bounds
    z_i = pos[2] * (bounds * bounds)
    return (x_i + y_i + z_i)

@njit
def index_to_ivec3_bounds(i: int, bounds: int) -> np.ndarray:
    x = i % bounds
    y = (i // bounds) % bounds
    z = i // (bounds * bounds)
    return np.array([x, y, z], dtype=np.int32)

@njit
def index_to_ivec3(i: int) -> np.ndarray:
    x = i % 32
    y = (i // 32) % 32
    z = i // (32 * 32)
    return np.array([x, y, z], dtype=np.int32)

@njit
def add_voxel_to_axis_cols(b: BlockData, x: int, y: int, z: int, axis_cols: np.ndarray):
    if b.is_solid():
        axis_cols[0, z, x] |= 1 << y
        axis_cols[1, y, z] |= 1 << x
        axis_cols[2, y, x] |= 1 << z

@njit
def trailing_zeros_64(value: np.uint64) -> int:
    if value == 0:
        return 64
    count = 0
    while (value & 1) == 0:
        count += 1
        value >>= 1
    return count


