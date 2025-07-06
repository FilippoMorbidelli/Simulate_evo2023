# Evolution simulation project - quad_mesh module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes:

# Import packages ------------------------------|
from src.Engine.settings import *
from src.Meshes.base_mesh import BaseMesh


# Main -----------------------------------------|
class QuadMesh(BaseMesh):

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_prog_3D.quad

        self.vbo_format = '3f 3f'
        self.attrs = ('in_position', 'in_color')
        self.vao = self.get_vao()

    def get_vertex_data(self):
        vertices = [(0.5, 0.5, 0.0), (-0.5, 0.5, 0.0), (-0.5, -0.5, 0.0),
                    (0.5, 0.5, 0.0), (-0.5, -0.5, 0.0), (0.5, -0.5, 0.0)]
        colors = [(0, 1, 0), (1, 0, 0), (1, 1, 0),
                  (0, 1, 0), (1, 1, 0), (0, 0, 1)]
        vertex_data = np.hstack([vertices, colors], dtype='float32')
        return vertex_data
