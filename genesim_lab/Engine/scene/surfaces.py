# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.Engine.world_gen.world import World
from genesim_lab.Engine.scene.sprite import *
from enum import IntEnum
import copy
from pathlib import Path
import os


# New Types ------------------------------------|
class GS(IntEnum):  # GS stands for GameState
    MainMenu       = 0
    MainGame       = 1
    PauseMenu      = 2
    SaveLoadMenu   = 3
    SettingsMenu   = 4
    UtilityOverlay = 5
    Other          = 6

# All surfaces ---------------------------------|
class Surfaces:

    def __init__(self, app):
        self.app = app

        self.surf = self.init_surfaces()
        self.active = None
        self.master = None
        self.max = None

        # Init flags, handle, update and render for each scene
        self.state = {
            # Dictionary containing each Scene status flags
            # Surface: render --> [True, False]
            #          depth  --> [1, 2, 3, ..., None]
            #          update --> [Update, Frozen, None]
            GS.MainMenu       : {"Render" : True , "Depth" : 1   , "Update" : False},
            GS.MainGame       : {"Render" : False, "Depth" : None, "Update" : False},
            GS.SaveLoadMenu   : {"Render" : False, "Depth" : None, "Update" : False},
            GS.SettingsMenu   : {"Render" : False, "Depth" : None, "Update" : False},
            GS.PauseMenu      : {"Render" : False, "Depth" : None, "Update" : False},
            GS.UtilityOverlay : {"Render" : False, "Depth" : None, "Update" : False},
            GS.Other          : {"Render" : False, "Depth" : None, "Update" : False}
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

        # Compute current Scene state
        self.handle_current_scene()

    def init_surfaces(self):
        surf_group = type("Contains each single surface", (), {})()

        # Initialize each surface alone
        surf_group.utility       = UtilityMenu(self.app)
        surf_group.main_game     = MainGame(self.app)
        surf_group.main_menu     = MainMenu(self.app)
        surf_group.saves_menu    = SaveLoadMenu(self.app)
        surf_group.settings_menu = SettingsMenu(self.app)
        surf_group.pause_menu    = PauseMenu(self.app)
        surf_group.other         = Other(self.app)

        return surf_group

    def handle_current_scene(self):
        self.active = [scene for scene, status in self.state.items() if status["Render"] is True]
        self.active = sorted(self.active, key=lambda x: self.state[x]["Depth"])  # Sort active scenes depending on depth

        self.master = [i for i in self.active if type(self.state[i]["Depth"]) is int][-1]
        self.max = self.state[self.master]["Depth"]

    def update_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            if self.state[act_surf]["Update"]:
                self.update[act_surf](self.app)
        # Player movement is allowed only when MainGame is main rendered page
        if self.state[GS.MainGame]["Depth"] == self.max:
            self.app.player.update()

    def render_current_scene(self):
        for act_surf in self.active:  # Search for active surface to update
            self.render[act_surf]()

    # These methods are used by events to change state of the different scenes
    def reset_status(self, scene):
        self.state[scene] = {"Render" : False, "Depth" : None, "Update" : False}

    def set_primary(self, scene):
        # Reset all statuses
        reset = {"Render" : False, "Depth" : None, "Update" : False}
        self.state = {my_key : copy.deepcopy(reset) for my_key in GS}
        # Set the input as primary+
        self.state[scene] = {"Render" : True, "Depth" : 1, "Update" : True}

    def set_only_primary(self, scene, overlay = GS.UtilityOverlay):
        # Update Scene to Primary level without resetting others
        self.state[scene] = {"Render" : True, "Depth" : self.max + 1, "Update" : True}
        # Update Overlay
        if self.state[overlay]["Render"]:
            self.update_overlay(overlay)

    def set_custom(self, scene, depth = False, activity = True, overlay = GS.UtilityOverlay):
        # Update custom scene
        # Update Render
        self.state[scene]["Render"] = True
        # Update Depth, if passed
        if depth:
            self.state[scene]["Depth"] = depth
        # Update Activity
        self.state[scene]["Update"] = activity
        # Update Overlay
        if self.state[overlay]["Render"]:
            self.update_overlay(overlay)

    def set_switch(self, scene, depth, update = True):
        # Switch Scene render
        self.state[scene]["Render"] = not self.state[scene]["Render"]
        # Switch Arguments
        if self.state[scene]["Render"]:
            self.state[scene]["Depth"] = depth
            self.state[scene]["Update"] = update
        else:
            self.state[scene]["Depth"] = None
            self.state[scene]["Update"] = False

    def update_overlay(self, overlay):
        self.state[overlay]["Depth"] = self.state[self.master]["Depth"] + 0.1


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
        background_menu = BackgroundSprite(app, "menu/main_menu", "menu",  "svg", False)
        app.shader_prog_2D.main_menu.add(background_menu)
        # Background team logo button
        background_logo = BackgroundSprite(app, "menu/main_menu", "logo", "svg", False)
        app.shader_prog_2D.main_menu.add(background_logo)

        # Play button
        button_play = ButtonSprite(app, "menu/main_menu", "play", "svg", True)
        app.shader_prog_2D.main_menu.add(button_play)
        # Continue button (with SaveFiles)
        button_continue = ButtonSprite(app, "menu/main_menu", "continue", "svg", True)
        app.shader_prog_2D.main_menu.add(button_continue)
        # Settings button
        button_settings = ButtonSprite(app, "menu/main_menu", "settings", "svg", True)
        app.shader_prog_2D.main_menu.add(button_settings)
        # Quit button
        button_quit = ButtonSprite(app, "menu/main_menu", "quit", "svg", True)
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
        background_window = BackgroundSprite(app, "menu/pause_menu", "window", "svg", False)
        app.shader_prog_2D.pause_menu.add(background_window)

        # Return to main menu button
        button_return_main = ButtonSprite(app, "menu/pause_menu", "return_main", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_return_main)
        # Save button
        button_save = ButtonSprite(app, "menu/pause_menu", "save", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_save)
        # Settings button
        button_settings = ButtonSprite(app, "menu/pause_menu", "settings", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_settings)
        # Quit button
        button_quit = ButtonSprite(app, "menu/pause_menu", "quit", "svg", True)
        app.shader_prog_2D.pause_menu.add(button_quit)


class SaveLoadMenu:

    def __init__(self, app):
        # Save Files path
        self.save_path = Path(__file__).parent.parent.parent.parent / app.stg.util.save_path
        self.save_info = "SaveInfo.txt"
        self.save_anchor_basic = [350, 200]
        self.save_anchor_n = [0, 160]
        self.max_saves = 5
        # Init each sprite for the SaveLoad menu scene
        # Background

        # Temp background TO BE REMOVED!!!!
        temp_surf = pg.sprite.Sprite()
        temp_surf.flag = False
        temp_surf.name = "blank_screen"
        temp_surf.forced_reconstruct = False
        temp_surf.rect = app.stg.window.rect
        temp_surf.image = pg.Surface(app.stg.window.rect.size, pg.SRCALPHA, 32)
        temp_surf.image.fill((0, 0, 0))
        app.shader_prog_2D.saves_menu.add(temp_surf)
        # Title (alternating between Load and Save)
        static_alt_title = StaticAltSprite(app, "menu/saves_menu", False, ["load", "save"], [75, 30])
        app.shader_prog_2D.saves_menu.add(static_alt_title)
        # Save File blank container
        for n in range(self.max_saves):
            anchor = (self.save_anchor_basic[0] +  n * self.save_anchor_n[0], self.save_anchor_basic[1] +  n * self.save_anchor_n[1])
            container_save_n = BackgroundSprite(app, "menu/saves_menu", "save_container", "svg", False, anchor, str(n))
            app.shader_prog_2D.saves_menu.add(container_save_n)
        # Save File info and interaction
        for save in os.listdir(self.save_path):
            with open(self.save_path / save / self.save_info, "r") as f:
                # Extract save info
                info = f.read().split(",")
                name, date, num = info
                # Create Save interactable
                anchor = (self.save_anchor_basic[0] +  int(num) * self.save_anchor_n[0], self.save_anchor_basic[1] +  int(num) * self.save_anchor_n[1])
                button_save_n = ButtonSprite(app, "menu/saves_menu", "save_label", "svg", True, anchor, str(int(num)))
                # Write Save Info on interactable
                blit_text_to_surf(app, button_save_n, name, anchor=(80, 45))
                blit_text_to_surf(app, button_save_n, date, anchor=(180, 45))
                # Add to Class
                app.shader_prog_2D.saves_menu.add(button_save_n)
                # Close file
                f.close()

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
