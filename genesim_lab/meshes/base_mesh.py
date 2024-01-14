# Evolution simulation project - shader_program module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes:

# Import packages ------------------------------|
import numpy as np


# Main -----------------------------------------|
class BaseMesh:
    def __init__(self):
        # OpenGL context
        self.ctx = None
        # Shader program
        self.program = None
        # Vertex buffer data type format: "3f2" - "1u1 1u1"
        self.vbo_format_vert = None  # Vbo format reserved to vertex data
        self.vbo_format_extra = None  # Vbo format reserved to extra data [color, id, ecc]
        # Attribute names according to the format: ("in_position", "in_color")
        self.attrs_vert: tuple[str, ...] = ()  # Attributes reserved to vertex data
        self.attrs_extra: tuple[str, ...] = ()  # Attributes reserved to extra data
        # Vertex array object
        self.vao = None

    def get_vertex_data(self) -> np.array: ...

    def get_vao(self):
        vertex_data, extra_data = self.get_vertex_data()
        vbo_vert = self.ctx.buffer(vertex_data)
        vbo_extra = self.ctx.buffer(extra_data)
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo_vert, self.vbo_format_vert, *self.attrs_vert),  # First vbo, dedicated to vertex
                (vbo_extra, self.vbo_format_extra, *self.attrs_extra)  # Second vbo, dedicated to Voxel_ID, Face_ID
            ],
            skip_errors=True
        )
        return vao

    def render(self):
        self.vao.render()
