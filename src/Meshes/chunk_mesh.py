# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from src.Meshes.base_mesh import BaseMesh
from src.Meshes.chunk_mesh_utils import get_neighbors
from src.Meshes.chunk_mesh_builder_greedy import build_chunk_mesh_greedy

import numpy as np

# Import packages ------------------------------|
class ChunkMesh(BaseMesh):

    def __init__(self, chunk, asynch=False, vao = None):
        super().__init__()
        self.app = chunk.app
        self.chunk = chunk
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.chunk

        self.vbo_format = '1u4'  # All data passed as uint8
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data',)

        if not asynch:
            self.vao = self.get_vao()
        else:
            self.vao = self.asynch_get_vao(vao)

    def rebuild(self):
        self.vao = self.get_vao()

    def get_vertex_data(self):
        neighbors_voxels = get_neighbors(self.chunk.world.voxels,
                                         np.array(self.chunk.r_index),
                                         np.array(self.chunk.index),
                                         self.chunk.info)

        mesh = build_chunk_mesh_greedy(chunk_voxels = self.chunk.voxels,
                                       neighbors = neighbors_voxels,
                                       format_s = self.format_size,
                                       lod = 32)

        return mesh

    def get_vao(self):
        vertex_data = self.get_vertex_data()

        # Build normal vbo and vao
        vbo = self.ctx.buffer(vertex_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        return vao

    def asynch_get_vao(self, vertex_data):

        # Build normal vbo and vao
        vbo = self.ctx.buffer(vertex_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        return vao
