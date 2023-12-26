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
                if sprite.flag:
                    try:
                        check_over = sprite.mask.get_at(app.mouse)
                    except:
                        break
                    if sprite.over != check_over:
                        sprite.over = check_over
                        if sprite.over:
                            sprite.image = sprite.sprite_T  # Select sprite active
                            self.active_sprite = sprite.name  # Give sprite to event checker
                            break  # Break current search since over sprite has been found
                        elif not sprite.over:
                            sprite.image = sprite.sprite_F  # Deselect sprite active
                            self.active_sprite = None  # No active over sprite
        except:
            self.active_sprite = None

    def handle_events(self, app):
        # Search for master scene and sprite on which mouse is currently over
        app.scene.surfaces.handle_current_scene()  # Extract active surfaces from flags
        for act_surf in app.scene.surfaces.active:  # Iter over all active surfaces
            if act_surf[1][1] == 1:  # Select master surface
                scene = app.scene.surfaces.handle[act_surf[0]]  # Retrieve sprite group related to surface
                self.master_scene = act_surf[0]  # Save master surface
                self.find_active_sprite(app, scene)  # Find active sprite on scene

        # Switch between case with active sprite or not active sprite (check only always active events)
        match self.active_sprite:
            case None:
                # Check always active and on condition events
                for event in self.app.event_list:
                    for name, data in self.catalog["other"].items():  # Extract event data
                        if data[3][0]:
                            pass
                        else:
                            self.catalog["other"][name][3][0] = True
                            continue
                        if isinstance(self.app.scene.surfaces.flags[data[1][0]][data[1][1]], data[1][2]):  # Condition validity
                            event_to_check = getattr(self.event_types, data[0])  # Get event type
                            search = event_to_check(event, *data[2])  # search if event is present
                            if search == "found":
                                try:
                                    self.catalog["other"][data[3][1]][3][0] = data[3][2]
                                except:
                                    pass

            case str():
                # Check always active and on condition events
                for event in self.app.event_list:
                    for name, data in self.catalog["other"].items():
                        if data[3][0]:
                            pass
                        else:
                            self.catalog["other"][name][3][0] = True
                            continue
                        if isinstance(self.app.scene.surfaces.flags[data[1][0]][data[1][1]], data[1][2]):
                            event_to_check = getattr(self.event_types, data[0])  # Get event type
                            search = event_to_check(event, *data[2])  # search if event is present
                            if search == "found":
                                try:
                                    self.catalog["other"][data[3][1]][3][0] = data[3][2]
                                except:
                                    pass

                    # check for action/event possible with active sprite
                    event_data = self.catalog[self.master_scene][self.active_sprite]  # Extract event data
                    event_to_check = getattr(self.event_types, event_data[0])  # Get event type
                    search = event_to_check(event, *event_data[1])  # search if event is present


# Single events --------------------------------|
class EventTypes:
    def __init__(self, app):
        self.app = app

    def change_scene_m(self, event, etype, button, flag_name, flag_value):
        if event.type == etype and event.button == button:
            prev_status = self.app.scene.surfaces.flags['main_game'][1]  # Check state of main engine before change
            for action in range(len(flag_name)):
                self.app.scene.surfaces.flags[flag_name[action]] = flag_value[action]
            self.app.custom_events.active_sprite = None  # Reset active sprite if scene is changed
            reset_view(self.app, prev_status)
            return "found"
        else:
            return "not found"

    def change_scene_k(self, event, etype, key, flag_name, flag_value):
        if event.type == etype and event.key == key:
            prev_status = self.app.scene.surfaces.flags['main_game'][1]  # Check state of main engine before change
            for action in range(len(flag_name)):
                self.app.scene.surfaces.flags[flag_name[action]] = flag_value[action]
            self.app.custom_events.active_sprite = None  # Reset active sprite if scene is changed
            reset_view(self.app, prev_status)
            return "found"
        else:
            return "not found"

    def quit_game_m(self, event, etype, button, flag_value):
        if event.type == etype and event.button == button or event.type == pg.QUIT:
            self.app.is_running = flag_value
            return "found"
        else:
            return "not found"

    def quit_game_k(self, event, etype, key, flag_value):
        if event.type == etype and event.key == key or event.type == pg.QUIT:
            self.app.is_running = flag_value
            return "found"
        else:
            return "not found"

    def add_secondary_scene(self, event, e_type, button, action, condition=True):
        # Handles mouse buttons events
        # event.button = [1, 2, 3, 4, 5] == [left, middle, right, scroll up, scroll down]
        if event.type == e_type and event.button == button and condition:
            return action


def events_catalog():
    catalog = {
        "other": {
            # name = [handle type, ban event, [conditions], [event.type, event.key, flag_names, flag_values]]
            "close_pause_menu": ["change_scene_k",
                                 ["pause_menu", 1, int],
                                 [pg.KEYDOWN, pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, 1, "Update"],
                                                                                         [False, None, None]], ],
                                 [True, "open_pause_menu", False]],
            "open_pause_menu": ["change_scene_k",
                                ["main_game", 1, int],
                                [pg.KEYDOWN, pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, 2, "Frozen"],
                                                                                        [True, 1, "Update"]], ],
                                [True, "close_pause_menu", False]],
            "emergency_quit": ["quit_game_k",
                               ["running", 0, int],  # Trick to get always true condition
                               [pg.KEYDOWN, [pg.K_LALT, pg.K_F4], False],
                               [True]],
        },
        "main_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_play": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["main_game", "main_menu"],
                                             [[True, 1, "Update"], [False, None, None]], ], ],
            "button_continue": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["saves_menu", "main_menu"],
                                                 [[True, 1, "Update"], [False, None, None]], ], ],
            "button_settings": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["settings_menu", "main_menu"],
                                                 [[True, 1, "Update"], [False, None, None]], ], ],
            # sprite = [handle type,[event.type, event.button, game_running]]
            "button_quit": ["quit_game_m", [pg.MOUSEBUTTONDOWN, 1, False]]
        },
        "pause_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_return_main": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["pause_menu", "main_menu", "main_game"],
                                                    [[False, None, None], [True, 1, "Update"], [False, None, None]], ], ],
            "button_save": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["saves_menu", "pause_menu"],
                                                 [[True, 1, "Update"], [False, None, None]], ], ],
            "button_settings": ["change_scene_m", [pg.MOUSEBUTTONDOWN, 1, ["settings_menu", "pause_menu"],
                                                 [[True, 1, "Update"], [False, None, None]], ], ],
            # sprite = [handle type,[event.type, event.button, game_running]]
            "button_quit": ["quit_game_m", [pg.MOUSEBUTTONDOWN, 1, False]]

        },
    }
    return catalog


def reset_view(app, prev_status):
    main_game_status = app.scene.surfaces.flags['main_game'][1]
    if main_game_status == 1 and main_game_status != prev_status:
        pg.mouse.set_visible(False)
        pg.mouse.get_rel()
    elif prev_status == 1 and main_game_status != prev_status:
        pg.mouse.set_pos(app.screen.get_rect().center)
        pg.mouse.set_visible(True)
    elif main_game_status is None:
        app.player.reset(app)
