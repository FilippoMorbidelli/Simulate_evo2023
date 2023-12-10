# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
import pygame as pg
import ctypes
import moderngl as mgl
from genesim_lab.game.settings import *


# Main menu ------------------------------------|
class MainMenu:

    def __init__(self):
        pass


# 2D texture function --------------------------|
class GLTextures2D(pg.sprite.Group):

    def __init__(self, app, sprites=None):
        if sprites is None:
            super().__init__()
        else:
            super().__init__(sprites)
        self.app = app
        self.gl_context = app.ctx
        self.gl_program = None
        self.gl_buffer = None
        self.gl_vao = None
        self.gl_textures = {}

    def get_program(self):
        if self.gl_program is None:
            with open(f'genesim_lab/shaders/2D_sprite.vert') as file:
                vertex_shader_sprite = file.read()

            with open(f'genesim_lab/shaders/2D_sprite.frag') as file:
                fragment_shader_sprite = file.read()

            self.gl_program = self.gl_context.program(vertex_shader=vertex_shader_sprite,
                                                      fragment_shader=fragment_shader_sprite)
        return self.gl_program

    def get_buffer(self):
        if self.gl_buffer is None:
            self.gl_buffer = self.gl_context.buffer(None, reserve=6 * 4 * 4)
        return self.gl_buffer

    def get_vao(self):
        if self.gl_vao is None:
            self.gl_vao = self.gl_context.vertex_array(self.get_program(),
                                                       [(self.get_buffer(), "2f4 2f4", "in_position", "in_uv")])
        return self.gl_vao

    def get_texture(self, image):
        if image not in self.gl_textures:
            rgba_image = image.convert_alpha()
            texture = self.gl_context.texture(rgba_image.get_size(), 4, rgba_image.get_buffer())
            texture.swizzle = 'BGRA'
            self.gl_textures[image] = texture

    def convert_vertex(self, pt, surface):
        return pt[0] / surface.get_width() * 2 - 1, 1 - pt[1] / surface.get_height() * 2

    def render(self, sprite, surface):
        corners = [
            self.convert_vertex(sprite.rect.bottomleft, surface),
            self.convert_vertex(sprite.rect.bottomright, surface),
            self.convert_vertex(sprite.rect.topright, surface),
            self.convert_vertex(sprite.rect.topleft, surface)]
        vertices_quad_2d = (ctypes.c_float * (6 * 4))(
            *corners[0], 0.0, 1.0,
            *corners[1], 1.0, 1.0,
            *corners[2], 1.0, 0.0,
            *corners[0], 0.0, 1.0,
            *corners[2], 1.0, 0.0,
            *corners[3], 0.0, 0.0)

        self.get_buffer().write(vertices_quad_2d)
        self.get_texture(sprite.image)
        self.get_vao().render()

    def draw2d(self):
        for sprite in self:
            self.render(sprite, self.app.screen)


class StaticSprite(pg.sprite.Sprite):
    def __init__(self, app, image, dest=(0, 0)):
        super().__init__()
        try:
            self.image = pg.image.load(f'{image}.png').convert_alpha()
        except:
            #self.image = pg.Surface((1920, 1080), pg.SRCALPHA)
            #self.image.blit(image, dest)
            self.image = pg.Surface((100, 100), pg.SRCALPHA)
            pg.draw.circle(self.image, (255, 255, 0), (50, 50), 50)
        self.rect = self.image.get_rect(center=app.screen.get_rect().center)
