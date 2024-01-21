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
        self.major_change = False  # Detects if a major change like a scene change has happened to stop event search

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

    def search_generic_event(self, event):
        for name, data in self.catalog["other"].items():  # Extract event data
            handle, cond, effect, val = data
            if val[0]:
                pass
            else:
                val[0] = True
                continue
            if isinstance(self.app.scene.surfaces.flags[cond[0]][cond[1]], cond[2]):  # Condition validity
                event_to_check = getattr(self.event_types, handle)  # Get event type
                search = event_to_check(event, *effect)  # search if event is present
                if search == "found":
                    try:
                        self.catalog["other"][val[1]][3][0] = val[2]
                    except:
                        pass

    def handle_events(self, app):
        # Search for master scene and sprite on which mouse is currently over
        app.scene.surfaces.handle_current_scene()  # Extract active surfaces from flags
        for act_surf in app.scene.surfaces.active:  # Iter over all active surfaces
            if act_surf[1][1] == 1:  # Select master surface
                scene = app.scene.surfaces.handle[act_surf[0]]  # Retrieve sprite group related to surface
                self.master_scene = act_surf[0]  # Save master surface
                self.find_active_sprite(app, scene)  # Find active sprite on scene

        # Switch between case with active sprite or not active sprite (check only always active events)
        match (self.master_scene, self.active_sprite):
            case ("main_game", _):  # Main Game, any condition
                for event in self.app.event_list:
                    # Generic events
                    self.search_generic_event(event=event)
                    if self.major_change:
                        self.major_change = False
                        break

                    # Player events
                    self.app.player.handle_event(event=event)

                    # Sprite events

                    # World events

            case (_, str()):  # Any scene, any active sprite
                # Check always active and on condition events
                for event in self.app.event_list:
                    # Generic events
                    self.search_generic_event(event=event)
                    if self.major_change:
                        self.major_change = False
                        break

                    # Sprite events
                    # check for action/event possible with active sprite
                    event_data = self.catalog[self.master_scene][self.active_sprite]  # Extract event data
                    event_to_check = getattr(self.event_types, event_data[0])  # Get event type
                    search = event_to_check(event, *event_data[1])  # search if event is present
                    if self.major_change:
                        if self.active_sprite == "button_play":
                            self.event_types.sub_init_world()
                        self.active_sprite = None  # Reset active sprite if scene is changed
                        self.major_change = False
                        break

            case (_, None):  # Any scene, inactive sprite
                # Check always active and on condition events
                for event in self.app.event_list:
                    self.search_generic_event(event=event)
                    if self.major_change:
                        self.major_change = False
                        break


# Single events --------------------------------|
class EventTypes:
    def __init__(self, app):
        self.app = app

    def change_scene(self, event, e_type, in_type, user_in, flag_name, flag_value):
        if event.type == e_type:
            if in_type == 'button':
                event_in = event.button
            else:
                event_in = event.key
            if event_in == user_in:
                prev_status = self.app.scene.surfaces.flags['main_game'][1]  # Check state of main engine before change
                for name, value in zip(flag_name, flag_value):
                    self.app.scene.surfaces.flags[name] = value
                reset_view(self.app, prev_status)
                self.app.custom_events.major_change = True
            return "found"
        else:
            return "not found"

    def quit_game(self, event, e_type, in_type, user_in, flag_value):
        if event.type == e_type or event.type == pg.QUIT:
            if in_type == 'button':
                event_in = event.button
            else:
                event_in = event.key
            if event_in == user_in:
                self.app.is_running = flag_value
            return "found"
        else:
            return "not found"

    def overlap_scene(self, event, e_type, in_type, user_in, flag):
        if event.type == e_type:
            if in_type == 'button':
                event_in = event.button
            else:
                event_in = event.key
            if event_in == user_in and self.app.scene.surfaces.flags[flag][0]:
                self.app.scene.surfaces.flags[flag] = [False, None, None]
            elif event_in == user_in and not self.app.scene.surfaces.flags[flag][0]:
                self.app.scene.surfaces.flags[flag] = [True, 0.1, "Update"]

    def sub_init_world(self):
        self.app.scene.surfaces.surf.main_game.init_world()


def events_catalog():
    catalog = {
        "other": {
            # name = [handle type, ban event, [conditions], [event.type, event.key, flag_names, flag_values]]
            "close_pause_menu": [
                "change_scene",  # Event handle to use for this custom event
                ["pause_menu", 1, int],  # Additional condition
                [pg.KEYDOWN, "key", pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, 1, "Update"],  # Event data
                                                                               [False, None, None]]],
                [True, "open_pause_menu", False],   # Event validity status and effect on other event status
            ],
            "open_pause_menu": [
                "change_scene",  # Event handle to use for this custom event
                ["main_game", 1, int],  # Additional condition
                [pg.KEYDOWN, "key", pg.K_ESCAPE, ["main_game", "pause_menu"], [[True, 2, "Frozen"],  # Event data
                                                                               [True, 1, "Update"]]],
                [True, "close_pause_menu", False],  # Event validity status and effect on other event status
            ],
            "emergency_quit": [
                "quit_game",  # Event handle to use for this custom event
                ["running", 0, int],  # Additional condition (trick to get always true)
                [pg.KEYDOWN, "key", [pg.K_LALT, pg.K_F4], False],  # Event data
                [True],  # Event validity status
            ],
            "debug_window": [
                "overlap_scene",  # Event handle to use for this custom event
                ["running", 0, int],  # Additional condition (trick to get always true)
                [pg.KEYDOWN, "key", pg.K_F1, "utility"],  # Event data
                [True],  # Event validity status
            ],
        },
        "main_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_play": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["main_game", "main_menu"], [[True, 1, "Update"],  # Event data
                                                                               [False, None, None]]],
                [True],  # Event validity status
            ],
            "button_continue": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["saves_menu", "main_menu"], [[True, 1, "Update"],  # Event data
                                                                                [False, None, None]]],
                [True],  # Event validity status
            ],
            "button_settings": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["settings_menu", "main_menu"], [[True, 1, "Update"],  # Event data
                                                                                   [False, None, None]]],
                [True],  # Event validity status
            ],
            # sprite = [handle type,[event.type, event.button, game_running]]
            "button_quit": [
                "quit_game",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, False],  # Event data
                [True],  # Event validity status
            ]
        },
        "pause_menu": {
            "button_return_main": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["pause_menu", "main_menu", "main_game"],  # Event data
                 [[False, None, None], [True, 1, "Update"], [False, None, None]]],
                [True],  # Event validity status
            ],
            "button_save": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["saves_menu", "pause_menu"], [[True, 1, "Update"],  # Event data
                                                                                 [False, None, None]]],
                [True],  # Event validity status
            ],
            "button_settings": [
                "change_scene",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, ["settings_menu", "pause_menu"], [[True, 1, "Update"],  # Event data
                                                                                    [False, None, None]]],
                [True],  # Event validity status
            ],
            "button_quit": [
                "quit_game",  # Event handle to use for this custom event
                [pg.MOUSEBUTTONDOWN, "button", 1, False],  # Event data
                [True],  # Event validity status
            ]

        },
        "main_game": {
            "init_game": [
                "init_world",  # Event handle to use for this custom event
            ]
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
        app.player.reset()


# Custom exceptions --
class SceneChanged(Exception):
    pass
