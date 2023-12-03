# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, game, plot mode, ecc)

# Import packages ------------------------------|
from genesim_lab.game.settings import *
from genesim_lab.meshes.quad_mesh import QuadMesh


# Main -----------------------------------------|
class Scene:

    def __init__(self, app):
        self.app = app
        # Initialize quadrilateral
        self.quad = QuadMesh(self.app)

    def update(self):
        pass

    def render(self):
        self.quad.render()
