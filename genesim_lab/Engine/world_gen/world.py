# Evolution simulation project - world_objects generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
import math
import numpy as np
import numpy.random as rnd
from numba import types
from numba.typed import Dict
from genesim_lab.Engine.world_gen.chunk import Chunk
from genesim_lab.Engine.player.voxel_handler import VoxelHandler
from genesim_lab.Engine.world_objects.voxel_marker import VoxelMarker
from genesim_lab.Engine.world_objects.celestial_body import Celestial
from genesim_lab.Engine.world_gen.sparsevoxeloctree import build_svo
from genesim_lab.Engine.settings import ChunkMeshSettings


# World generator ------------------------------|
class World:
    # World structure is divided into multiple regions of stg.world.r_size chunks on each dim

    def __init__(self, app, load_voxels = None):
        self.app = app
        self.info = app.stg.world

        # Retrieve mesh settings and frustum
        self.mesh_stg = self.get_mesh_stg()
        self.frustum_check = self.app.player.frustum.is_on_frustum

        # Create or load world
        if load_voxels is None:

            # Create new world
            regions_to_create = get_init_regions(self.info, self.app.player.position)

            # Prepare voxel dict to be also used by Numba NJit
            self.voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])
            for r_id in regions_to_create.keys():
                self.voxels[r_id] = np.zeros([self.info.r_vol, self.info.c_vol], dtype='uint8')

            # Prepare chunks dict
            self.chunks: dict = {r_id: [None for _ in range(self.info.r_vol)] for r_id in regions_to_create.keys()}

            # Build Chunks, mesh and SVO
            self.build_chunks(regions_to_create, new=True)
            self.build_chunk_mesh()

            # Build world sparse voxel octree
            self.svo: dict = {r: build_svo(self.app, self.info, self.chunks[r], regions_to_create[r]) for r in
                              regions_to_create.keys()}

        else:

            # Load world
            # Prepare voxel dict to be also used by Numba NJit
            self.voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])
            for r_id in load_voxels.keys():
                self.voxels[r_id] = np.zeros([self.info.r_vol, self.info.c_vol], dtype='uint8')

            # Prepare chunks dict
            self.chunks: dict = {r_id: [None for _ in range(self.info.r_vol)] for r_id in load_voxels.keys()}

            # Build Chunks, mesh and SVO
            self.build_chunks(load_voxels, new=False)
            self.build_chunk_mesh()

            # Build world sparse voxel octree
            self.svo: dict = {r: build_svo(self.app, self.info, self.chunks[r], self.chunks[r][0].r_index) for r in
                              load_voxels.keys()}

        # Player interactivity
        self.voxel_handler = VoxelHandler(self)
        self.voxel_marker = VoxelMarker(self.voxel_handler)

        # World objects
        self.celestial = Celestial(self)

    def build_chunks(self, load_voxels, new=True):
        for r in load_voxels.keys():

            # Compute region chunk distribution
            if new:
                w, h, d = load_voxels[r]
            else:
                h = r // self.info.depth_rn * self.info.width_rn
                d = (r - h * self.info.depth_rn * self.info.width_rn) // self.info.width_rn
                w = r - h * self.info.depth_rn * self.info.width_rn - d * self.info.width_rn

            width = int(self.info.w_width - w * self.info.r_size) if w == self.info.width_rn - 1 else self.info.r_size
            height = int(self.info.w_height - h * self.info.r_size) if h == self.info.height_rn - 1 else self.info.r_size
            depth = int(self.info.w_width - d * self.info.r_size) if d == self.info.depth_rn - 1 else self.info.r_size

            for x in range(width):
                for y in range(height):
                    for z in range(depth):
                        chunk = Chunk(self, index=(x, y, z), r_index=(w, h, d))

                        chunk_index = x + self.info.r_size * z + self.info.r_area * y
                        self.chunks[r][chunk_index] = chunk

                        # Put the chunk voxels in a separate array
                        if new:
                            self.voxels[r][chunk_index] = chunk.build_voxels()
                        else:
                            self.voxels[r][chunk_index] = load_voxels[r][chunk_index, :]
                            chunk.is_empty = False

                        # Get pointer to voxels
                        chunk.voxels = self.voxels[r][chunk_index]

    def build_chunk_mesh(self):
        for r in self.chunks.values():
            for chunk in r:
                if chunk is not None:
                    chunk.build_mesh()

    def update_active_regions(self):
        # Compute new regions
        p_pos = self.app.player.position
        new_reg = get_init_regions(self.info, p_pos)

        #Get Set of both region dicts
        current_set = set(self.voxels.keys())
        new_set = set(new_reg.keys())

        to_delete = list(current_set - new_set)
        to_add    = list(new_set - current_set)

        # Delete regions
        for rid in to_delete:
            # Save region to delete
            self.app.save_load.save_single_region(rid)
            # Delete region data
            self.voxels.pop(rid)
            self.chunks.pop(rid)
            self.svo.pop(rid)

        # Load/Create regions
        for rid in to_add:
            # Send to Load Process queue the required region to be loaded or created
            self.app.req_queues["load"].put([rid, new_reg[rid]])


    def update(self):
        # Update Regions
        self.update_active_regions()

        # Update Sky objects
        self.celestial.update()

        # Update Player functions
        self.voxel_handler.update()  # Update ray casting algorithm for player
        self.voxel_marker.update()  # Update voxel marker obtained from ray casting algorithm

    def render(self):
        # Render Chunks of each region
        for rid, svo in self.svo.items():
            self.svo_frustum_render(svo, rid)

        # Render Sky objects
        self.celestial.render()

        # Render Player functions
        self.voxel_marker.render()

    def svo_frustum_render(self, node, region):
        # Check if node is visible and inside player frustum
        if node.visibility and self.frustum_check(node.center, sphere_radius=node.sides.x * 0.5 * math.sqrt(3)):

            # Check if parent at level X contains data to be rendered
            if node.data:

                for ck_id, _ in node.data.items():
                    self.chunks[region][ck_id].render()

            # If node doesn't contain item check if it has children and is visible from player frustum
            elif node.children:

                for child_coord, child_node in node.children.items():
                    self.svo_frustum_render(child_node, region)

    def get_mesh_stg(self):

        stg = ChunkMeshSettings(self.info.c_size, self.info.c_area, self.info.c_vol,
                                self.info.offset[0], self.info.offset[1], self.info.offset[2],
                                self.info.v_x, self.info.v_y, self.info.v_z,
                                self.info.r_size, self.info.r_area, self.info.rc_size,
                                self.info.width_rn, self.info.height_rn, self.info.depth_rn)

        return stg

