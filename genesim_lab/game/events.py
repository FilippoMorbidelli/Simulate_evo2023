# Evolution simulation project - events module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles events and actions to compute

# Import packages ------------------------------|
import pygame as pg


# Main event handler ---------------------------|
class EventHandler:
    def __init__(self, app):
        self.app = app
        self.active_sprite = None
        self.active_scene = None
        self.catalog = events_catalog()

        # FPS event to update it every second only
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)

    def handle_events(self, app):
        app.scene.surfaces.handle_current_scene()  # Define active scene flags
        for act_surf in app.scene.surfaces.active:  # Manage multiple scene at the same time TBC!!
            scene = app.scene.surfaces.handle[act_surf]
            if scene is None or act_surf == "utility":
                pass
            else:
                self.active_scene = act_surf
                find_active_sprite(app, scene)

        if self.active_sprite is None:
            for event in self.app.event_list:
                # Secure "close game" event
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                    self.app.is_running = False
        else:
            for event in self.app.event_list:
                # Secure "close game" event
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                    self.app.is_running = False

                # check for action/event in that sprite
                event_data = self.catalog[self.active_scene][self.active_sprite]
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

    def change_screen(self, app, event, etype, button, flag_name, flag_value):
        if event.type == etype and event.button == button:
            app.scene.surfaces.flags[flag_name] = flag_value


def find_active_sprite(app, scene):  # Generalize function!!!
    for sprite in scene:
        try:
            check_over = sprite.mask.get_at(app.mouse)
        except:
            break
        if sprite.flag != check_over:
            sprite.flag = check_over
            if sprite.flag:
                sprite.image = sprite.button_T  # Select sprite active
                app.custom_events.active_sprite = sprite.name  # Give sprite to event checker
                break  # Break current search since over sprite has been found
            elif not sprite.flag:
                sprite.image = sprite.button_F  # Deselect sprite active
                app.custom_events.active_sprite = None  # No active over sprite


def events_catalog():
    catalog = {
        "main_menu": {
            # sprite = [handle type,[event.type, event.button, flag_name, flag_value]]
            "button_play": ["change_screen", [pg.MOUSEBUTTONDOWN, 1, "main_game", True]]
        },
    }
    return catalog
