# Evolution simulation project - events module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles events and actions to compute

# Import packages ------------------------------------------------------------------------------------------------------
import pygame as pg
from string import digits
from genesim_lab.Engine.scene.surfaces import GS


# Main event handler ---------------------------------------------------------------------------------------------------
class EventHandler:  # Manage every event related to player and scenes (simulation events may be on other function)
    def __init__(self, app):
        # Init flags to define current scene and sprite to search on
        self.app           = app
        self.scene_ptr     = app.scene.surfaces # Current state and data of each scene
        self.master_scene  = None  # Master scene to search sprite on
        self.active_sprite = None  # Active sprite to search for events
        self.event_types   = EventTypes(app)  # Init event types class
        self.catalog       = self.events_catalog()  # Compute event catalog for each action
        # Other

        # Custom FPS event to update it every half second
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)
        # Custom UI event to write or remove | char every half second
        self.ui_dict = {
            "ui_string"     : "",
            "ui_action"     : "",
            "ui_char_time"  : 0,
            "ui_char_event" : 750,
            "ui_show"       : False
        }

#---## Main Event handler functions ------------------------------------------------------------------------------------
    def find_active_sprite(self, scene):
        # Try to iterate over scene sprites
        try:
            for sprite in scene:
                # If sprite is static skip
                if sprite.to_interact:
                    # Find if collision is true
                    mouse_pos = self.app.mouse[0] - sprite.rect.x, self.app.mouse[1] - sprite.rect.y
                    try:
                        check_over = sprite.mask.get_at(mouse_pos)
                    except(IndexError,):
                        # Mouse is outside sprite rect
                        continue
                    # Check if already over
                    if sprite.over != check_over:
                        # Set over attribute
                        sprite.over = check_over
                        if sprite.over:
                            # Switch sprite active
                            sprite.image = sprite.sprite_T
                            self.active_sprite = sprite.name
                            break  # Break current search since over sprite has been found
                        else:
                            # Switch sprite active
                            sprite.image = sprite.sprite_F
                            self.active_sprite = None
        # No sprite is present so no sprite can be active
        except(Exception,):
            print("No Sprite in Scene") # TO BE REMOVED
            self.active_sprite = None

    def handle_events(self):
        # This function handle events that can happen in the current scene
        # Find master surface
        self.master_scene = self.scene_ptr.master # TBD no sense to update it each frame
        # Find active sprite (if any)
        self.find_active_sprite(self.scene_ptr.handle[self.master_scene])

        # Check events happening
        match (self.master_scene, self.active_sprite):

            # [Main Game, check all events]
            case (GS.MainGame, _):
                # Iterate over each event
                for event in self.app.event_list:
                    # Other User events
                    if self.search_generic_event(event=event):
                        continue
                    # Non-Sprite User events
                    if self.search_non_sprite_event(event=event):
                        continue
                    # Sprite User events
                    if self.active_sprite is not None:
                        if self.search_sprite_event(event=event):
                            continue
                    # Player events
                    self.app.player.handle_event(event=event) # TBD
                    # World events
                    # TBD

            # [User input requested, check related events and others only]
            case (GS.UserInput, _):
                # Iterate over each event
                for event in self.app.event_list:
                    # Other User events
                    if self.search_generic_event(event=event):
                        continue
                    # Text Input
                    self.search_user_input(event=event)
                # Append | character to current string every 0.5 seconds
                self.ui_dict["ui_char_time"] += self.app.delta_time
                if self.ui_dict["ui_char_time"] >= self.ui_dict["ui_char_event"]:
                    if self.ui_dict["ui_show"]:
                        self.ui_dict["ui_string"] = self.ui_dict["ui_string"][:-1]
                        self.ui_dict["ui_show"] = False
                        self.ui_dict["ui_char_time"] = 0
                    else:
                        self.ui_dict["ui_string"] += "|"
                        self.ui_dict["ui_show"] = True
                        self.ui_dict["ui_char_time"] = 0

            # [Any other scene, check all events]
            case (_, _):
                # Iterate over each event
                for event in self.app.event_list:
                    # Other User events
                    if self.search_generic_event(event=event):
                        continue
                    # Non-Sprite User events
                    if self.search_non_sprite_event(event=event):
                        continue
                    # Sprite User events
                    if self.active_sprite is not None:
                        if self.search_sprite_event(event=event):
                            continue

