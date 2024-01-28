# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.engine.world_gen.world import World
from genesim_lab.engine.world_objects.voxel_marker import VoxelMarker
from genesim_lab.engine.scene.sprite import *


# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        self.surf = self.init_surfaces()
        self.active = None

        # Init flags, handle, update and render for each scene
        self.flags = {  # Dictionary containing the scene status flags
            # Surface: render --> [True, False]
            #          level  --> [1, 2, 3, ..., None]
            #          update --> [Update, Frozen, None]
            "main_menu": [True, 1, "Update"],
            "utility": [False, None, None],
            "main_game": [False, None, None],
            "saves_menu": [False, None, None],
            "settings_menu": [False, None, None],
            "pause_menu": [False, None, None],
            "other": [False, None, None],
            "running": [1]
        }
        self.handle = {
            "main_menu": app.shader_prog_2D.main_menu,
            "utility": app.shader_prog_2D.utility,
            "main_game": self.surf.main_game.handle,
            "saves_menu": app.shader_prog_2D.saves_menu,
            "settings_menu": app.shader_prog_2D.settings_menu,
            "pause_menu": app.shader_prog_2D.pause_menu,
            "other": app.shader_prog_2D.other
        }
        self.update = {
            "main_menu": self.app.shader_prog_2D.main_menu.update,
            "utility": self.app.shader_prog_2D.utility.update,
            "main_game": self.surf.main_game.update,
            "saves_menu": self.app.shader_prog_2D.saves_menu.update,
            "settings_menu": self.app.shader_prog_2D.settings_menu.update,
            "pause_menu": self.app.shader_prog_2D.pause_menu.update,
            "player_control": self.app.player.update,
            "other": self.app.shader_prog_2D.other.update,
        }
        self.render = {
            "main_menu": self.app.shader_prog_2D.main_menu.draw2d,
            "utility": self.app.shader_prog_2D.utility.draw2d,
            "main_game": self.surf.main_game.render,
            "saves_menu": self.app.shader_prog_2D.saves_menu.draw2d,
            "settings_menu": self.app.shader_prog_2D.settings_menu.draw2d,
            "pause_menu": self.app.shader_prog_2D.pause_menu.draw2d,
            "other": self.app.shader_prog_2D.other.draw2d
        }

        # Init utility vision --> fps counter, version info
        # Init main menu

    def init_surfaces(self):
        surf_group = type("Contains each single surface", (), {})()

        # Initialize each surface alone
        surf_group.utility = UtilityMenu(self.app)
        surf_group.main_game = MainGame(self.app)
        surf_group.main_menu = MainMenu(self.app)
        surf_group.saves_menu = SavesMenu(self.app)
        surf_group.settings_menu = SettingsMenu(self.app)
        surf_group.pause_menu = PauseMenu(self.app)
        surf_group.other = Other(self.app)

        return surf_group

    def handle_current_scene(self):
        self.active = [[scene, status] for scene, status in self.flags.items() if status[0] is True]
        self.active = sorted(self.active, key=lambda x: x[1][1], reverse=True)

    def update_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            if act_surf[1][2]:
                self.update[act_surf[0]](self.app)
        # Check if player should move, if not reset all (TBD)
        if self.flags['main_game'][1] == 1:
            self.update['player_control']()

    def render_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            self.render[act_surf[0]]()


class Other:

    def __init__(self, app):
        pass
        # Custom cursor
        #other_cursor = DynamicSprite(app, "other", "cursor", "svg", False)
        #app.shader_prog_2D.other.add(other_cursor)


class MainMenu:

    def __init__(self, app):
        # Init each sprite for the main menu scene
        # Load first backgrounds and then foremost sprites, defining the z order

        # Background menu button
        background_menu = BackgroundSprite(app, "main_menu", "menu",  "svg", False)
        app.shader_prog_2D.main_menu.add(background_menu)
        # Background team logo button
        background_logo = BackgroundSprite(app, "main_menu", "logo", "svg", False)
        app.shader_prog_2D.main_menu.add(background_logo)

        # Play button
        button_play = ButtonSprite(app, "main_menu", "play", "svg", True)
        app.shader_prog_2D.main_menu.add(button_play)
        # Continue button (with saves)
        button_continue = ButtonSprite(app, "main_menu", "continue", "svg", True)
        app.shader_prog_2D.main_menu.add(button_continue)
        # Settings button
        button_settings = ButtonSprite(app, "main_menu", "settings", "svg", True)
        app.shader_prog_2D.main_menu.add(button_settings)
        # Quit button
        button_quit = ButtonSprite(app, "main_menu", "quit", "svg", True)
        app.shader_prog_2D.main_menu.add(button_quit)


class UtilityMenu:

    def __init__(self, app):
        fps_counter = FpsSprite(app)
        util_text = UtilityStaticText(app, "version_info", 'Genesim Lab - version alpha\nAuthor: F. Morbidelli\nTrial version',
                                      pg.Rect(1620, 0, 300, 100), "right")
        app.shader_prog_2D.utility.add(fps_counter)
        app.shader_prog_2D.utility.add(util_text)


class PauseMenu:

    def __init__(self, app):
        # Init each sprite for the pause menu scene
        # Background transparent window button
        background_window = BackgroundSprite(app, "pause_menu", "window", "svg", False)
        app.shader_prog_2D.pause_menu.add(background_window)

        # Return to main menu button
        button_return_main = ButtonSprite(app, "pause_menu", "return_main", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_return_main)
        # Save button
        button_save = ButtonSprite(app, "pause_menu", "save", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_save)
        # Settings button
        button_settings = ButtonSprite(app, "pause_menu", "settings", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_settings)
        # Quit button
        button_quit = ButtonSprite(app, "pause_menu", "quit", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_quit)


class SavesMenu:

    def __init__(self, app):
        pass


class SettingsMenu:

    def __init__(self, app):
        pass


class MainGame:

    def __init__(self, app):
        self.app = app

        # Istantiate world
        self.world = None

        # Init overlay elements
        overlay_crosshair = OverlaySprite(app, "main_game", "crosshair", "svg", True)
        app.shader_prog_2D.main_game.add(overlay_crosshair)

    def init_world(self):
        # Initialize 3D graphic elements
        self.world = World(self.app)

    def handle(self):
        self.app.shader_prog_3D()
        self.app.shader_prog_2D.main_game()

    def update(self, app):
        self.world.update()
        self.app.shader_prog_3D.update()
        self.app.shader_prog_2D.main_game.update(app)

    def render(self):
        self.world.render()
        self.app.shader_prog_2D.main_game.draw2d()


def init_shaders_2d(app):
    # Creates shaders programs organized in subgroups relative to the different scenes
    programs = type("Contains all subgroup related to same shader program", (), {})()
    programs.main_menu = GLTextures2D(app)
    programs.utility = GLTextures2D(app)
    programs.pause_menu = GLTextures2D(app)
    programs.settings_menu = GLTextures2D(app)
    programs.saves_menu = GLTextures2D(app)
    programs.main_game = GLTextures2D(app)
    programs.other = GLTextures2D(app)

    return programs
