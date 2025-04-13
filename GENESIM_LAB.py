# Evolution simulation project - GENESIM LAB v0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 17/12/2023
# Notes: Main module to run simulation Engine

# Import third party and Engine packages ---------|
from genesim_lab.Engine.scene.surfaces import Scene, init_shaders_2d
from genesim_lab.Engine.world_gen.shader_program import ShaderProgram
from genesim_lab.Engine.scene.events import *
from genesim_lab.Engine.player.player import Player
from genesim_lab.Processes.Process import LoadProcess, SaveProcess
from genesim_lab.Engine.world_gen.textures import Textures
from genesim_lab.Engine.sl_manager.SaveManager import SaveManager
from genesim_lab.Engine.settings import GameSettings
from multiprocessing import Queue

import moderngl as mgl
import pygame as pg
import sys

import cProfile
import pstats
import io
import gc
import tracemalloc


# Game start -----------------------------------|
class BoxelEngine:  # Voxel Engine inspired from Minecraft

    def __init__(self):  # Initialize Engine
        # Initialize Engine window
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)  # X. OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)  # .X OpenGL version
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)  #
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)  #

        # Multiprocessing Manager and Engine settings
        self.stg = GameSettings()

        # Set Engine window size (default: full screen)
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
        self.cycle = 0

        # Keep track of mouse position and lock it inside screen, change cursor to custom one
        cursor = pg.image.load(f'genesim_lab/assets/other/cursor.svg').convert_alpha()
        cursor = pg.transform.scale(cursor, (48, 48))
        cursor = pg.cursors.Cursor((0, 0), cursor)
        pg.mouse.set_cursor(cursor)
        pg.event.set_grab(True)
        self.mouse_visible = True
        self.mouse = pg.mouse.get_pos()

        # Game is running?
        self.is_running = True

        # Init player control (during main Engine as master only)
        self.player = Player(self, position=self.stg.player.pos)

        # Init Save/Load Manager
        self.save_load = SaveManager(self)

        # Init scene and shader programs
        self.textures = Textures(self)
        self.shader_prog_2D = init_shaders_2d(self)
        self.shader_prog_3D = ShaderProgram(self)
        self.scene = Scene(self)

        # Init custom events and event list
        self.custom_events = EventHandler(self)
        self.event_list = None

        # Create Child Processes and Queues
        self.processes  = dict()
        self.req_queues = dict()
        self.resp_queue = Queue() # The response queue is unique since all processes communicate with parent only

        # Load region process
        self.req_queues["load"] = Queue()
        self.processes["load"] = LoadProcess(self.req_queues["load"], self.resp_queue)
        self.processes["load"].start()

        # Save region process
        self.req_queues["save"] = Queue()
        self.processes["save"] = SaveProcess(self.req_queues["save"], self.resp_queue)
        self.processes["save"].start()

    def update(self):
        # Update time, delta_time and cycle
        self.delta_time = self.clock.tick(self.stg.util.fps_limit)
        self.time = pg.time.get_ticks() * 0.001
        self.cycle = (self.cycle + 1) % 32

        # Update mouse position
        self.mouse = pg.mouse.get_pos()

        # Update 3D Shaders, 2D Shaders and scene
        self.scene.update_current_scene()

    def render(self):
        # Clear, render and update frame
        self.ctx.clear()
        self.scene.render_current_scene()
        pg.display.flip()

    def handle_events(self):
        # Get all events each loop
        self.event_list = pg.event.get()

        # Check always functioning events (ALT+F4, ecc)
        self.custom_events.handle_events()

    def gc_collection(self):
        # Collect garbage every 2 seconds
        if not self.cycle:
            #gc.collect()
            pass

    def run(self):
        # Main Engine loop
        while self.is_running:
            self.handle_events()  # Handle event checks and computations
            self.update()         # Perform attributes, variables and state updates
            self.render()         # Perform render of current scene once every update has been done
            self.gc_collection()  # Perform garbage collection

        # Shutdown any running process
        for process in self.processes.values():
            process.terminate()

        # Shutdown Pygame and System
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

    with open('profiling/stats_02_03_025.txt', 'w+') as f:
        f.write(s.getvalue())


# Main ----------------------------------------------|
if __name__ == '__main__':
    app = BoxelEngine()
    app.run()
    #profiling()
