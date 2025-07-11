# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from src.Meshes.chunk_mesh_utils import *

# World generator ------------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)
#-
def build_chunk_mesh_greedy(chunk_voxels: np.ndarray,
                            nb: np.ndarray,
                            chunk_pos: List[int32],
                            format_s: int32,
                            lod: Lod = Lod.L32) -> Optional[np.ndarray]:

    # If Chunk is empty exit
    if not np.any(chunk_voxels):
        return np.empty(1, dtype='uint32')

    # Array containing mesh vertices already packed for GPU
    vertices = np.empty(CHUNK_VOL * 18 * format_s, dtype='uint32')

    # solid binary for each x,y,z axis (3)
    axis_cols = np.zeros((3, CHUNK_SIZE_P, CHUNK_SIZE_P), dtype=uint64)

    # cull mask to perform greedy slicing
    col_face_masks = np.zeros((6, CHUNK_SIZE_P, CHUNK_SIZE_P), dtype=uint64)

#-
# Main mesh building function
#@njit(fastmath=True, cache=True, nogil=True)
def build_chunk_mesh_new(chunks_refs: ChunksRefs, lod: Lod = Lod.L32) -> Optional[ChunkMesh]:
    if chunks_refs.is_all_voxels_same():
        return None

    mesh = ChunkMesh()

    # solid binary for each x,y,z axis (3)
    axis_cols = np.zeros((3, CHUNK_SIZE_P, CHUNK_SIZE_P), dtype=uint64)

    # the cull mask to perform greedy slicing
    col_face_masks = np.zeros((6, CHUNK_SIZE_P, CHUNK_SIZE_P), dtype=uint64)

    # inner chunk voxels
    chunk = chunks_refs.chunks[vec3_to_index(np.array([1, 1, 1], dtype=int32), 3)]
    assert len(chunk.voxels) == CHUNK_SIZE3 or len(chunk.voxels) == 1

    for z in range(CHUNK_SIZE):
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                i = 0 if len(chunk.voxels) == 1 else (z * CHUNK_SIZE + y) * CHUNK_SIZE + x
                add_voxel_to_axis_cols(chunk.voxels[i], x + 1, y + 1, z + 1, axis_cols)

    # neighbor chunk voxels
    for z in [0, CHUNK_SIZE_P - 1]:
        for y in range(CHUNK_SIZE_P):
            for x in range(CHUNK_SIZE_P):
                pos = np.array([x, y, z], dtype=int32) - 1
                add_voxel_to_axis_cols(chunks_refs.get_block(pos), x, y, z, axis_cols)

    for z in range(CHUNK_SIZE_P):
        for y in [0, CHUNK_SIZE_P - 1]:
            for x in range(CHUNK_SIZE_P):
                pos = np.array([x, y, z], dtype=int32) - 1
                add_voxel_to_axis_cols(chunks_refs.get_block(pos), x, y, z, axis_cols)

    for z in range(CHUNK_SIZE_P):
        for x in [0, CHUNK_SIZE_P - 1]:
            for y in range(CHUNK_SIZE_P):
                pos = np.array([x, y, z], dtype=int32) - 1
                add_voxel_to_axis_cols(chunks_refs.get_block(pos), x, y, z, axis_cols)

    # face culling
    for axis in range(3):
        for z in range(CHUNK_SIZE_P):
            for x in range(CHUNK_SIZE_P):
                col = axis_cols[axis, z, x]
                col_face_masks[2 * axis, z, x] = col & ~(col << 1)
                col_face_masks[2 * axis + 1, z, x] = col & ~(col >> 1)

    # find faces and build binary planes
    data = [{} for _ in range(6)]  # List[Dict[int, Dict[int, np.ndarray]]]

    for axis in range(6):
        for z in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                col = col_face_masks[axis, z + 1, x + 1]
                col >>= 1
                col &= ~(1 << CHUNK_SIZE)

                while col != 0:
                    y = trailing_zeros_64(uint64(col))
                    col &= col - 1

                    if axis in (0, 1):  # down, up
                        voxel_pos = np.array([x, y, z], dtype=np.int32)
                    elif axis in (2, 3):  # left, right
                        voxel_pos = np.array([y, z, x], dtype=np.int32)
                    else:  # forward, back
                        voxel_pos = np.array([x, z, y], dtype=np.int32)

                    # calculate ambient occlusion
                    ao_index = 0
                    for ao_i, ao_offset in enumerate(ADJACENT_AO_DIRS):
                        if axis == 0:  # down
                            ao_sample_offset = np.array([ao_offset[0], -1, ao_offset[1]], dtype=np.int32)
                        elif axis == 1:  # up
                            ao_sample_offset = np.array([ao_offset[0], 1, ao_offset[1]], dtype=np.int32)
                        elif axis == 2:  # left
                            ao_sample_offset = np.array([-1, ao_offset[1], ao_offset[0]], dtype=np.int32)
                        elif axis == 3:  # right
                            ao_sample_offset = np.array([1, ao_offset[1], ao_offset[0]], dtype=np.int32)
                        elif axis == 4:  # forward
                            ao_sample_offset = np.array([ao_offset[0], ao_offset[1], -1], dtype=np.int32)
                        else:  # back
                            ao_sample_offset = np.array([ao_offset[0], ao_offset[1], 1], dtype=np.int32)

                        ao_voxel_pos = voxel_pos + ao_sample_offset
                        ao_block = chunks_refs.get_block(ao_voxel_pos)
                        if ao_block.is_solid():
                            ao_index |= 1 << ao_i

                    current_voxel = chunks_refs.get_block_no_neighbour(voxel_pos)
                    block_hash = ao_index | (current_voxel.block_type.value << 9)

                    if block_hash not in data[axis]:
                        data[axis][block_hash] = {}

                    if y not in data[axis][block_hash]:
                        data[axis][block_hash][y] = np.zeros(32, dtype=np.uint32)

                    data[axis][block_hash][y][x] |= 1 << z

    vertices = []
    for axis, block_ao_data in enumerate(data):
        facedir = list(FaceDir)[axis]

        for block_ao, axis_plane in block_ao_data.items():
            ao = block_ao & 0b111111111
            block_type = block_ao >> 9

            for axis_pos, plane in axis_plane.items():
                quads_from_axis = greedy_mesh_binary_plane(plane, lod.size())

                for q in quads_from_axis:
                    q.append_vertices(vertices, facedir, axis_pos, lod, ao, block_type)

    mesh.vertices.extend(vertices)
    if not mesh.vertices:
        return None

    mesh.indices = generate_indices(len(mesh.vertices))
    return mesh


#@njit
def greedy_mesh_binary_plane(data: np.ndarray, lod_size: int) -> List['GreedyQuad']:
    greedy_quads = []
    data = data.copy()

    for row in range(data.shape[0]):
        y = 0
        while y < lod_size:
            # find first solid
            trailing_zeros = 0
            temp = data[row] >> y
            while (temp & 1) == 0 and y < lod_size:
                trailing_zeros += 1
                temp >>= 1
                y += 1

            if y >= lod_size:
                continue

            # count trailing ones
            h = 0
            temp = data[row] >> y
            while (temp & 1) == 1 and (y + h) < lod_size:
                h += 1
                temp >>= 1

            # convert height to mask
            if h == 32:
                h_as_mask = 0xFFFFFFFF
            else:
                h_as_mask = (1 << h) - 1

            mask = h_as_mask << y

            # grow horizontally
            w = 1
            while row + w < lod_size:
                next_row_h = (data[row + w] >> y) & h_as_mask
                if next_row_h != h_as_mask:
                    break

                data[row + w] &= ~mask
                w += 1

            greedy_quads.append(GreedyQuad(
                y=y,
                w=w,
                h=h,
                x=row
            ))
            y += h

    return greedy_quads
