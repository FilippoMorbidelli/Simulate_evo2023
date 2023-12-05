# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
import pygame as pg
import moderngl as mgl
from settings import *


# Main menu ------------------------------------|
class MainMenu:

    def __init__(self):
        pass


# 2D texture function --------------------------|
class GLTextures2D(pg.sprite.Group):

    def __init__(self, sprites=None):
        if sprites is None:
            super().__init__()
        else:
            super().__init__(sprites)
        self.gl_context = None
        self.gl_program = None
        self.gl_buffer = None
        self.gl_vao = None
        self.gl_textures = {}

    def get_program(self, program):
        if self.gl_program is None:
            self.gl_program = self.gl_context.program(
                vertex_shader= vertex_shader_sprite,
                fragment_shader= fragment_shader_sprite)
        return ModernGLGroup.gl_program

    def get_buffer(self):
        if ModernGLGroup.gl_buffer == None:
            ModernGLGroup.gl_buffer = ModernGLGroup.gl_context.buffer(None, reserve=6 * 4 * 4)
        return ModernGLGroup.gl_buffer

    def get_vao(self):
        if ModernGLGroup.gl_vao == None:
            ModernGLGroup.gl_vao = ModernGLGroup.gl_context.vertex_array(
                ModernGLGroup.get_program(), [(ModernGLGroup.get_buffer(), "2f4 2f4", "in_position", "in_uv")])
        return ModernGLGroup.gl_vao

    def get_texture(self, image):
        if not image in ModernGLGroup.gl_textures:
            rgba_image = image.convert_alpha()
            texture = ModernGLGroup.gl_context.texture(rgba_image.get_size(), 4, rgba_image.get_buffer())
            texture.swizzle = 'BGRA'
            ModernGLGroup.gl_textures[image] = texture
        return ModernGLGroup.gl_textures[image]

    def convert_vertex(self, pt, surface):
        return pt[0] / surface.get_width() * 2 - 1, 1 - pt[1] / surface.get_height() * 2

    def render(self, sprite, surface):
        corners = [
            ModernGLGroup.convert_vertex(sprite.rect.bottomleft, surface),
            ModernGLGroup.convert_vertex(sprite.rect.bottomright, surface),
            ModernGLGroup.convert_vertex(sprite.rect.topright, surface),
            ModernGLGroup.convert_vertex(sprite.rect.topleft, surface)]
        vertices_quad_2d = (ctypes.c_float * (6 * 4))(
            *corners[0], 0.0, 1.0,
            *corners[1], 1.0, 1.0,
            *corners[2], 1.0, 0.0,
            *corners[0], 0.0, 1.0,
            *corners[2], 1.0, 0.0,
            *corners[3], 0.0, 0.0)

        ModernGLGroup.get_buffer().write(vertices_quad_2d)
        ModernGLGroup.get_texture(sprite.image).use(0)
        ModernGLGroup.get_vao().render()

    def draw(self, surface):
        for sprite in self:
            ModernGLGroup.render(sprite, surface)
class Textures2D:

    def __init__(self):
        self.all_GL_textures = None  # Initialize GL textures module
        self.all_GL_textures.main_menu = None  # Initialize module for main menu textures

    def surf_txtr(self, image, group):  # Image converter from pygame surf/blit to OpenGL
        if image not in self.all_GL_textures:
            rgba_image = image.convert_alpha()
            texture = ModernGLGroup.gl_context.texture(rgba_image.get_size(), 4, rgba_image.get_buffer())
            texture.swizzle = 'BGRA'
            ModernGLGroup.gl_textures[image] = texture
        return ModernGLGroup.gl_textures[image]
