# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *


# Import packages ------------------------------|
class WorldClock:

    def __init__(self, world):
        self.app = world.app
        self.speedup = self.app.stg.world_obj.speedup
        self.revolution = self.app.stg.world_obj.revolution

        self.delta = self.app.delta_time
        self.second = 0
        self.minute = 0
        self.hour = 6
        self.day = 1
        self.month = 1
        self.year = 1

    def update_time(self):
        self.delta = self.app.delta_time * self.speedup
        self.second += self.delta

        if self.second >= 60:
            self.second -= 60
            self.minute += 1
            if self.minute >= 60:
                self.minute -= 60
                self.hour += 1
                if self.hour >= 24:
                    self.hour -= 24
                    self.day += 1
                    if self.day > 30:
                        self.day -= 30
                        self.month += 1
                        if self.month > 12:
                            self.month -= 12
                            self.year += 1






