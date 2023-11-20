# Evolution simulation project - world generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: this module contains every class and function needed by the main simulation to generate the creatures

# Import packages------------------------------------
import numpy as np
import numpy.random as rnd


# Resources-----------------------------------------
class Resources:
    def __init__(self, settings, masks):

        # Spawn initial food on vegetation
        size_veg_mask = int(np.size(masks.veg_mask) / 2)
        veg_f_ind = rnd.choice(size_veg_mask, size=settings['resources']['init_food_veg'], replace=True)
        veg_f_grid = masks.veg_mask[veg_f_ind]
        self.food = np.hstack((rnd.uniform(veg_f_grid[:, 1], veg_f_grid[:, 1] - 1).reshape(-1, 1),
                               rnd.uniform(veg_f_grid[:, 0], veg_f_grid[:, 0] + 1).reshape(-1, 1))).tolist()

        # Spawn initial food on grass
        size_grs_mask = int(np.size(masks.grass_mask) / 2)
        grs_f_ind = rnd.choice(size_grs_mask, size=settings['resources']['init_food_grass'], replace=True)
        grs_f_grid = masks.grass_mask[grs_f_ind]
        self.food.append(np.hstack((rnd.uniform(grs_f_grid[:, 1], grs_f_grid[:, 1] - 1).reshape(-1, 1),
                                    rnd.uniform(grs_f_grid[:, 0], grs_f_grid[:, 0] + 1).reshape(-1, 1))).tolist())

        # Spawn initial ponds on grass
        size_pnd_mask = int(np.size(masks.grass_mask) / 2)
        pnd_f_ind = rnd.choice(size_pnd_mask, size=settings['resources']['init_pond'], replace=True)
        pnd_f_grid = masks.grass_mask[pnd_f_ind]
        self.pond = np.hstack((rnd.uniform(pnd_f_grid[:, 1], pnd_f_grid[:, 1] - 1).reshape(-1, 1),
                               rnd.uniform(pnd_f_grid[:, 0], pnd_f_grid[:, 0] + 1).reshape(-1, 1))).tolist()

    def spawn_resource(self, r_type, where, n, masks, settings):
        # r_type: 0 = food, 1 = pond
        # where: 0 = water, 1 = grass, 2 = vegetation
        # n: number of resources to spawn

        if r_type == 0:  # Spawn food
            food_n_check = np.size(self.food)
            if food_n_check < settings['resources']['food_max']:
                match where:
                    case 0:
                        mask = masks.water_mask
                    case 1:
                        mask = masks.grass_mask
                    case 2:
                        mask = masks.veg_mask
                    case _:
                        mask = np.array([0, 0])
                size_mask = int(np.size(mask) / 2)
                res_ind = rnd.choice(size_mask, size=n, replace=True)
                res_grid = mask[res_ind]
                self.food.extend(np.hstack((rnd.uniform(res_grid[:, 1], res_grid[:, 1] - 1).reshape(-1, 1),
                                            rnd.uniform(res_grid[:, 0], res_grid[:, 0] + 1).reshape(-1, 1))).tolist())
        elif r_type == 1:  # Spawn pond
            pond_n_check = np.size(self.pond)
            if pond_n_check < settings['resources']['pond_max']:
                mask = masks.grass_mask
                size_mask = int(np.size(mask) / 2)
                res_ind = rnd.choice(size_mask, size=n, replace=True)
                res_grid = mask[res_ind]
                self.pond.extend(np.hstack((rnd.uniform(res_grid[:, 1], res_grid[:, 1] - 1).reshape(-1, 1),
                                            rnd.uniform(res_grid[:, 0], res_grid[:, 0] + 1).reshape(-1, 1))).tolist())

    def remove_resource(self, r_type, r_coord):
        # r_type: 0 = food, 1 = pond

        if r_type == 0:  # Remove food
            self.food.remove(r_coord)
        elif r_type == 1:  # Remove pond
            self.pond.remove(r_coord)

