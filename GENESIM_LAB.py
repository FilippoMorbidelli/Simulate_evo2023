# Evolution simulation project - GENESIM LAB v0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 02/12/2023
# Notes: Main module to run simulation game

# Import third party and game packages --------------|
from genesim_lab.game.world import *

from genesim_lab.game.settings import *
from genesim_lab.game.events import *
from genesim_lab.game.shader_program import ShaderProgram
from genesim_lab.game.scene import Scene
from genesim_lab.game.menu import GLTextures2D
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
        self.shader_program_2D = GLTextures2D(self)
        self.scene = Scene(self)

        # FPS event to update it every second only
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)

        # Instance event_list
        self.event_list = None

    def update(self):
        # Update 3D shaders 2D shaders and scene
        self.shader_program.update()
        self.shader_program_2D.update(app)
        self.scene.update()

        # Update time, delta_time and display fps on the top left part of the screen
        self.delta_time = self.clock.tick(144)
        self.time = pg.time.get_ticks() * 0.001
        #self.screen.blit(pg.font.SysFont('Verdana', 20).render(
        #    f'{self.clock.get_fps() :.0f}', True, (255, 255, 255)), (0, 0))

    def render(self):
        # Clear, render and update frame
        self.ctx.clear()
        self.scene.render()
        pg.display.flip()

    def handle_events(self):
        # Get all events
        self.event_list = pg.event.get()
        # Handle all events
        for event in self.event_list:
            # Secure "close game" event
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                self.is_running = False
            # Quit game via button
            #self.is_running = mouse_evt(event, pg.MOUSEBUTTONDOWN, 1, False)

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
