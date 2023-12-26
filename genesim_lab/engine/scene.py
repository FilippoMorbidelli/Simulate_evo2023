# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, engine, plot mode, ecc)

# Import packages ------------------------------|
from genesim_lab.engine.surfaces import *


# Main -----------------------------------------|
class Scene:

    def __init__(self, app):
        self.app = app

        # Initialize surfaces logic
        self.surfaces = Surfaces(self.app)

    def update(self):
        self.surfaces.update_current_scene()
        # Check current scene and render proper scene
        # Main menu

        # Main engine

    def render(self):
        self.surfaces.render_current_scene()
        # Render proper elements