# -- World Util functions ----------------------------------------------------------------------------------------------
def get_init_regions(w_info, pos):
    rx, ry, rz = (pos / w_info.scale + w_info.offset * w_info.c_size) // w_info.rc_size

    regions = {}
    for x in [rx - 1, rx, rx + 1]:

        # Check if outside world bound
        if not 0 <= x < w_info.width_rn:
            continue

        for y in [ry - 1, ry, ry + 1]:

            # Check if outside world bound
            if not 0 <= y < w_info.height_rn:
                continue

            for z in [rz - 1, rz, rz + 1]:

                # Check if outside world bound
                if not 0 <= z < w_info.depth_rn:
                    continue

                r_id = int(x + w_info.width_rn * z + w_info.width_rn * w_info.depth_rn * y)
                regions[r_id] = [x, y, z]

    return regions


class SimGrid:
    def __init__(self, settings):
        # Preallocate attributes
        self.masks = type("Terrain masks", (), {})()

        # Preallocate grid
        n = settings['terrain']['shape']
        grid = np.ones(n, dtype=np.int32)

        # Compute noise
        noise = fractal_noise(settings)
        noise = (noise - noise.min()) / (noise.max() - noise.min())

        # Generate water
        threshold = settings['terrain']['water_threshold']
        grid[noise < threshold] = settings['terrain']['water_ID']

        # Generate vegetation
        potential = ((noise - threshold) / (1 - threshold)) ** 4 * 0.7
        mask = (noise > threshold) * (rnd.rand(n[0], n[1]) < potential)
        grid[mask] = settings['terrain']['vegetation_ID']
        self.grid = grid

        # Extract terrain masks
        veg_mask = np.argwhere(mask)
        veg_mask[:, 0] = veg_mask[:, 0] - n[0] / 2  # change y values (on rows)
        veg_mask[:, 0] = - veg_mask[:, 0]
        veg_mask[:, 1] = veg_mask[:, 1] - n[1] / 2  # change x values (on columns)
        self.masks.veg_mask = veg_mask

        grass_mask = np.argwhere(grid == 1)
        grass_mask[:, 0] = grass_mask[:, 0] - n[0] / 2
        grass_mask[:, 0] = - grass_mask[:, 0]
        grass_mask[:, 1] = grass_mask[:, 1] - n[1] / 2
        self.masks.grass_mask = grass_mask

        water_mask = np.argwhere(grid == 0)
        water_mask[:, 0] = water_mask[:, 0] - n[0] / 2
        water_mask[:, 0] = - water_mask[:, 0]
        water_mask[:, 1] = water_mask[:, 1] - n[1] / 2
        self.masks.water_mask = water_mask


# Utility functions----------------------------------
def generate_perlin_noise_2d(shape, res):
    f = lambda tt: 6 * tt ** 5 - 15 * tt ** 4 + 10 * tt ** 3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1

    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)

    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)

    # Interpolation
    t = f(grid)
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)


def fractal_noise(settings):
    # Get grid settings
    shape = settings['terrain']['shape']
    res = settings['terrain']['resolution']
    octaves = settings['terrain']['octaves']
    persistence = settings['terrain']['persistence']

    # Compute fractal noise
    noise = np.zeros(shape)
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        noise += amplitude * generate_perlin_noise_2d(shape, (frequency * res[0], frequency * res[1]))
        frequency *= 2


        amplitude *= persistence
    return noise
