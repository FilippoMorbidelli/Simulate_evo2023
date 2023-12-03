# Evolution simulation project - shader_program module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes:

# Import packages ------------------------------|
from genesim_lab.game.settings import *


# Main -----------------------------------------|
class ShaderProgram:

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        # ------ Shaders ------ #
        self.quad = self.get_program(shader_name='quad')
        # --------------------- #
        self.set_uniforms_on_init()

    def set_uniforms_on_init(self):
        pass

    def update(self):
        pass

    def get_program(self, shader_name):
        with open(f'genesim_lab/shaders/{shader_name}.vert') as file:
            vertex_shader = file.read()

        with open(f'genesim_lab/shaders/{shader_name}.frag') as file:
            fragment_shader = file.read()

        program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        return program
