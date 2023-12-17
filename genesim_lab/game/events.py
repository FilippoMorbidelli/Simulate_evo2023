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

        # FPS event to update it every second only
        self.FPS_EVENT = pg.USEREVENT + 1
        pg.time.set_timer(self.FPS_EVENT, 500)

    def check_events(self):
        for event in self.app.event_list:
            # Secure "close game" event
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_LALT and event.key == pg.K_F4):
                self.app.is_running = False
            # Quit game via button
            #self.is_running = mouse_evt(event, pg.MOUSEBUTTONDOWN, 1, False)


# Single events --------------------------------|
def key_evt(event, e_type, key, action, condition=True):
    # Handles keyboard events
    if event.type == e_type and event.key == key and condition:
        return action


def mouse_evt(event, e_type, button, action, condition=True):
    # Handles mouse buttons events
    # event.button = [1, 2, 3, 4, 5] == [left, middle, right, scroll up, scroll down]
    if event.type == e_type and event.button == button and condition:
        return action
