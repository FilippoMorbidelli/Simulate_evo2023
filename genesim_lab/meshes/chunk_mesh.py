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

        self.vbo_format_vert = '3f2'  # Vertex are passed as float16
        self.vbo_format_extra = '1u1 1u1'  # Voxel_ID and Face_ID are passed as uint8
        self.format_size = [sum(int(fmt[:1]) for fmt in self.vbo_format_vert.split()),
                            sum(int(fmt[:1]) for fmt in self.vbo_format_extra.split())]
        self.attrs_vert = ('in_position',)
        self.attrs_extra = ('voxel_id', 'face_id')
        self.vao = self.get_vao()

    def get_vertex_data(self):
        mesh = build_chunk_mesh(
            chunk_voxels=self.chunk.voxels,
            format_size=self.format_size,
            dim=self.chunk.info,
            chunk_pos=self.chunk.position,
            world_voxels=self.chunk.world.voxels
        )
        return mesh
