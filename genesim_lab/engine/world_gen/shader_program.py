# Evolution simulation project - shader_program module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes:

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


# Main -----------------------------------------|
class ShaderProgram:

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.player = app.player
        # ------ Shaders ------ #
        self.chunk = self.get_program(shader_name='chunk')
        self.instanced_chunks = self.get_program(shader_name='instanced_chunks')
        self.voxel_marker = self.get_program(shader_name='voxel_marker')
        self.celestials = self.get_program(shader_name='celestial')
        self.skybox = self.get_program(shader_name='skybox')
        # --------------------- #
        self.set_uniforms_on_init()

    def set_uniforms_on_init(self):
        # Chunks
        self.chunk['m_proj'].write(self.player.m_proj)
        self.chunk['m_model'].write(glm.mat4())
        self.chunk['u_texture_array_0'] = 2
        self.chunk['scale'].write(self.app.stg.world.scale)

        # Instanced Chunks
        self.instanced_chunks['m_proj'].write(self.player.m_proj)
        self.instanced_chunks['u_texture_array_0'] = 2
        self.instanced_chunks['scale'].write(self.app.stg.world.scale)

        # Marker
        self.voxel_marker['m_proj'].write(self.player.m_proj)
        self.voxel_marker['m_model'].write(glm.mat4())
        self.voxel_marker['u_texture_0'] = 1
        self.voxel_marker['scale'].write(self.app.stg.world.scale)

        # Celestial bodies
        self.celestials['m_proj'].write(self.player.m_proj)
        self.celestials['m_model'].write(glm.mat4())
        self.celestials['u_texture_array_sky'] = 3

        # Skybox
        self.skybox['u_texture_cubemap_skybox'] = 4

    def update(self, *args):
        # Chunks
        self.chunk['m_view'].write(self.player.m_view)
        # Instanced chunks
        self.instanced_chunks['m_view'].write(self.player.m_view)
        # Marker
        self.voxel_marker['m_view'].write(self.player.m_view)
        # Celestial bodies
        self.celestials['m_view'].write(self.player.m_view)
        # Skybox
        m_view = glm.mat4(glm.mat3(self.player.m_view))
        self.skybox['m_invProjView'].write(glm.inverse(self.player.m_proj * m_view))

    def get_program(self, shader_name):
        with open(f'genesim_lab/shaders/{shader_name}.vert') as file:
            vertex_shader = file.read()

        with open(f'genesim_lab/shaders/{shader_name}.frag') as file:
            fragment_shader = file.read()

        program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        return program