#---## Search Event functions ------------------------------------------------------------------------------------------
    # Function that retrieves from catalog each Generic event and calls the specific function
    def search_generic_event(self, event):
        # Iterate over each event of class "OTHER"
        for name, data in self.catalog[GS.Other].items():
            e_type, conditions, outcomes = data
            # Retrieve event type
            event_fnc = getattr(self.event_types, e_type)
            # Compute event
            if event_fnc(event, *conditions, outcomes):
                # Event found, return up
                return True
        # Event not found in catalog
        return False

    # Function that retrieves from catalog each Master Scene event related to sprites and calls the specific function
    def search_sprite_event(self, event):
        # Strip and save ID of multiple sprite
        act_sprite = self.active_sprite.rstrip(digits)
        # Save it TBD
        # No need to Iterate over each event of class Master Scene
        e_type, conditions, outcomes = self.catalog[self.master_scene]["sprite"][act_sprite]
        # Retrieve event type
        event_fnc = getattr(self.event_types, e_type)
        # Compute event
        if event_fnc(event, *conditions, outcomes):
            # Event found, return up
            return True
        # Event not found in catalog
        return False

    # Function that retrieves from catalog each Master Scene event related to Non-sprites and calls the specific function
    def search_non_sprite_event(self, event):
        # Iterate over each event of class Master Scene
        for name, data in self.catalog[self.master_scene]["non_sprite"].items():
            e_type, conditions, outcomes = data
            # Retrieve event type
            event_fnc = getattr(self.event_types, e_type)
            # Compute event
            if event_fnc(event, *conditions, outcomes):
                # Event found, return up
                return True
            # Event not found in catalog
        return False

    def search_user_input(self, event):
        # Check that event is key pressed
        if event.type == pg.KEYDOWN:
            # Retrieve key
            in_key = event.key
            # Perform related action
            if in_key == pg.K_BACKSPACE:
                self.ui_dict["ui_string"] = self.ui_dict["ui_string"][:-1]
            elif in_key == pg.K_RETURN:
                self.event_types.user_input_action(self.ui_dict["ui_action"])
                self.ui_dict["ui_string"] = ""
                self.ui_dict["ui_action"] = ""
            elif in_key == pg.K_ESCAPE:
                self.event_types.user_input_action("")
                self.ui_dict["ui_string"] = ""
                self.ui_dict["ui_action"] = ""
            elif in_key == pg.K_MINUS:
                self.ui_dict["ui_string"] += "_"
            elif in_key <= 127:
                self.ui_dict["ui_string"] += chr(in_key)

#---## Event Catalog ---------------------------------------------------------------------------------------------------
    def events_catalog(self):
        # Full catalog containing every user interaction in the game
        # The catalog is organized based of the current scene the player is at.
        # Each scene, except "OTHER" divides into sprite and non-sprite events
        # Every interaction is represented by:
        # Interaction name = [event type, event conditions, event outcomes]
        catalog = {
            # Other events / always active events
            GS.Other: {
                "emergency_quit" : [
                    "quit_game",  # Event handle to use for this custom event
                    [pg.KEYDOWN, "key", [pg.K_LALT, pg.K_F4]],  # Event data
                    [],
                ],
                "debug_window" : [
                    "change_scene",  # Event handle to use for this custom event
                    [pg.KEYDOWN, "key", pg.K_F1],  # Event data
                    [lambda : self.scene_ptr.set_switch(GS.UtilityOverlay, self.scene_ptr.max + 0.1)],
                ],
            },
            # Main menu interactions
            GS.MainMenu: {
                "sprite" : {
                    "button_play" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_primary(GS.MainGame),
                         lambda : self.scene_ptr.surf.main_game.init_world()],
                    ],
                    "button_continue" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_primary(GS.SaveLoadMenu),
                         lambda : self.app.shader_prog_2D.saves_menu.sprites()[1].alternate("load")],
                    ],
                    "button_settings" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_primary(GS.SaveLoadMenu)],
                    ],
                    "button_quit" : [
                        "quit_game",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],  # Event data
                        [],
                    ]
                },
                "non_sprite" : {
                    # Currently no event present
                }
            },
            # Pause menu interactions
            GS.PauseMenu: {
                "sprite" : {
                    "button_return_main" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_primary(GS.MainMenu)],  # Event data
                    ],
                    "button_save" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_only_primary(GS.SaveLoadMenu),
                         lambda : self.app.shader_prog_2D.saves_menu.sprites()[1].alternate("save")],
                    ],
                    "button_settings" : [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.scene_ptr.set_primary(GS.SettingsMenu)],
                    ],
                    "button_quit": [
                        "quit_game",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],  # Event data
                        [],
                    ]
                },
                "non_sprite" : {
                    "close_pause_menu": [
                        "change_scene",  # Op type
                        [pg.KEYDOWN, "key", pg.K_ESCAPE],  # Activation conditions
                        [lambda : self.scene_ptr.set_primary(GS.MainGame)],  # Outcomes
                    ]
                }
            },
            # Main Game interactions
            GS.MainGame : {
                "sprite" : {
                    # Currently no event present
                },
                "non_sprite" : {
                    "open_pause_menu": [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.KEYDOWN, "key", pg.K_ESCAPE],
                        [lambda : self.scene_ptr.set_only_primary(GS.PauseMenu),
                         lambda : self.scene_ptr.set_custom(GS.MainGame, activity = False)],
                    ]
                }
            },
            # Save-Load menu interactions
            GS.SaveLoadMenu : {
                "sprite" : {
                    "button_save_label": [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda : self.app.save_load.manage_sl(self.active_sprite)],  # Event data
                    ],
                    "button_save_new": [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.MOUSEBUTTONDOWN, "button", 1],
                        [lambda: self.scene_ptr.set_userinput("save") if self.app.scene.sprite_util["SaveLoad"] == "save" else None],  # mAYBE PUT START NEW GAME SAVE?
                    ]
                },
                "non_sprite" : {
                    "return_main_menu": [
                        "change_scene",  # Event handle to use for this custom event
                        [pg.KEYDOWN, "key", pg.K_ESCAPE],
                        [lambda: self.scene_ptr.set_primary(GS.MainMenu) if self.app.scene.sprite_util["SaveLoad"] == "load" else self.scene_ptr.reset_status(GS.SaveLoadMenu)],
                    ]
                }
            }
        }
        return catalog


