# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


# World generator ------------------------------|
class Chunk:

    def __init__(self, app):
        self.app = app
        self.voxels: np.array = self.build_voxels()

    def build_voxels(self):
        # Empty chunk
        voxels = np.zeros(game_stgs['world']['chunk_vol'], dtype='uint8')
        