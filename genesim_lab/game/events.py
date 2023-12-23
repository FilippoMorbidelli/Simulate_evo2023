# Evolution simulation project - events module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles events and actions to compute

# Import packages ------------------------------|
import pygame as pg


# Main event handler ---------------------------|
class EventHandler:  # Manage every event related to player and scenes (simulation events may be on other function)
    def __init__(self, app):
        # Init flags to define current scene and sprite to search on
        self.app = app
        self.master_scene = None  # Master scene to search sprite on
        self.active_sprite = None  # Active sprite to search for events
        self.catalog = events_catalog()  # Compute event catalog for each action
        self.event_types = EventTypes(self.app)  # Init event types class

        # Custom FPS event to update it every half second
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)

    def find_active_sprite(self, app, scene):
        try:
            for sprite in scene:
                try:
                    check_over = sprite.mask.get_at(app.mouse)
                except:
                    break
                if sprite.flag != check_over:
                    sprite.flag = check_over
                    if sprite.flag:
                        sprite.image = sprite.sprite_T  # Select sprite active
                        self.active_sprite = sprite.name  # Give sprite to event checker
                        break  # Break current search since over sprite has been found
                    elif not sprite.flag:
                        sprite.image = sprite.sprite_F  # Deselect sprite active
                        self.active_sprite = None  # No active over sprite
        except:
            self.active_sprite = None

    def handle_events(self, app):
        # Search for master scene and sprite on which mouse is currently over
        app.scene.surfaces.handle_current_scene()  # Extract active surfaces from flags
        for act_surf in app.scene.surfaces.active:  # Iter over all active surfaces
            if act_surf[1][1] == "Master":  # Select master surface
                scene = app.scene.surfaces.handle[act_surf[0]]  # Retrieve sprite group related to surface
                self.master_scene = act_surf[0]  # Save master surface
                self.find_active_sprite(app, scene)  # Find active sprite on scene

        # Switch between case with active sprite or not active sprite (check only always active events)
        match self.active_sprite:
            case None:
                # Check always active and on condition events
                for event in self.app.event_list:
                    for name, data in self.catalog["other"].items():  # Extract event data
                        if self.app.scene.surfaces.flags[data[1][0]][data[1][1]] == data[1][2]:  # Condition validity
                            event_to_check = getattr(self.event_types, data[0])  # Get event type
                            event_to_check(event, *data[2])  # search if event is present

            case str():
                # Check always active and on condition events
                for event in self.app.event_list:
                    for name, data in self.catalog["other"].items():
                        if self.app.scene.surfaces.flags[data[1][0]][data[1][1]] == data[1][2]:
                            event_to_check = getattr(self.event_types, data[0])  # Get event type
                            event_to_check(event, *data[2])  # search if event is present

                    # check for action/event possible with active sprite
                    event_data = self.catalog[self.master_scene][self.active_sprite]  # Extract event data
                    event_to_check = getattr(self.event_types, event_data[0])  # Get event type
                    event_to_check(event, *event_data[1])  # search if event is present


# Single events --------------------------------|
class EventTypes:
    def __init__(self, app):
        self.app = app

    def change_scene(self, event, etype, button, flag_name, flag_value):
        if event.type == etype and event.button == button:
            for action in range(len(flag_name)):
                self.app.scene.surfaces.flags[flag_name[action]] = flag_value[action]

    def quit_game_m(self, event, etype, button, flag_value):
        if event.type == etype and event.button == button or event.type == pg.QUIT:
            self.app.is_running = flag_value

    def quit_game_k(self, event, etype, key, flag_value):
        if event.type == etype and event.key == key or event.type == pg.QUIT:
            self.app.is_running = flag_value

    def add_secondary_scene(self, event, e_type, button, action, condition=True):
        # Handles mouse buttons events
        # event.button = [1, 2, 3, 4, 5] == [left, middle, right, scroll up, scroll down]
        if event.type == e_type and event.button == button and condition:
            return action


def events_catalog():
    catalog = {
        "other": {
            # name = [handle type, [conditions], [event.type, event.key, flag_names, flag_values]]
            "open_pause_menu": ["change_scene",
                                ["main_game", 1, str()],
                                [pg.KEYDOWN, pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, "Secondary", "Frozen"],
                                                                                        [True, "Master", "Update"]], ]],
            "close_pause_menu": ["change_scene",
                                 ["pause_menu", 0, True],
                                 [pg.KEYDOWN, pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, "Master", "Update"],
                                                                                         [False, None, None]], ]],
            "emergency_quit": ["quit_game_k",
                               ["running", 0, 1],  # Trick to get always true condition
                               [pg.KEYDOWN, [pg.K_LALT, pg.K_F4], False]]
        },
        "main_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_play": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["main_game", "main_menu"],
                                             [[True, "Master", "Update"], [False, None, None]], ], ],
            "button_continue": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["saves_menu", "main_menu"],
                                                 [[True, "Master", "Update"], [False, None, None]], ], ],
            "button_settings": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["settings_menu", "main_menu"],
                                                 [[True, "Master", "Update"], [False, None, None]], ], ],
            # sprite = [handle type,[event.type, event.button, game_running]]
            "button_quit": ["quit_game_m", [pg.MOUSEBUTTONDOWN, 1, False]]
        },
        "pause_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_return_main": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["pause_menu", "main_menu"],
                                                    [[False, "Null", "Null"], [True, "Master", "Update"]], ], ]
        },
    }
    return catalog
