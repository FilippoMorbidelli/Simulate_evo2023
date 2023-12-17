# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, game, plot mode, ecc)

# Import packages ------------------------------|
import pygame as pg
from genesim_lab.game.settings import *
from genesim_lab.game.surfaces import *
from genesim_lab.meshes.quad_mesh import QuadMesh
from genesim_lab.game.sprite import *
from genesim_lab.game.shader_program import ShaderProgram


# Main -----------------------------------------|
class Scene:

    def __init__(self, app):
        self.app = app

        # Initialize surfaces logic
        self.surfaces = Surfaces(self.app)

        # Initialize quadrilateral
        self.quad = QuadMesh(self.app)

    def update(self):
        self.surfaces.update_current_scene()
        self.app.shader_prog_3D.update()
        # Check current scene and render proper scene
        # Main menu

        # Main game

    def render(self):
        self.surfaces.render_current_scene()
        # Render proper elements
        self.quad.render()
