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

        # Instantiate voxel dict in NJit
        self.voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])

        # Create or load world
        if load_voxels is None:

            # Create new world
            regions_to_create = get_init_regions(self.info, self.app.player.position)

            # Prepare voxel dict to be also used by Numba NJit
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
        if self.app.resp_queue.empty():
            # If no responses are available check if active regions changed

            # Compute new regions
            p_pos = self.app.player.position
            new_reg = get_init_regions(self.info, p_pos)

            #Get Set of both region dicts
            current_set = set(self.voxels.keys())
            new_set = set(new_reg.keys())

            to_delete = list(current_set - new_set)
            to_add    = list(new_set - current_set)

            # Delete regions
            if self.app.req_queues["save"].empty():
                for rid in to_delete:
                    # Save region to delete
                    self.app.save_load.save_single_region(rid)
                    # Delete region data
                    self.voxels.pop(rid)
                    self.chunks.pop(rid)
                    self.svo.pop(rid)

            # Load/Create regions
            if self.app.req_queues["load"].empty():
                for rid in to_add:
                    # Send to Load Process queue the required region to be loaded or created
                    self.app.req_queues["load"].put([rid, new_reg[rid], self.info, self.app.stg.util])

        else:
            # Process any response
            event, status, data = self.app.resp_queue.get()

            match event:
                case "Load":

                    # Unwrap data
                    if status == "Init":
                        r_id, vox = data
                        # Insert voxels in Dict and instantiate chunks
                        self.voxels[r_id] = vox
                        self.chunks[r_id] = [None for _ in range(self.info.r_vol)]

                    elif status == "InProgress":
                        r_id, r_coord, vm, vmg = data
                        # Add Chunks and Meshes
                        self.asynch_load_region(r_id, r_coord, vm, vmg)

                    elif status == "Done":
                        r_id, r_coord = data
                        # Create SVO
                        self.svo[r_id] = build_svo(self.app, self.info, self.chunks[r_id], r_coord)

                case "Save":
                    pass

    def asynch_load_region(self, r_id, r_coord, vm, vmg):

        # Compute region chunk distribution
        w, h, d = r_coord

        for c_id in vm.keys():
            y = c_id // self.info.r_area
            z = c_id % self.info.r_area // self.info.r_size
            x = c_id % self.info.r_area % self.info.r_size

            chunk = Chunk(self, index=(x, y, z), r_index=(w, h, d))

            self.chunks[r_id][c_id] = chunk

            # Get pointer to voxels
            chunk.voxels = self.voxels[r_id][c_id]
            chunk.is_empty = False

            # Build mesh with already computed data
            if c_id in self.info.r_limit:
                chunk.build_mesh()
            else:
                chunk.build_mesh(asynch=True, vao_v=vm[c_id], vao_vg=vmg[c_id])

    def update(self):
        # Update Regions
        if self.app.custom_events.REGION_EVENT in [e.type for e in self.app.event_list]:
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
                for ck_id in node.data.keys():
                    self.chunks[region][ck_id].render()

            # If node doesn't contain item check if it has children and is visible from player frustum
            elif node.children:
                for child_node in node.children.values():
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


# Utility functions----------------------------------
