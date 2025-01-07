# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.meshes.base_mesh import BaseMesh
from genesim_lab.meshes.chunk_mesh_builder import build_chunk_mesh
import numpy as np


# Import packages ------------------------------|
class ChunkMesh(BaseMesh):

    def __init__(self, chunk):
        super().__init__()
        self.app = chunk.app
        self.chunk = chunk
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.chunk
        self.program_oc = self.app.shader_prog_3D.chunk_oc

        self.vbo_format = '1u4'  # All data passed as uint8
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data',)
        self.vao, self.vao_oc = self.get_vao()

    def rebuild(self):
        self.vao, self.vao_oc = self.get_vao()

    def get_vertex_data(self):
        mesh, greedy_mesh = build_chunk_mesh(
            chunk_voxels=self.chunk.voxels,
            format_size=self.format_size,
            chunk_pos=self.chunk.index,
            world_voxels=self.chunk.world.voxels,
        )

        return mesh

    def get_vao(self):
        vertex_data = self.get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        bb_vert = [
            (0, 0, 32), (32, 0, 32), (32, 32, 32), (0, 32, 32),
            (0, 32, 0), (0, 0, 0), (32, 0, 0), (32, 32, 0)
        ]
        bb_ind = [
            (0, 2, 3), (0, 1, 2),
            (1, 7, 2), (1, 6, 7),
            (6, 5, 4), (4, 7, 6),
            (3, 4, 5), (3, 5, 0),
            (3, 7, 4), (3, 2, 7),
            (0, 6, 1), (0, 5, 6),
        ]
        vbo_bounding_box = np.array([bb_vert[ind] for triangle in bb_ind for ind in triangle], dtype='uint16').flatten()

        vao_oc = self.ctx.vertex_array(
            self.program_oc,
            [
                (self.ctx.buffer(vbo_bounding_box), '3u2', *('in_position',)),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )

        return vao, vao_oc

    def render_oc(self):
        self.vao_oc.render()
