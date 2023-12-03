# Evolution simulation project - events module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles events and actions to compute

# Import packages ------------------------------|


# Main event handler ---------------------------|

# Single events --------------------------------|
def key_evt(event, e_type, key, value, condition=True):
    # Handles keyboard events
    if event.type == e_type and event.key == key and condition:
        return value


def mouse_evt(event, e_type, button, action, condition=True):
    # Handles mouse buttons events
    # event.button = [1, 2, 3, 4, 5] == [left, middle, right, scroll up, scroll down]
    if event.type == e_type and event.button == button and condition:
        return action
