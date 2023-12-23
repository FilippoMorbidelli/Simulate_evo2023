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

        # Custom FPS event to update it every half second
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)

    def find_active_sprite(self, app, scene):  # Generalize function!!!
        try:
            for sprite in scene:
                try:
                    check_over = sprite.mask.get_at(app.mouse)
                except:
                    break
                if sprite.flag != check_over:
                    sprite.flag = check_over
                    if sprite.flag:
                        sprite.image = sprite.button_T  # Select sprite active
                        self.active_sprite = sprite.name  # Give sprite to event checker
                        break  # Break current search since over sprite has been found
                    elif not sprite.flag:
                        sprite.image = sprite.button_F  # Deselect sprite active
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
                for event in self.app.event_list:
                    # Secure "close game" event
                    if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                        self.app.is_running = False
            case str():
                for event in self.app.event_list:
                    # Secure "close game" event
                    if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                        self.app.is_running = False

                    # check for action/event in that sprite
                    event_data = self.catalog[self.master_scene][self.active_sprite]
                    event_to_check = getattr(EventTypes, event_data[0])
                    event_to_check(EventTypes, app, event, *event_data[1])


            # Quit game via button
            #self.is_running = mouse_evt(event, pg.MOUSEBUTTONDOWN, 1, False)


# Single events --------------------------------|
class EventTypes:
    def __init__(self):
        pass
    def key_evt(self, event, e_type, key, action, condition=True):
        # Handles keyboard events
        if event.type == e_type and event.key == key and condition:
            return action

    def mouse_evt(self, event, e_type, button, action, condition=True):
        # Handles mouse buttons events
        # event.button = [1, 2, 3, 4, 5] == [left, middle, right, scroll up, scroll down]
        if event.type == e_type and event.button == button and condition:
            return action

    def change_scene(self, app, event, etype, button, flag_name, flag_value):
        if event.type == etype and event.button == button:
            for action in range(len(flag_name)):
                app.scene.surfaces.flags[flag_name[action]] = flag_value[action]

    def quit_game(self, app, event, etype, button, flag_name, flag_value):  # TBD
        if event.type == etype and event.button == button:
            for action in range(len(flag_name)):
                app.scene.surfaces.flags[flag_name[action]] = flag_value[action]


def events_catalog():
    catalog = {
        "main_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_play": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["main_game", "main_menu"],
                                             [[True, "Master", "Update"], [False, "Null", "Null"]], ], ]
        },
        "pause_menu": {
            # sprite = [handle type,[event.type, event.button, flag_names, flag_values]]
            "button_return_main": ["change_scene", [pg.MOUSEBUTTONDOWN, 1, ["pause_menu", "main_menu"],
                                                    [[False, "Null", "Null"], [True, "Master", "Update"]], ], ]
        },
    }
    return catalog
