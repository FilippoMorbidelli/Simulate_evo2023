# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
import random
from genesim_lab.engine.settings import *
from genesim_lab.meshes.chunk_mesh import ChunkMesh


# World generator ------------------------------|
class Chunk:

    def __init__(self, world, index):
        self.app = world.app
        self.world = world
        self.index = index
        self.pos = (self.index - offset) * c_scale
        self.info = world.info
        self.m_model = self.get_model_matrix()

        # Build chunk
        self.voxels: np.array = None
        self.current_vbo: np.array = None
        self.mesh: ChunkMesh = None
        self.is_empty = True

        self.center = np.array(self.pos + 0.5 * c_scale, dtype='float32')  #(glm.vec3(self.index) + 0.5) * c_scale #
        self.is_on_frustum = self.app.player.frustum.is_on_frustum

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.pos)  #glm.vec3(self.index) * c_scale
        return m_model

    def set_uniform(self):
        self.mesh.program['m_model'].write(self.m_model)

    def build_mesh(self):
        self.mesh = ChunkMesh(self)

    def render(self):
        if not self.is_empty:  # and self.is_on_frustum(self.center):
            self.set_uniform()
            self.mesh.render()

    def build_voxels(self):
        # Empty chunk
        voxels = np.zeros(self.info.c_vol, dtype='uint8')
        rng = random.randrange(1, 100)

        # Fill chunk
        cx, cy, cz = glm.ivec3(self.index) * c_size

        for x in range(c_size):
            for z in range(c_size):
                wx = x + cx
                wz = z + cz
                world_height = int(glm.simplex(glm.vec2(wx, wz) * 0.01) * 32 + 32)
                local_height = min(world_height - cy, c_size)

                for y in range(local_height):
                    wy = y + cy
                    voxels[x + c_size * z + self.info.c_area * y] = 1

        if np.any(voxels):
            self.is_empty = False

        return voxels
