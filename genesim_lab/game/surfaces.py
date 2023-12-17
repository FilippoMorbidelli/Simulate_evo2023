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
from operator import methodcaller as mc


# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        # Initialize flags for each scene
        self.flags = {"Main_menu": True,
                      "Utility": True,
                      "Main_game": False
                      }  # Dictionary containing the scene flags

        self.surf = self.init_surfaces()
        self.active = None
        # Init utility vision --> fps counter, version info
        # Init main menu

    def init_surfaces(self):
        surf_group = type("Contains each single surface", (), {})()

        # Initialize each surface alone
        surf_group.utility = UtilityMenu(self.app)

        return surf_group

    def update_current_scene(self):
        self.active = [surf for surf, status in self.flags.items() if status is True]
        for act_surf in self.active:
            self.app.shader_prog_2D.utility.update(self.app)

    def render_current_scene(self):
        # Render always active elements
        self.app.shader_prog_2D.utility.draw2d()


class MainMenu:

    def __init__(self):
        pass

    def update(self):
        pass


class UtilityMenu:

    def __init__(self, app):
        fps_counter = FpsSprite(app)
        util_text = UtilityStaticText(app, 'Genesim Lab - version alpha\nAuthor: F. Morbidelli\nTrial version',
                                      pg.Rect(1620, 0, 300, 100), "right")
        app.shader_prog_2D.utility.add(fps_counter)
        app.shader_prog_2D.utility.add(util_text)

    def update(self):
        pass


class PauseMenu:

    def __init__(self):
        pass

    def update(self):
        pass


def init_shaders(app):
    # Creates shaders programs organized in subgroups relative to the different scenes
    programs = type("Contains all subgroup related to same shader program", (), {})()
    programs.main_menu = GLTextures2D(app)
    programs.utility = GLTextures2D(app)

    return programs
