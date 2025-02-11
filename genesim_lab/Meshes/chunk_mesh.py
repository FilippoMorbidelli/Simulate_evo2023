# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.Meshes.base_mesh import BaseMesh
from genesim_lab.Meshes.chunk_mesh_builder import build_chunk_mesh
import numpy as np


# Import packages ------------------------------|
class ChunkMesh(BaseMesh):

    def __init__(self, chunk, threaded=False):
        super().__init__()
        self.app = chunk.app
        self.chunk = chunk
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.chunk
        self.program_greedy = self.app.shader_prog_3D.chunk_greedy

        self.vbo_format = '1u4'  # All data passed as uint8
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data',)

        # Thread safe temporary variables
        self.vertex_tmp = None
        self.greedy_tmp = None

        self.vao = None
        self.vao_greedy = None

        if not threaded:
            self.vao, self.vao_greedy = self.get_vao()
        else:
            self.get_vertex_thread_safe()

    def rebuild(self):
        self.vao, self.vao_greedy = self.get_vao()

    def get_vertex_data(self):
        mesh, greedy_mesh = build_chunk_mesh(
            chunk_voxels = self.chunk.voxels,
            format_size  = self.format_size,
            chunk_pos    = self.chunk.index,
            world_voxels = self.chunk.world.voxels,
            region_pos   = self.chunk.r_index,
            stg          = self.chunk.mesh_stg,
        )

        return mesh, greedy_mesh

    def get_vao(self):
        vertex_data, greedy_data = self.get_vertex_data()

        # Build normal vbo and vao
        vbo = self.ctx.buffer(vertex_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        # Build greedy vbo and vao
        vbo_greedy = self.ctx.buffer(greedy_data)
        vao_greedy = self.ctx.vertex_array(
            self.program_greedy,
            [
                (vbo_greedy, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        return vao, vao_greedy

    def render_greedy(self):
        self.vao_greedy.render()

    def get_vertex_thread_safe(self):
        self.vertex_tmp, self.greedy_tmp = self.get_vertex_data()

    def get_vao_thread_save(self):
        # Build normal vbo and vao
        vbo = self.ctx.buffer(self.vertex_tmp)
        self.vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        self.vertex_tmp = None

        # Build greedy vbo and vao
        vbo_greedy = self.ctx.buffer(self.greedy_tmp)
        self.vao_greedy = self.ctx.vertex_array(
            self.program_greedy,
            [
                (vbo_greedy, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        self.greedy_tmp = None

