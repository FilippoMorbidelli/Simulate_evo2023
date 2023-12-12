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
class AllMenu:

    def __init__(self, app):
        self.app = app

        # Init utility vision --> fps counter, version info
        fps_counter = FpsSprite(app)
        self.app.shader_program_2D.add(fps_counter)
        # Init main menu

    def init_shader(self):
        # Init all shader groups
        #shader_program_2D = GLTextures2D(app)
        pass
        #return shader_program_2D


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
        return self.gl_textures[image]

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
        self.get_texture(sprite.image).use(0)
        self.get_vao().render()

    def draw2d(self):
        for sprite in self:
            self.render(sprite, self.app.screen)

    def update(self, app):
        for sprite in self:
            sprite.update(app)


class StaticSprite(pg.sprite.Sprite):
    def __init__(self, app, image, dest=(0, 0)):
        super().__init__()
        try:
            self.image = pg.image.load(f'{image}.png').convert_alpha()
        except:
            self.image = pg.Surface((1920, 1080), pg.SRCALPHA)
            self.image.blit(image, dest)
            self.dest = dest
        self.rect = self.image.get_rect(center=app.screen.get_rect().center)


class FpsSprite(pg.sprite.Sprite):
    def __init__(self, app):
        super().__init__()
        self.image = pg.Surface((1920, 1080), pg.SRCALPHA)
        self.image.blit(pg.font.SysFont('Verdana', 20).render(f'{app.clock.get_fps() :.0f}',
                                                              True, (255, 255, 255)), (0, 0))
        self.rect = self.image.get_rect(center=app.screen.get_rect().center)

    def update(self, app):
        for event in pg.event.get():
            if event.type == app.FPS_EVENT_ID:
                self.image = pg.Surface((1920, 1080), pg.SRCALPHA)
                self.image.blit(pg.font.SysFont('Verdana', 20).render(f'{app.clock.get_fps() :.0f}',
                                                                      True, (255, 255, 255)), (0, 0))
            else:
                pass
