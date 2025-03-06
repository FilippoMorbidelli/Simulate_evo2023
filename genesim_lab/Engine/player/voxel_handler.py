# Evolution simulation project - voxel handler module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes:

# Import packages ------------------------------|
from genesim_lab.Engine.settings import *
from genesim_lab.Meshes.chunk_mesh_builder import get_chunk_index
from math import floor


# Voxel Handler --------------------------------|
class VoxelHandler:

    def __init__(self, world):
        self.app = world.app
        self.chunks = world.chunks
        self.w_info = world.app.stg.world

        # Ray casting result
        self.chunk = None
        self.voxel_id = None
        self.voxel_index = None
        self.voxel_local_pos = None
        self.voxel_world_pos = None
        self.voxel_normal = None

        self.interaction_mode = 0  # 0: remove voxel  1: add voxel
        self.new_voxel_id = 1

    def add_voxel(self):
        if self.voxel_id:
            # Check voxel id along normal
            result = self.get_voxel_id(self.voxel_world_pos + self.voxel_normal)

            # Is new place empty?
            if not result[0]:
                _, voxel_index, _, chunk = result
                chunk.voxels[voxel_index] = self.new_voxel_id
                chunk.mesh.rebuild()

                # was it an empty chunk
                if chunk.is_empty:
                    chunk.is_empty = False

    def rebuild_adj_chunk(self, adj_voxel_pos):
        r_index, index = get_chunk_index(adj_voxel_pos)
        # If chunk exists rebuild it
        if r_index != -1 and self.chunks[r_index][index] is not None:
            self.chunks[r_index][index].mesh.rebuild()

    def rebuild_adjacent_chunks(self):
        lx, ly, lz = self.voxel_local_pos
        wx, wy, wz = self.voxel_world_pos

        if lx == 0:
            self.rebuild_adj_chunk((wx - 1, wy, wz))
        elif lx == self.w_info.c_size - 1:
            self.rebuild_adj_chunk((wx + 1, wy, wz))

        if ly == 0:
            self.rebuild_adj_chunk((wx, wy - 1, wz))
        elif ly == self.w_info.c_size - 1:
            self.rebuild_adj_chunk((wx, wy + 1, wz))

        if lz == 0:
            self.rebuild_adj_chunk((wx, wy, wz - 1))
        elif lz == self.w_info.c_size - 1:
            self.rebuild_adj_chunk((wx, wy, wz + 1))

    def remove_voxel(self):
        if self.voxel_id:
            self.chunk.voxels[self.voxel_index] = 0
            self.chunk.mesh.rebuild()
            self.rebuild_adjacent_chunks()

    def set_voxel(self):
        if self.interaction_mode:
            self.add_voxel()
        else:
            self.remove_voxel()

    def switch_mode(self):
        self.interaction_mode = not self.interaction_mode

    def update(self):
        self.ray_cast()

    def ray_cast(self):
        # start point
        x1, y1, z1 = self.app.player.position
        # end point
        x2, y2, z2 = self.app.player.position + self.app.player.forward * self.app.stg.interaction.max_ray_dist

        current_voxel_pos = glm.vec3(floor(x1), self.w_info.v_y * floor(self.w_info.iv_y * y1), floor(z1))
        self.voxel_id = 0
        self.voxel_normal = glm.vec3(0)
        step_dir = -1

        dx = glm.sign(x2 - x1)
        delta_x = min(dx / (x2 - x1), 10000000.0) if dx != 0 else 10000000.0
        max_x = delta_x * (1.0 - glm.fract(x1)) if dx > 0 else delta_x * glm.fract(x1)

        dy = glm.sign(y2 - y1) * self.w_info.scale.y
        delta_y = min(dy / (y2 - y1), 10000000.0) if dy != 0 else 10000000.0
        max_y = delta_y * (1.0 - glm.fract(y1)) if dy > 0 else delta_y * glm.fract(y1)

        dz = glm.sign(z2 - z1)
        delta_z = min(dz / (z2 - z1), 10000000.0) if dz != 0 else 10000000.0
        max_z = delta_z * (1.0 - glm.fract(z1)) if dz > 0 else delta_z * glm.fract(z1)

        while not (max_x > 1.0 and max_y > 1.0 and max_z > 1.0):

            result = self.get_voxel_id(voxel_world_pos=current_voxel_pos)
            if result[0]:
                self.voxel_id, self.voxel_index, self.voxel_local_pos, self.chunk = result
                self.voxel_world_pos = current_voxel_pos

                if step_dir == 0:
                    self.voxel_normal.x = -dx
                elif step_dir == 1:
                    self.voxel_normal.y = -dy
                else:
                    self.voxel_normal.z = -dz
                return True

            if max_x < max_y:
                if max_x < max_z:
                    current_voxel_pos.x += dx
                    max_x += delta_x
                    step_dir = 0
                else:
                    current_voxel_pos.z += dz
                    max_z += delta_z
                    step_dir = 2
            else:
                if max_y < max_z:
                    current_voxel_pos.y += dy
                    max_y += delta_y
                    step_dir = 1
                else:
                    current_voxel_pos.z += dz
                    max_z += delta_z
                    step_dir = 2
        return False

    def get_voxel_id(self, voxel_world_pos):
        world_pos_off = glm.ivec3(voxel_world_pos / self.w_info.scale + self.w_info.offset * self.w_info.c_size)
        rx, ry, rz = region_pos = glm.ivec3(world_pos_off // self.w_info.rc_size)
        cx, cy, cz = glm.ivec3((world_pos_off - region_pos * self.w_info.rc_size) // self.w_info.c_size)

        if 0 <= rx < self.w_info.width_rn and 0 <= ry < self.w_info.height_rn and 0 <= rz < self.w_info.depth_rn:
            region_index = rx + self.w_info.width_rn * rz + self.w_info.depth_rn * self.w_info.width_rn * ry
            chunk_index = cx + self.w_info.r_size * cz + self.w_info.r_area * cy
            try:
                chunk = self.chunks[region_index][chunk_index] # Maybe add a try - exception if region is not loaded?
            except (Exception, ):
                chunk = None
                print("No voxel available for handling")

            if chunk is None:
                return 0, 0, 0, 0

            lx, ly, lz = voxel_local_pos = (world_pos_off - region_pos * self.w_info.rc_size) % self.w_info.c_size

            voxel_index = int(lx + self.w_info.c_size * lz + self.w_info.c_area * ly)
            voxel_id = chunk.voxels[voxel_index]

            return voxel_id, voxel_index, voxel_local_pos, chunk
        return 0, 0, 0, 0

