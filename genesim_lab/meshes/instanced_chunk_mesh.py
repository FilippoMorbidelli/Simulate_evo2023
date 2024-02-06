# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.meshes.base_mesh import BaseMesh
import numpy as np
from genesim_lab.engine.settings import c_vol, w_vol


# Import packages ------------------------------|
class InstChunkMesh(BaseMesh):

    def __init__(self, world):
        super().__init__()
        self.app = world.app
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.instanced_chunks

        self.vbo_format = '1u4 3u4'  # All data passed as uint8
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data', 'model',)
        self.vao = self.get_vao()

    def rebuild(self):
        self.vao = self.get_vao()

    def get_vertex_data(self):
        mesh = np.zeros(w_vol * c_vol * 18 * 4, dtype='uint32')
        return mesh
