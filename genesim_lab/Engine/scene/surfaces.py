# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.Engine.world_gen.world import World
from genesim_lab.Engine.scene.sprite import *
from enum import IntEnum


# New Types ------------------------------------|
class GS(IntEnum):  # GS stands for GameState
    MainMenu       = 1
    MainGame       = 2
    PauseMenu      = 3
    SaveLoadMenu   = 4
    SettingsMenu   = 5
    UtilityOverlay = 6
    Other          = 7
    Running        = 8

    PlayerControl  = 20

class SD(IntEnum):  # SD stands for StateData
    Render = 0
    Depth  = 1
    Update = 2

# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        self.surf = self.init_surfaces()
        self.active = None

        # Init flags, handle, update and render for each scene
        self.state = {
            # Dictionary containing each Scene status flags
            # Surface: render --> [True, False]
            #          depth  --> [1, 2, 3, ..., None]
            #          update --> [Update, Frozen, None]
            GS.MainMenu       : [True, 1, "Update"],
            GS.MainGame       : [False, None, None],
            GS.SaveLoadMenu   : [False, None, None],
            GS.SettingsMenu   : [False, None, None],
            GS.PauseMenu      : [False, None, None],
            GS.UtilityOverlay : [False, None, None],
            GS.Other          : [False, None, None],
            GS.Running        : [1]
        }
        self.handle = {
            GS.MainMenu       : app.shader_prog_2D.main_menu,
            GS.UtilityOverlay : app.shader_prog_2D.utility,
            GS.MainGame       : self.surf.main_game.handle,
            GS.SaveLoadMenu   : app.shader_prog_2D.saves_menu,
            GS.SettingsMenu   : app.shader_prog_2D.settings_menu,
            GS.PauseMenu      : app.shader_prog_2D.pause_menu,
            GS.Other          : app.shader_prog_2D.other
        }
        self.update = {
            GS.MainMenu       : self.app.shader_prog_2D.main_menu.update,
            GS.UtilityOverlay : self.app.shader_prog_2D.utility.update,
            GS.MainGame       : self.surf.main_game.update,
            GS.SaveLoadMenu   : self.app.shader_prog_2D.saves_menu.update,
            GS.SettingsMenu   : self.app.shader_prog_2D.settings_menu.update,
            GS.PauseMenu      : self.app.shader_prog_2D.pause_menu.update,
            GS.PlayerControl  : self.app.player.update,
            GS.Other          : self.app.shader_prog_2D.other.update,
        }
        self.render = {
            GS.MainMenu       : self.app.shader_prog_2D.main_menu.draw2d,
            GS.UtilityOverlay : self.app.shader_prog_2D.utility.draw2d,
            GS.MainGame       : self.surf.main_game.render,
            GS.SaveLoadMenu   : self.app.shader_prog_2D.saves_menu.draw2d,
            GS.SettingsMenu   : self.app.shader_prog_2D.settings_menu.draw2d,
            GS.PauseMenu      : self.app.shader_prog_2D.pause_menu.draw2d,
            GS.Other          : self.app.shader_prog_2D.other.draw2d
        }

    def init_surfaces(self):
        surf_group = type("Contains each single surface", (), {})()

        # Initialize each surface alone
        surf_group.utility       = UtilityMenu(self.app)
        surf_group.main_game     = MainGame(self.app)
        surf_group.main_menu     = MainMenu(self.app)
        surf_group.saves_menu    = SavesMenu(self.app)
        surf_group.settings_menu = SettingsMenu(self.app)
        surf_group.pause_menu    = PauseMenu(self.app)
        surf_group.other         = Other(self.app)

        return surf_group

    def handle_current_scene(self):
        self.active = [scene for scene, status in self.state.items() if status[SD.Render] is True]
        self.active = sorted(self.active, key=lambda x: self.state[x][SD.Depth], reverse=True)  # Sort active scenes depending on depth

    def update_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            if self.state[act_surf][SD.Update]:
                self.update[act_surf](self.app)
        # Player movement is allowed only when MainGame is main rendered page
        if self.state[GS.MainGame][SD.Depth] == 1:
            self.update[GS.PlayerControl]()

    def render_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            self.render[act_surf]()


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
        # Continue button (with SaveFiles)
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

        # Instance world
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
    # Creates Shaders programs organized in subgroups relative to the different scenes
    programs = type("Contains all subgroup related to same shader program", (), {})()
    programs.main_menu     = GLTextures2D(app)
    programs.utility       = GLTextures2D(app)
    programs.pause_menu    = GLTextures2D(app)
    programs.settings_menu = GLTextures2D(app)
    programs.saves_menu    = GLTextures2D(app)
    programs.main_game     = GLTextures2D(app)
    programs.other         = GLTextures2D(app)

    return programs
