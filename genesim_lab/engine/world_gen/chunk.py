# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from genesim_lab.meshes.chunk_mesh import ChunkMesh


# World generator ------------------------------|
class Chunk:

    def __init__(self, app):
        self.app = app
        self.voxels: np.array = self.build_voxels()
        self.mesh: ChunkMesh = None
        self.build_mesh()

    def build_mesh(self):
        self.mesh = ChunkMesh(self)

    def render(self):
        self.mesh.render()

    def build_voxels(self):
        chunk_size = stg.world.chunk_size
        chunk_area = stg.world.chunk_area
        # Empty chunk
        voxels = np.zeros(stg.world.chunk_vol, dtype='uint8')

        # Fill chunk
        for x in range(chunk_size):
            for z in range(chunk_size):
                for y in range(chunk_size):
                    voxels[x + chunk_size * z + chunk_area * y] = x + y + z
        return voxels
