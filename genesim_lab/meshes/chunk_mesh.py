# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation
import numpy as np

# Import packages ------------------------------|
from genesim_lab.meshes.base_mesh import BaseMesh
from genesim_lab.meshes.chunk_mesh_builder import build_chunk_mesh


# Import packages ------------------------------|
class ChunkMesh(BaseMesh):

    def __init__(self, chunk):
        super().__init__()
        self.app = chunk.app
        self.chunk = chunk
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.chunk

        self.vbo_format = '3u1 1u1 1u1'
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('in_position', 'voxel_id', 'face_id')  #, 'voxel_id'
        self.vao = self.get_vao()

    def get_vertex_data(self):
        mesh = build_chunk_mesh(
            chunk_voxels=self.chunk.voxels,
            format_size=self.format_size,
        )
        return mesh
