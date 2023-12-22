# Evolution simulation project - GENESIM LAB v0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 17/12/2023
# Notes: Main module to run simulation game

# Import third party and game packages ---------|
from genesim_lab.game.world import *
from genesim_lab.game.settings import *
from genesim_lab.game.events import *
from genesim_lab.game.scene import Scene
from genesim_lab.game.surfaces import *
from genesim_lab.game.shader_program import ShaderProgram
from genesim_lab.game.events import *
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
            self.screen = pg.display.set_mode((0, 0), flags=pg.FULLSCREEN | pg.OPENGL | pg.DOUBLEBUF)
        else:
            self.screen = pg.display.set_mode((self.g_stg['window']['l'], self.g_stg['window']['h']),
                                              flags=pg.OPENGL | pg.DOUBLEBUF)
        self.g_stg['window']['rect'] = self.screen.get_rect()  # Get current rect of main window

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

        # Init custom events and event list and mouse position on screen
        self.mouse = pg.mouse.get_pos()
        self.custom_events = EventHandler(self)
        self.event_list = None

        # Init scene and shader programs
        self.shader_prog_2D = init_shaders_2d(self)
        self.shader_prog_3D = ShaderProgram(self)
        self.scene = Scene(self)

    def update(self):
        # Update 3D shaders 2D shaders and scene
        self.scene.update()

        # Update time, delta_time
        self.delta_time = self.clock.tick(self.g_stg['util']['fps_limit'])
        self.time = pg.time.get_ticks() * 0.001

        # Update mouse position
        self.mouse = pg.mouse.get_pos()

    def render(self):
        # Clear, render and update frame
        self.ctx.clear()
        self.scene.render()
        pg.display.flip()

    def handle_events(self):
        # Get all events each loop
        self.event_list = pg.event.get()

        # Check always functioning events (ALT+F4, ecc)
        self.custom_events.check_events()

    def run(self):
        # Main game loop
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
        pg.quit()
        sys.exit()


# Main ----------------------------------------------|
if __name__ == '__main__':
    app = BoxelEngine()
    app.run()
