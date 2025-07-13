# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from src.Meshes.chunk_mesh_utils import *
from numpy.typing import NDArray
from numba.typed import Dict as nDict

# World generator ------------------------------|
# New Chunk Mesh builder only greedy with AO!! Copied from Rust fast mesher (https://www.youtube.com/watch?v=qnGoGq7DWMc)
#-
def build_chunk_mesh_greedy(chunk_voxels: np.ndarray,
                            neighbors: np.ndarray,
                            chunk_pos: List[int32],
                            format_s: int32,
                            lod: Lod = Lod.L32) -> Optional[np.ndarray]:

    # If Chunk is empty exit
    assert len(chunk_voxels) == CHUNK_SIZE3 or len(chunk_voxels) == 1
    if not np.any(chunk_voxels):
        return np.empty(1, dtype='uint32')

    # Array containing mesh vertices already packed for GPU
    vertices = np.empty(CHUNK_SIZE3 * 18 * format_s, dtype='uint32')

    # solid binary for each x,y,z axis (3)
    axis_cols: NDArray[np.uint64] = np.zeros((3, PAD_SIZE, PAD_SIZE), dtype=uint64)

    # cull mask to perform greedy slicing
    col_face_masks: NDArray[np.uint64] = np.zeros((6, PAD_SIZE, PAD_SIZE), dtype=uint64)

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
    for z in [0, PAD_SIZE - 1]:
        neighbor_id = FaceDir.Forward if z else FaceDir.Back
        z_index = z * CHUNK_SIZE

        for y in range(PAD_SIZE):
            y_index = y * CHUNK_SIZE2

            for x in range(PAD_SIZE):
                i = y_index + z_index + x

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x, y, z, axis_cols)

    # Along y axis
    for y in [0, PAD_SIZE - 1]:
        neighbor_id = FaceDir.Up if y else FaceDir.Down
        y_index = y * CHUNK_SIZE2

        for z in range(PAD_SIZE):
            z_index = z * CHUNK_SIZE

            for x in range(PAD_SIZE):
                i = y_index + z_index + x

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x, y, z, axis_cols)

    # Along x axis
    for x in [0, PAD_SIZE - 1]:
        neighbor_id = FaceDir.Right if x else FaceDir.Left

        for z in range(PAD_SIZE):
            z_index = z * CHUNK_SIZE

            for y in range(PAD_SIZE):
                y_index = y * CHUNK_SIZE2
                i = y_index + z_index + x

                add_voxel_to_axis_cols(neighbors[neighbor_id, i], x, y, z, axis_cols)

    # Face culling
    for axis in range(3):
        for z in range(PAD_SIZE):
            for x in range(PAD_SIZE):
                col = axis_cols[axis, z, x]
                col_face_masks[2 * axis + 0, z, x] = col & ~(col << 1)
                col_face_masks[2 * axis + 1, z, x] = col & ~(col >> 1)

    # Greedy meshing planes for every axis (6)
    # cannot use List[Dict[int, Dict[int, np.ndarray]]] due to Numba so trying with NumbaDict but may be a bottleneck!!
    data = [nDict.empty(key_type=uint64, value_type=nDict.empty(key_type=uint32, value_type=uint8[:])) for _ in range(6)]

    # Compute Ambient Occlusion
    for axis in range(6):
        for z in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                # skip padded by adding 1(for x padding) and (z+1) for (z padding)
                col = col_face_masks[axis, z + 1, x + 1]
                # removes the right most and left most padding values, because they are invalid
                col >>= 1
                col &= ~(1 << CHUNK_SIZE)

                while col != 0:
                    # py implementation of trailing zeros (uint64)
                    y = bit_length(col & -col)
                    col &= col - 1 # clear least significant set bit

                    # get the voxel position based on axis
                    match axis:
                        case FaceDir.Up | FaceDir.Down:
                            voxel_pos: NDArray[int32] = np.array([x, y, z], dtype=int32)
                        case FaceDir.Left | FaceDir.Right:
                            voxel_pos: NDArray[int32] = np.array([y, z, x], dtype=int32)
                        case FaceDir.Forward | FaceDir.Back | _:
                            voxel_pos: NDArray[int32] = np.array([x, z, y], dtype=int32)

                    # compute ambient occlusion
                    ao_index = 0
                    for ao_i, ao_offset in enumerate(ADJACENT_AO_DIRS):
                        # ambient occlusion is sampled based on axis(ascent or descent)
                        match axis:
                            case FaceDir.Down:
                                ao_sample_offset = np.array([ao_offset[0], -1, ao_offset[1]], dtype=int32)
                            case FaceDir.Up:
                                ao_sample_offset = np.array([ao_offset[0],  1, ao_offset[1]], dtype=int32)
                            case FaceDir.Left:
                                ao_sample_offset = np.array([-1, ao_offset[1], ao_offset[0]], dtype=int32)
                            case FaceDir.Right:
                                ao_sample_offset = np.array([ 1, ao_offset[1], ao_offset[0]], dtype=int32)
                            case FaceDir.Forward:
                                ao_sample_offset = np.array([ao_offset[0], ao_offset[1], -1], dtype=int32)
                            case FaceDir.Back | _:
                                ao_sample_offset = np.array([ao_offset[0], ao_offset[1],  1], dtype=int32)

                        ao_voxel_pos = voxel_pos + ao_sample_offset

                        # Find if neighbor voxel is solid or not to count for AO
                        is_valid_neighbor = np.sum((ao_voxel_pos < 0) | (ao_voxel_pos > 31))
                        if not is_valid_neighbor:
                            ao_block = chunk_voxels[ao_voxel_pos[2] * CHUNK_SIZE + ao_voxel_pos[1] * CHUNK_SIZE2 + ao_voxel_pos[0]]
                        elif is_valid_neighbor == 1:
                            face = bound_to_face(np.array((ao_voxel_pos < 0) + (ao_voxel_pos > 31)))
                            ao_block = neighbors[face, (ao_voxel_pos[2] & 0b11111) * CHUNK_SIZE + (ao_voxel_pos[1] & 0b11111) * CHUNK_SIZE2 + (ao_voxel_pos[0] & 0b11111)]
                        else :
                            ao_block = 0

                        if ao_block != BlockType.Air:
                            ao_index |= 1 << ao_i

                    current_voxel = chunk_voxels[voxel_pos[2] * CHUNK_SIZE + voxel_pos[1] * CHUNK_SIZE2 + voxel_pos[0]]
                    block_hash = ao_index | (current_voxel << 9)

                    if block_hash not in data[axis]:
                        data[axis][block_hash] = {}

                    if y not in data[axis][block_hash]:
                        data[axis][block_hash][y] = {}

                    data[axis][block_hash][y][x] |= 1 << z

    # Sample planes for greedy meshing
    for axis, block_ao_data in enumerate(data):
        for block_hash, axis_plane in block_ao_data.items():
            ao = block_hash & 0b111111111
            block_type = block_hash >> 9

            for axis_pos, plane in axis_plane.items():
                quads_from_axis = greedy_mesh_binary_plane(plane, lod.size())

                #for q in quads_from_axis:
                #    q.append_vertices(vertices, axis, axis_pos, lod, ao, block_type)

    #mesh.vertices.extend(vertices)
    #if not mesh.vertices:
    #    return None

    #mesh.indices = generate_indices(len(mesh.vertices))
    #return mesh

@njit
def greedy_mesh_binary_plane(voxel_mask, lod: int) -> List[int32]:
    row_length = CHUNK_SIZE
    greedyQuads = []

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
            h_as_mask = (1 << trailing_ones) - 1 if trailing_ones > 0 else 0
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
            greedyQuads.append([h, w, trailing_ones, row])

            h += trailing_ones

    return greedyQuads

#-------------------------------------------------------------------------------
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
