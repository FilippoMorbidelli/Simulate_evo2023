# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
import pygame as pg
import moderngl as mgl
from genesim_lab.game.settings import *
from genesim_lab.meshes.quad_mesh import QuadMesh
from genesim_lab.game.sprite import *


# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        self.flags = type("Current scene logic", (), {})()
        # Initialize flags for each scene
        self.flags.Main_menu = True
        self.flags.utility = True

        # Init utility vision --> fps counter, version info
        # Init main menu

    @staticmethod
    def init_shaders(app):
        programs = type("Contains all subgroup related to same shader program", (), {})()
        programs.main_menu = GLTextures2D(app)
        programs.utility = GLTextures2D(app)
        return programs

    def update_current_scene(self):
        pass


class MainMenu:

    def __init__(self):
        pass

    def update(self):
        pass


class UtilityMenu:

    def __init__(self, app):
        pass

    def update(self):
        pass


class PauseMenu:

    def __init__(self):
        pass

    def update(self):
        pass
