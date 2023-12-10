# Evolution simulation project - scene module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Contains all renders in the varius scenes (main menu, options, game, plot mode, ecc)

# Import packages ------------------------------|
import pygame as pg
from genesim_lab.game.settings import *
from genesim_lab.meshes.quad_mesh import QuadMesh


# Main -----------------------------------------|
class Scene:

    def __init__(self, app):
        self.app = app
        # Initialize pygame surface on which 2D textures are applied
        self.support_surface = pg.Surface((1920, 1080), pg.SRCALPHA)
        # Initialize always present features --> fps counter, version info
        fps = self.support_surface.blit(pg.font.SysFont('Verdana', 20).render(f'{app.clock.get_fps() :.0f}',
                                                                    True, (255, 255, 255)), (0, 0))
        self.app.shader_program_2D.add(self.support_surface)

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
        self.app.shader_program_2D.draw2d()
        # Render proper elements
        self.quad.render()
