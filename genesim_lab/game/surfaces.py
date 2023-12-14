# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
import pygame as pg
import moderngl as mgl
from genesim_lab.game.settings import *
from genesim_lab.game.sprite import *


# All surfaces ---------------------------------|
class Surfaces:

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

    def get_current_surf(self):
        pass
