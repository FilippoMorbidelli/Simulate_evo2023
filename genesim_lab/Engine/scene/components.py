# Evolution simulation project -
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes:

# Import packages ------------------------------------------------------------------------------------------------------
from genesim_lab.Engine.world_gen.world import World
import numpy as np


# Scene Advanced Components --------------------------------------------------------------------------------------------
class WorldMainMenu(World):
    def __init__(self, app):
        super().__init__(app)
        self.chunks: list = [None for _ in range(4)]

    def build_chunks(self):
        chunks = np.load()
        self.chunks = chunks