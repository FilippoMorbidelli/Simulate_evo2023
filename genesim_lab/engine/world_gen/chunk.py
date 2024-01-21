# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation
import random

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from genesim_lab.meshes.chunk_mesh import ChunkMesh


# World generator ------------------------------|
class Chunk:

    def __init__(self, world, position):
        self.app = world.app
        self.world = world
        self.position = position
        self.info = world.info
        self.m_model = self.get_model_matrix()

        # Build chunk
        self.voxels: np.array = None
        self.mesh: ChunkMesh = None
        self.is_empty = True

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), glm.vec3(self.position) * self.info.c_size * [1, 0.5, 1])
        return m_model

    def set_uniform(self):
        self.mesh.program['m_model'].write(self.m_model)

    def build_mesh(self):
        self.mesh = ChunkMesh(self)

    def render(self):
        if not self.is_empty:
            self.set_uniform()
            self.mesh.render()

    def build_voxels(self):
        c_size = self.info.c_size
        # Empty chunk
        voxels = np.zeros(self.info.c_vol, dtype='uint8')
        rng = random.randrange(1, 100)

        # Fill chunk
        cx, cy, cz = glm.ivec3(self.position) * c_size

        for x in range(c_size):
            for z in range(c_size):
                wx = x + cx
                wz = z + cz
                world_height = int(glm.simplex(glm.vec2(wx, wz) * 0.01) * 32 + 32)
                local_height = min(world_height - cy, c_size)

                for y in range(local_height):
                    wy = y + cy
                    voxels[x + c_size * z + self.info.c_area * y] = rng

        if np.any(voxels):
            self.is_empty = False

        return voxels
