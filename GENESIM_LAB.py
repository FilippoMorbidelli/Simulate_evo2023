# Evolution simulation project - GENESIM LAB v0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 17/12/2023
# Notes: Main module to run simulation engine

# Import third party and engine packages ---------|
from genesim_lab.engine.scene.scene import Scene
from genesim_lab.engine.scene.surfaces import *
from genesim_lab.engine.world_gen.shader_program import ShaderProgram
from genesim_lab.engine.scene.events import *
from genesim_lab.engine.player.player import Player
from genesim_lab.engine.settings import *
from genesim_lab.engine.world_gen.textures import Textures
import moderngl as mgl
import pygame as pg
import sys

import cProfile
import pstats
import io


# Game start -----------------------------------|
class BoxelEngine:  # Voxel engine inspired from Minecraft

    def __init__(self):  # Initialize engine
        # Initialize engine window
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)  # X. OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)  # .X OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)  #
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)  #

        # Initialize engine settings
        self.stg = stg

        # Set engine window size (default: full screen)
        if self.stg.window.full_screen:
            self.screen = pg.display.set_mode((0, 0), flags=pg.FULLSCREEN | pg.OPENGL | pg.DOUBLEBUF)
        else:
            self.screen = pg.display.set_mode((self.stg.window.l, self.stg.window.h),
                                              flags=pg.OPENGL | pg.DOUBLEBUF)
        self.stg.window.rect = self.screen.get_rect()  # Get current rect of main window

        # Call contexts for ModernGL
        self.ctx = mgl.create_context()
        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        self.ctx.gc_mode = 'auto'  # Garbage collection

        # Keep track of time and delta_time
        self.clock = pg.time.Clock()
        self.delta_time = 0
        self.time = 0

        # Keep track of mouse positionand lock it inside screen, change curson to custom one
        cursor = pg.image.load(f'genesim_lab/assets/other/cursor.svg').convert_alpha()
        cursor = pg.transform.scale(cursor, (48, 48))
        cursor = pg.cursors.Cursor((0, 0), cursor)
        pg.mouse.set_cursor(cursor)
        self.mouse = pg.mouse.get_pos()
        pg.event.set_grab(True)
        self.mouse_visible = True

        # Game is running?
        self.is_running = True

        # Init player control (during main engine as master only)
        self.player = Player(self)

        # Init scene and shader programs
        self.textures = Textures(self)
        self.shader_prog_2D = init_shaders_2d(self)
        self.shader_prog_3D = ShaderProgram(self)
        self.scene = Scene(self)

        # Init custom events and event list
        self.custom_events = EventHandler(self)
        self.event_list = None

    def update(self):
        # Update time, delta_time
        self.delta_time = self.clock.tick(self.stg.util.fps_limit)
        self.time = pg.time.get_ticks() * 0.001

        # Update mouse position
        self.mouse = pg.mouse.get_pos()

        # Update 3D shaders 2D shaders and scene
        self.scene.update()

    def render(self):
        # Clear, render and update frame
        self.ctx.clear()
        self.scene.render()
        pg.display.flip()

    def handle_events(self):
        # Get all events each loop
        self.event_list = pg.event.get()

        # Check always functioning events (ALT+F4, ecc)
        self.custom_events.handle_events(self)

    def run(self):
        # Main engine loop
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
        pg.quit()
        sys.exit()  # Comment during profiling


def profiling():
    pr = cProfile.Profile()
    pr.enable()
    app.run()
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats()

    with open('profiling/stats_27122023_1.txt', 'w+') as f:
        f.write(s.getvalue())


# Main ----------------------------------------------|
if __name__ == '__main__':
    app = BoxelEngine()
    app.run()
    # profiling()
