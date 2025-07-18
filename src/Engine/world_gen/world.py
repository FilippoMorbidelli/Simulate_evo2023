# Evolution simulation project - world_objects generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
import math
import numpy as np
import time
import numpy.random as rnd
from numba import types
from numba.typed import Dict
from src.Engine.world_gen.chunk import Chunk
from src.Engine.player.voxel_handler import VoxelHandler
from src.Engine.world_objects.voxel_marker import VoxelMarker
from src.Engine.world_objects.celestial_body import Celestial
from src.Engine.world_gen.sparsevoxeloctree import build_svo
from src.Meshes.chunk_mesh_builder import let_settings_global


# World generator ------------------------------|
class World:
    # World structure is divided into multiple regions of stg.world.r_size chunks on each dim

    def __init__(self, app, load_voxels = None):
        self.app = app
        self.info = app.stg.world
        self.center_region = 0

        # Load and Save processes status
        self.load_status = "Idle"
        self.save_status = "Idle"
        let_settings_global(self.info)

        # Retrieve frustum
        self.frustum_check = self.app.player.frustum.is_on_frustum

        # Instantiate voxel dict in NJit
        self.voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])

        # Create or load world
        if load_voxels is None:

            # Create new world
            regions_to_create, _, _ = get_init_regions(self.info, self.app.player.position, self.center_region)

            # Prepare voxel dict to be also used by Numba NJit
            for r_id in regions_to_create.keys():
                self.voxels[r_id] = np.zeros([self.info.r_vol, self.info.c_vol], dtype='uint8')

            # Prepare chunks and svo dict
            self.chunks = dict()
            self.svo = dict()

            # Send to Load Process queue the required region to be loaded or created
            self.app.req_queues["load"].put(["InitWorld", list(regions_to_create.keys()), regions_to_create, {}, self.info, self.app.stg.util])
            # Update local load process status
            self.load_status = "Occupied"

        else:

            # Load world
            # Prepare voxel dict to be also used by Numba NJit
            for r_id in load_voxels.keys():
                self.voxels[r_id] = np.zeros([self.info.r_vol, self.info.c_vol], dtype='uint8')

            # Prepare chunks and svo dict
            self.chunks = dict()
            self.svo = dict()

            # Send to Load Process queue the required region to be loaded or created
            self.app.req_queues["load"].put(["InitWorld", list(load_voxels.keys()), load_voxels, {}, self.info, self.app.stg.util])
            # Update local load process status
            self.load_status = "Occupied"

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

        # If no responses are available check if active regions changed
        if self.app.resp_queue.empty():

            # Compute new regions
            p_pos = self.app.player.position
            new_reg, self.center_region, p_dir = get_init_regions(self.info, p_pos, self.center_region)

            #Get Set of both region dicts
            current_set = set(self.voxels.keys())
            new_set = set(new_reg.keys())

            to_delete = list(current_set - new_set)
            to_add    = list(new_set - current_set)

            # Delete regions
            if self.save_status == "Idle" and self.load_status == "Idle" and to_delete:
                # Copy voxels dict to send
                to_send_dict = dict()
                for r in to_delete:
                    to_send_dict[r] = self.voxels[r]
                # Send to Save Process queue the required region to be loaded or created
                self.app.req_queues["save"].put(["SaveRegion", to_delete, to_send_dict, self.info, self.app.stg.util])
                # Update local load process status
                self.save_status = "Occupied"

            # Load/Create regions
            if self.load_status == "Idle" and to_add:
                # Copy voxels dict to send
                to_send_dict = dict()
                case = abs(p_dir[0]) + abs(p_dir[1]) + abs(p_dir[2])
                if case == 1:
                    for r in to_add:
                        r_index = [new_reg[r][0] - p_dir[0], new_reg[r][1] - p_dir[1], new_reg[r][2] - p_dir[2]]
                        r_id = int(r_index[0] + self.info.width_rn * r_index[2] + self.info.width_rn * self.info.depth_rn * r_index[1])
                        try:
                            to_send_dict[r_id] = self.voxels[r_id]
                        except (Exception, ):
                            pass
                else:
                    for r in new_set.intersection(current_set):
                        to_send_dict[r] = self.voxels[r]
                # Send to Load Process queue the required region to be loaded or created
                self.app.req_queues["load"].put(["LoadRegion", to_add, new_reg, to_send_dict, self.info, self.app.stg.util])
                # Update local load process status
                self.load_status = "Occupied"

        else:

            # Process any response
            event, status, data = self.app.resp_queue.get()

            # Match type of response
            match event:
                case "Load":

                    # Handle response depending on status
                    if status == "Init":
                        r_id, vox = data
                        # Insert voxels in Dict and instantiate chunks
                        self.voxels[r_id] = vox
                        self.chunks[r_id] = [None for _ in range(self.info.r_vol)]
                        # Update local load process status
                        self.load_status = status

                    elif status == "InProgress":
                        r_id, r_coord, vm, vmg = data
                        # Add Chunks and Meshes
                        self.asynch_load_region(r_id, r_coord, vm, vmg)
                        # Update local load process status
                        self.load_status = status

                    elif status == "DoneRegion":
                        r_id, r_coord = data
                        # Create SVO
                        self.svo[r_id] = build_svo(self.app, self.info, self.chunks[r_id], r_coord)
                        # Update local load process status
                        self.load_status = status

                    elif status == "Done":
                        # Update local load process status
                        self.load_status = "Idle"

                    elif status == "InitDone":
                        # Update local load process status
                        self.load_status = "Idle"
                        # Save World Info
                        #self.app.req_queues["save"].put(["CompleteSave", self.info, self.app.stg.util])
                        # Save Each region
                        for r in self.voxels:
                            # Send Complete save request
                            self.app.req_queues["save"].put(
                                ["SaveRegion", r, {r : self.voxels[r]}, self.info, self.app.stg.util])
                        # Update local load process status
                        self.save_status = "Occupied"


                case "Save":

                    # Handle response depending on status
                    if status == "InProgress":
                        r_id = data
                        # Delete region data
                        self.voxels.pop(r_id)
                        self.chunks.pop(r_id)
                        self.svo.pop(r_id)
                        # Reset local save process status
                        self.save_status = status

                    elif status == "Done":
                        # Reset local save process status
                        self.save_status = "Idle"

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
            chunk.build_mesh(asynch=True, vao_v=vm[c_id])

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

# -- World Util functions ----------------------------------------------------------------------------------------------
def get_init_regions(w_info, pos, c_reg):
    rx, ry, rz = (pos / w_info.scale + w_info.offset * w_info.c_size) // w_info.rc_size

    new_center = rx + w_info.width_rn * rz + w_info.width_rn * w_info.depth_rn * ry

    pry = c_reg // (w_info.width_rn * w_info.depth_rn)
    prz = (c_reg - pry * w_info.width_rn * w_info.depth_rn) // w_info.width_rn
    prx = (c_reg - pry * w_info.width_rn * w_info.depth_rn) % w_info.width_rn

    direction = [rx - prx, ry - pry, rz - prz]

    new_regions = {}
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
                new_regions[r_id] = [x, y, z]

    return new_regions, new_center, direction


# Utility functions----------------------------------
