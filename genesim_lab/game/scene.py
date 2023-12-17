# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, game, plot mode, ecc)

# Import packages ------------------------------|
import pygame as pg
from genesim_lab.game.settings import *
from genesim_lab.meshes.quad_mesh import QuadMesh
from genesim_lab.game.sprite import *


# Main -----------------------------------------|
class Scene:

    def __init__(self, app):
        self.app = app

        fps_counter = FpsSprite(app)
        util_text = UtilityStaticText(app, 'Genesim Lab - version alpha\nAuthor: F. Morbidelli\nTrial version', pg.Rect(1620, 0, 300, 100), "right")
        app.shader_prog_2D.utility.add(fps_counter)
        app.shader_prog_2D.utility.add(util_text)

        # Initialize main menu

        # Initialize quadrilateral
        self.quad = QuadMesh(self.app)

    def update(self):
        pass
        # Check current scene and render proper scene
        # Main menu

        # Main game

    def render(self):
        # Render always active elements
        self.app.shader_prog_2D.utility.draw2d()
        # Render proper elements
        self.quad.render()
