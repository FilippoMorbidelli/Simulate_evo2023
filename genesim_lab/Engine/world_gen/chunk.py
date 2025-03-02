# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
import random
from pyglm import glm
import numpy as np
from genesim_lab.Meshes.chunk_mesh import ChunkMesh
from genesim_lab.Engine.settings import Proxy


# World generator ------------------------------|
class Chunk:

    def __init__(self, world, index, r_index):
        self.app = world.app
        self.world = world
        self.info = world.info
        self.mesh_stg = world.mesh_stg
        self.index = index
        self.r_index = rx, ry, rz = np.array(r_index)
        self.pos = (glm.vec3(self.index) + glm.vec3(rx, ry, rz) * self.info.r_size - self.info.offset) * self.info.c_scale
        self.m_model = self.get_model_matrix()

        # Build chunk
        self.voxels: np.array = None
        self.mesh: ChunkMesh = None
        self.is_empty = True

        self.center = glm.vec3(self.pos) + 0.5 * self.info.c_scale
        self.is_on_frustum = self.app.player.frustum.is_on_frustum

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.pos)  #glm.vec3(self.index) * c_scale
        return m_model

    def set_uniform(self):
        self.mesh.program['m_model'].write(self.m_model)
        self.mesh.program_greedy['m_model'].write(self.m_model)

    def build_mesh(self, asynch=False, vao_v = None, vao_vg = None):
        self.mesh = ChunkMesh(self, asynch=asynch, vao_v = vao_v, vao_vg = vao_vg)

    def render(self):
        if not self.is_empty:
            self.set_uniform()

            if glm.distance(self.app.player.frustum.cam.position, self.center) > self.info.c_threshold:
                self.mesh.render_greedy()
            else:
                self.mesh.render()

    def build_voxels(self):
        # Empty chunk
        voxels = np.zeros(self.info.c_vol, dtype='uint8')
        rng = random.randrange(1, 100)

        # Fill chunk
        cx, cy, cz = (glm.ivec3(self.index) + glm.ivec3(self.r_index) * self.info.r_size) * self.info.c_size

        for x in range(self.info.c_size):
            for z in range(self.info.c_size):
                wx = x + cx
                wz = z + cz
                world_height = int(glm.simplex(glm.vec2(wx, wz) * 0.01) * 32 + 32)
                local_height = min(world_height - cy, self.info.c_size)

                for y in range(local_height):
                    wy = y + cy
                    voxels[x + self.info.c_size * z + self.info.c_area * y] = 1

        if np.any(voxels):
            self.is_empty = False

        return voxels


class ChunkProxy(Chunk):

    def __init__(self, w_stg, index, r_index):
        # Create proxy class
        world = Proxy()
        world.app = Proxy()
        world.app.player = Proxy()
        world.app.player.frustum = Proxy()
        world.app.player.frustum.is_on_frustum = None
        world.info = w_stg
        world.mesh_stg = None
        # Super init with proxy class
        super().__init__(world, index, r_index)