# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.meshes.quad_mesh import QuadMesh
from genesim_lab.game.sprite import *


# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        self.surf = self.init_surfaces()
        self.active = None

        # Initialize flags and update/render for each scene
        self.flags = {  # Dictionary containing the scene flags
            "Main_menu": False,
            "Utility": True,
            "Main_game": True
        }
        self.update = {
            "Main_menu": self.app.shader_prog_2D.utility.update,
            "Utility": self.app.shader_prog_2D.utility.update,
            "Main_game": self.app.shader_prog_3D.update
        }
        self.render = {
            "Main_menu": self.app.shader_prog_2D.utility.draw2d,
            "Utility": self.app.shader_prog_2D.utility.draw2d,
            "Main_game": self.surf.main_game.quad.render
        }

        # Init utility vision --> fps counter, version info
        # Init main menu

    def init_surfaces(self):
        surf_group = type("Contains each single surface", (), {})()

        # Initialize each surface alone
        surf_group.utility = UtilityMenu(self.app)
        surf_group.main_game = MainGame(self.app)

        return surf_group

    def update_current_scene(self):
        self.active = [surf for surf, status in self.flags.items() if status is True]
        for act_surf in self.active:
            self.update[act_surf](self.app)

    def render_current_scene(self):
        # Render always active elements
        for act_surf in self.active:
            self.render[act_surf]()


class MainMenu:

    def __init__(self):
        pass


class UtilityMenu:

    def __init__(self, app):
        fps_counter = FpsSprite(app)
        util_text = UtilityStaticText(app, 'Genesim Lab - version alpha\nAuthor: F. Morbidelli\nTrial version',
                                      pg.Rect(1620, 0, 300, 100), "right")
        app.shader_prog_2D.utility.add(fps_counter)
        app.shader_prog_2D.utility.add(util_text)


class PauseMenu:

    def __init__(self):
        pass


class MainGame:

    def __init__(self, app):
        # Initialize quadrilateral
        self.quad = QuadMesh(app)


def init_shaders_2d(app):
    # Creates shaders programs organized in subgroups relative to the different scenes
    programs = type("Contains all subgroup related to same shader program", (), {})()
    programs.main_menu = GLTextures2D(app)
    programs.utility = GLTextures2D(app)

    return programs
