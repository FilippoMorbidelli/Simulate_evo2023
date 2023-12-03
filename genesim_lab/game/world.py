# Evolution simulation project - world generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, game start and world generation

# Import packages ------------------------------|
import numpy as np
import numpy.random as rnd

from genesim_lab.game.settings import *
from genesim_lab.game.events import *
from genesim_lab.game.shader_program import ShaderProgram
from genesim_lab.game.scene import Scene
import moderngl as mgl
import pygame as pg
import sys


# Game start -----------------------------------|
class BoxelEngine:  # Voxel engine inspired from Minecraft

    def __init__(self):  # Initialize game
        # Initialize game window
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)  # X. OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)  # .X OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)  #
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)  #

        # Initialize game settings
        self.g_stg = game_settings()

        # Set game window size (default: full screen)
        if self.g_stg['window']['full_screen']:
            pg.display.set_mode((0, 0), flags=pg.FULLSCREEN | pg.OPENGL | pg.DOUBLEBUF)
        else:
            pg.display.set_mode((self.g_stg['window']['l'], self.g_stg['window']['h']),
                                flags=pg.OPENGL | pg.DOUBLEBUF)

        # Call context for ModernGL
        self.ctx = mgl.create_context()
        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        self.ctx.gc_mode = 'auto'  # Garbage collection

        # Keep track of time and delta_time
        self.clock = pg.time.Clock()
        self.delta_time = 0
        self.time = 0

        # Game is running?
        self.is_running = True

        # Init shaders and scene
        self.shader_program = ShaderProgram(self)
        self.scene = Scene(self)

    def update(self):
        # Update shaders and scene
        self.shader_program.update()
        self.scene.update()

        # Update time, delta_time and display fps on the top left part of the screen
        self.delta_time = self.clock.tick()
        self.time = pg.time.get_ticks() * 0.001
        #self.screen.blit(pg.font.SysFont('Verdana', 20).render(
        #    f'{self.clock.get_fps() :.0f}', True, (255, 255, 255)), (0, 0))

    def render(self):
        # Clear, render and update frame
        self.ctx.clear()
        self.scene.render()
        pg.display.flip()

    def handle_events(self):
        # Handle all events
        for event in pg.event.get():
            # Secure "close game" event
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                self.is_running = False
            # Quit game via button
            #self.is_running = mouse_evt(event, pg.MOUSEBUTTONDOWN, 1, False)

    def run(self):
        # Main gamer loop
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
        pg.quit()
        sys.exit()


# World generator ------------------------------|
class SimGrid:
    def __init__(self, settings):
        # Preallocate attributes
        self.masks = type("Terrain masks", (), {})()

        # Preallocate grid
        n = settings['terrain']['shape']
        grid = np.ones(n, dtype=np.int32)

        # Compute noise
        noise = fractal_noise(settings)
        noise = (noise - noise.min()) / (noise.max() - noise.min())

        # Generate water
        threshold = settings['terrain']['water_threshold']
        grid[noise < threshold] = settings['terrain']['water_ID']

        # Generate vegetation
        potential = ((noise - threshold) / (1 - threshold)) ** 4 * 0.7
        mask = (noise > threshold) * (rnd.rand(n[0], n[1]) < potential)
        grid[mask] = settings['terrain']['vegetation_ID']
        self.grid = grid

        # Extract terrain masks
        veg_mask = np.argwhere(mask)
        veg_mask[:, 0] = veg_mask[:, 0] - n[0] / 2  # change y values (on rows)
        veg_mask[:, 0] = - veg_mask[:, 0]
        veg_mask[:, 1] = veg_mask[:, 1] - n[1] / 2  # change x values (on columns)
        self.masks.veg_mask = veg_mask

        grass_mask = np.argwhere(grid == 1)
        grass_mask[:, 0] = grass_mask[:, 0] - n[0] / 2
        grass_mask[:, 0] = - grass_mask[:, 0]
        grass_mask[:, 1] = grass_mask[:, 1] - n[1] / 2
        self.masks.grass_mask = grass_mask

        water_mask = np.argwhere(grid == 0)
        water_mask[:, 0] = water_mask[:, 0] - n[0] / 2
        water_mask[:, 0] = - water_mask[:, 0]
        water_mask[:, 1] = water_mask[:, 1] - n[1] / 2
        self.masks.water_mask = water_mask


# Utility functions----------------------------------
def generate_perlin_noise_2d(shape, res):
    f = lambda tt: 6 * tt ** 5 - 15 * tt ** 4 + 10 * tt ** 3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1

    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)

    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)

    # Interpolation
    t = f(grid)
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)


def fractal_noise(settings):
    # Get grid settings
    shape = settings['terrain']['shape']
    res = settings['terrain']['resolution']
    octaves = settings['terrain']['octaves']
    persistence = settings['terrain']['persistence']

    # Compute fractal noise
    noise = np.zeros(shape)
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        noise += amplitude * generate_perlin_noise_2d(shape, (frequency * res[0], frequency * res[1]))
        frequency *= 2
        amplitude *= persistence
    return noise
