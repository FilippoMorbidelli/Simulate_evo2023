# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, Engine, plot mode, ecc)

# Import packages ------------------------------|
from genesim_lab.Engine.scene.surfaces import *


# Main -----------------------------------------|
class Scene:
    # This class is just a middle man
    # Contains some data about scene and sprites
    def __init__(self, app):
        self.app = app
        self.sprite_util = {
            "SaveLoad" : "",
        }

        # Initialize surfaces logic
        self.surfaces = Surfaces(self.app)

    def update(self):
        self.surfaces.update_current_scene()
        # Check current scene and render proper scene
        # Main menu

        # Main Engine

    def render(self):
        self.surfaces.render_current_scene()
        # Render proper elements
