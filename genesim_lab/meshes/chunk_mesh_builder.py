# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


# World generator ------------------------------|
def is_void(voxel_pos, chunk_voxels):
    chunk_size = stg.world.chunk_size
    chunk_area = stg.world.chunk_area
    x, y, z = voxel_pos
    if 0 <= x < chunk_size and 0 <= y < chunk_size and 0 <= z < chunk_size:
        if chunk_voxels[x + chunk_size * z + chunk_area * y]:
            return False
    return True


def add_data(vertex_data, index, *vertices):
    for vertex in vertices:
        for attr in vertex:
            vertex_data[index] = attr
            index += 1
    return index


def build_chunk_mesh(chunk_voxels, format_size):
    chunk_size = stg.world.chunk_size
    chunk_area = stg.world.chunk_area
    vertex_data = np.empty(stg.world.chunk_vol * 18 * format_size, dtype='uint8')
    index = 0

    for x in range(chunk_size):
        for y in range(chunk_size):
            for z in range(chunk_size):
                voxel_id = chunk_voxels[x + chunk_size * z + chunk_area * y]
                if not voxel_id:
                    continue

                # top face
                if is_void((x, y + 1, z), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x    , y + 1, z    , voxel_id, 0)
                    v1 = (x + 1, y + 1, z    , voxel_id, 0)
                    v2 = (x + 1, y + 1, z + 1, voxel_id, 0)
                    v3 = (x    , y + 1, z + 1, voxel_id, 0)

                    index = add_data(vertex_data, index, v0, v3, v2, v0, v2, v1)

                # bottom face
                if is_void((x, y - 1, z), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x    , y, z    , voxel_id, 1)
                    v1 = (x + 1, y, z    , voxel_id, 1)
                    v2 = (x + 1, y, z + 1, voxel_id, 1)
                    v3 = (x    , y, z + 1, voxel_id, 1)

                    index = add_data(vertex_data, index, v0, v2, v3, v0, v1, v2)

                # right face
                if is_void((x + 1, y, z), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x + 1, y    , z    , voxel_id, 2)
                    v1 = (x + 1, y + 1, z    , voxel_id, 2)
                    v2 = (x + 1, y + 1, z + 1, voxel_id, 2)
                    v3 = (x + 1, y    , z + 1, voxel_id, 2)

                    index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                # left face
                if is_void((x - 1, y, z), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x, y    , z    , voxel_id, 3)
                    v1 = (x, y + 1, z    , voxel_id, 3)
                    v2 = (x, y + 1, z + 1, voxel_id, 3)
                    v3 = (x, y    , z + 1, voxel_id, 3)

                    index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

                # back face
                if is_void((x, y, z - 1), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x    , y    , z, voxel_id, 4)
                    v1 = (x    , y + 1, z, voxel_id, 4)
                    v2 = (x + 1, y + 1, z, voxel_id, 4)
                    v3 = (x + 1, y    , z, voxel_id, 4)

                    index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                # front face
                if is_void((x, y, z + 1), chunk_voxels):
                    # format: x, y, z, voxel_id, face_id
                    v0 = (x    , y    , z + 1, voxel_id, 5)
                    v1 = (x    , y + 1, z + 1, voxel_id, 5)
                    v2 = (x + 1, y + 1, z + 1, voxel_id, 5)
                    v3 = (x + 1, y    , z + 1, voxel_id, 5)

                    index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

    return vertex_data[:index + 1]
