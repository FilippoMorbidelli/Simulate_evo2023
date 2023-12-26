# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and engine packages---------------
import numpy as np
import numpy.random as rnd


# Genome DataBase------------------------------------
def basic_genome():

    # The basic genome implemented is reported as dictionary
    genome = {
        'fix': {  # Fixed genome, cannot change randomly
            'num_inputs': 9,  # Number of creature mind inputs
            'num_hidden': 5,  # Number of creature mind hidden neurons
            'num_outputs': 7,  # Number of creature mind outputs
            'weights': {
                'w_ih': rnd.uniform(low=-1 / np.sqrt(9), high=1 / np.sqrt(9), size=[9, 5]),
                'w_ho': rnd.uniform(low=-1 / np.sqrt(5), high=1 / np.sqrt(5), size=[5, 7]),
                'w_io': rnd.uniform(low=-1 / np.sqrt(9), high=1 / np.sqrt(9), size=[9, 7])
            },
        },
        'cng': {  # Changeable genome through evolution
            'max_vec': 1,  # Max velocity that a creature can make in a tick [m]
            'max_age': 500,  # Max number of ticks the creature can survive
            'num_sex': 2,  # Number of allowed sexes
            'spawn_energy': 1000,
            'spawn_water': 1000,
            'en_loss_tick': 2,
            'wt_loss_tick': 3,
            'repr_cost': 500,
            'max_energy': 1500,
            'max_water': 1500,
            'num_child': 1,
            'pref_same_genome': 1,
            'sight_distance': 10  # [m]
        },
    }
    return genome
