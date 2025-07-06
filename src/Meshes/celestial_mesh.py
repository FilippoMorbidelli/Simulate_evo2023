# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the Engine, Engine start and world_objects generation

# Import packages ------------------------------|
from src.Engine.settings import *
from src.Meshes.base_mesh import BaseMesh


# Import packages ------------------------------|
class SkyObjMesh(BaseMesh):

    def __init__(self, app, b_id):
        super().__init__()
        self.app = app
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.celestials
        self.body_id = b_id

        self.vbo_format = '2f2 3f2'
        self.attrs = ('in_tex_coord_0', 'in_position')
        self.vao = self.get_vao()

    @staticmethod
    def get_data(vertices, indices):
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='float16')

    @staticmethod
    def get_data_int16(vertices, indices):
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='int16')

    def get_vertex_data(self):
        vertices = [
            (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
            (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5)
        ]
        indices = [
            (0, 2, 3), (0, 1, 2),  # Front face
            (1, 7, 2), (1, 6, 7),  # Right face
            (6, 5, 4), (4, 7, 6),  # Back face
            (3, 4, 5), (3, 5, 0),  # Left face
            (3, 7, 4), (3, 2, 7),  # Top face
            (0, 6, 1), (0, 5, 6),  # Bottom face
        ]
        vertex_data = self.get_data(vertices, indices)

        tex_coord_vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
        tex_coord_indices = [
            (0, 2, 3), (0, 1, 2),
            (0, 2, 3), (0, 1, 2),
            (0, 1, 2), (2, 3, 0),
            (2, 3, 0), (2, 0, 1),
            (0, 2, 3), (0, 1, 2),
            (3, 1, 2), (3, 0, 1),
        ]
        tex_coord_data = self.get_data(tex_coord_vertices, tex_coord_indices)

        face_id = [(0,), (1,), (2,), (3,), (4,), (5,)]
        face_id_indices = [
            (4, 4, 4), (4, 4, 4),  # Front face
            (2, 2, 2), (2, 2, 2),  # Right face
            (5, 5, 5), (5, 5, 5),  # Back face
            (3, 3, 3), (3, 3, 3),  # Left face
            (0, 0, 0), (0, 0, 0),  # Top face
            (1, 1, 1), (1, 1, 1)   # Bottom face
        ]
        face_id_data = self.get_data_int16(face_id, face_id_indices)

        vertex_data = np.hstack([tex_coord_data, vertex_data])
        body_data = np.hstack([face_id_data, np.full((36, 1), self.body_id, dtype='int16')])
        return vertex_data, body_data

    def get_vao(self):
        vertex_data, body_data = self.get_vertex_data()
        vbo_vertex = self.ctx.buffer(vertex_data)
        vbo_obj = self.ctx.buffer(body_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo_vertex, self.vbo_format, *self.attrs),  # First vbo, dedicated to vertex
                (vbo_obj, '1i2 1i2', *('in_face_id', 'in_body_id',)),  # First vbo, dedicated to vertex
            ],
            skip_errors=True
        )
        return vao


class SkyBoxMesh(BaseMesh):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ctx = self.app.ctx
        self.program = self.app.shader_prog_3D.skybox

        self.vbo_format = '3f4'
        self.attrs = ('in_position',)
        self.vao = self.get_vao()

    @staticmethod
    def get_data(vertices, indices):
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='float32')

    def get_vertex_data(self):
        # in clip space
        z = 0.99999
        vertices = [(-1, -1, z), (1, 1, z), (-1, 1, z),
                    (-1, -1, z), (1, -1, z), (1, 1, z)]
        vertex_data = np.array(vertices, dtype='float32')
        #vertices = [
        #    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
        #    (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1)
        #]
        #indices = [
        #    (0, 2, 3), (0, 1, 2),  # Front face
        #    (1, 7, 2), (1, 6, 7),  # Right face
        #    (6, 5, 4), (4, 7, 6),  # Back face
        #    (3, 4, 5), (3, 5, 0),  # Left face
        #    (3, 7, 4), (3, 2, 7),  # Top face
        #    (0, 6, 1), (0, 5, 6),  # Bottom face
        #]
        #vertex_data = self.get_data(vertices, indices)
        #vertex_data = np.flip(vertex_data, 1).copy(order='C')

        return vertex_data
