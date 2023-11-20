# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and game packages---------------


# Settings-------------------------------------------
def sim_settings():
    """ """

    # Values are reported in SI units if they have a dimension [m, s, kg, ...]
    settings = {
        'tick': 1,  # [s] tick conversion to seconds
        'x_min': -128,  # [m]
        'y_min': -128,  # [m]
        'x_max': 128,  # [m]
        'y_max': 128,  # [m]
        'terrain': {
            'shape': (256, 256),
            'resolution': (1, 1),
            'octaves': 6,
            'persistence': 0.5,
            'grass_ID': 1,
            'grass_RGB': [],
            'water_threshold': 0.2,
            'water_ID': 0,
            'water_RGB': [],
            'vegetation_ID': 2,
            'vegetation_RGB': [],
        },
        'resources': {
            'init_food_veg': 50,
            'init_food_grass': 10,
            'init_pond': 25,
            'food_max': 150,
            'pond_max': 75,
            'food_radius': 0.05,
            'pond_radius': 0.2,
            'food_sp_ticks': 2,
            'pond_sp_ticks': 10,
        },
        'creatures': {
            'spawn_creatures': 50,
        },
    }

    return settings