# Event Types ----------------------------------------------------------------------------------------------------------
class EventTypes:
    def __init__(self, app):
        self.app       = app
        self.scene_ptr = app.scene.surfaces  # Current state and data of each scene
        self.prev_max  = None  # Depth of master scene (no overlays)

    def change_scene(self, event, input_action, input_type, input_keys, actions):
        # Check if the input action is the same as requested
        if event.type == input_action:
            # Check input type (mouse or keyboard)
            if input_type == 'button':
                event_in = event.button
            else:
                event_in = event.key
            # Check that user input is correct
            if event_in == input_keys:
                # Compute actions
                for act in actions:
                    act()
                # Handle current active scenes after event management
                self.scene_ptr.handle_current_scene()
                self.app.custom_events.master_scene = self.scene_ptr.master
                self.app.custom_events.active_sprite = None
                # Manage mouse since scene changed
                self.manage_mouse()
                # Confirm event found
                return True
        # Event not compliant
        return False

    def quit_game(self, event, input_action, input_type, input_keys, _):
        # Check if event is pg.QUIT
        if event.type == pg.QUIT:
            # Close game
            self.app.is_running = False
            # Confirm event found
            return True
        # Check if the input action is the same as requested
        if event.type == input_action:
            # Check input type (mouse or keyboard)
            if input_type == 'button':
                event_in = event.button
            else:
                event_in = event.key
            # Check that user input is correct
            if event_in == input_keys:
                # Close game
                self.app.is_running = False
                # Confirm event found
                return True
        # Event not compliant
        return False

    def manage_mouse(self):
        # Retrieve Main Game depth
        mg_depth = self.scene_ptr.state[GS.MainGame]["Depth"]
        # Manage mouse depending on Main Game state
        if self.prev_max != self.scene_ptr.max:
            # Hide mouse since Main Game is main scene
            if mg_depth == self.scene_ptr.max or self.scene_ptr.master == GS.UserInput:
                pg.mouse.set_visible(False)
                pg.mouse.get_rel()
            # Main game not primary scene so show and set mouse pos
            elif mg_depth != self.scene_ptr.max:
                pg.mouse.set_pos(self.app.screen.get_rect().center)
                pg.mouse.set_visible(True)
            # Exit from Main Game, reset player
            elif mg_depth is None:
                self.app.player.reset()
            # Update previous max
            self.prev_max = self.scene_ptr.max

    def user_input_action(self, action):
        # Exec action depending on type of user input
        self.scene_ptr.reset_status(GS.UserInput)
        if action == "save":
            self.app.save_load.manage_sl(self.app.custom_events.active_sprite)
        else:
            pass # TBD
        # Reset Sprite TO BE DONEEEEEEEEEEE
        #if self.app.custom_events.active_sprite:
        #    for sprite in self.scene_ptr.handle[self.app.custom_events.master_scene]:
        #        if sprite.name == self.app.custom_events.active_sprite:
        #            sprite.over = False
        #            sprite.image = sprite.sprite_F
        # Handle current active scenes after event management
        self.scene_ptr.handle_current_scene()
        self.app.custom_events.master_scene = self.scene_ptr.master
        self.app.custom_events.active_sprite = None
        # Manage mouse since scene changed
        self.manage_mouse()

# Custom exceptions --
class SceneChanged(Exception):
    pass
