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
        self.vbo_format = None  # Vbo format reserved to vertex data
        # Attribute names according to the format: ("in_position", "in_color")
        self.attrs: tuple[str, ...] = ()  # Attributes reserved to vertex data
        # Vertex array object
        self.vao = None

    def get_vertex_data(self) -> np.array: ...

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
        return vao

    def render(self):
        self.vao.render()
