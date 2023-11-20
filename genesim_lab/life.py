# Evolution simulation project - life module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: This module contains every class and function needed by the main simulation to generate the creatures

# Import packages------------------------------------
import numpy as np
import numpy.random as rnd
from torch import nn


# Life types----------------------------------------
class MacroLife:
    def __init__(self, stg, grid, genome, name=None):

        # Initialize attributes
        self.genome = type("Current genome of wildlife", (), {})()
        self.parameters = type("Current parameters of wildlife", (), {})()
        self.inputs = type("Current inputs of wildlife mind", (), {})()
        self.outputs = type("Current parameters of wildlife", (), {})()

        # General parameters and genome of wildlife
        self.parameters.xy = np.array([rnd.uniform(stg['x_min'], stg['x_max']),
                                       rnd.uniform(stg['y_min'], stg['y_max'])])   # XY position on grid
        self.parameters.curr_v = 0  # Current velocity
        self.parameters.dir = np.random.uniform(-1, 1)  # Head direction
        self.parameters.age = 0
        self.parameters.grid_pos, self.parameters.grid_pos_ID = check_grid_coord(self.parameters.xy, grid, stg)
        self.parameters.food_dist = 0  # Distance to nearest food (needed for collision check)
        self.parameters.water_dist = 0  # Distance to nearest source of water
        self.parameters.mate_dist = 0  # Distance to nearest mate
        self.parameters.prm_ID = ''
        self.parameters.wl_ID = ''

        self.genome.v = genome['cng']['max_vel']  # Max velocity each step [m]
        self.genome.age_death = genome['cng']['max_age']
        self.genome.sex = np.round(np.random.uniform(0, 1))  # Gender assignment [0 = male, 1 = female]
        self.genome.sight = genome['cng']['sight_distance']

        # Genome links and weights
        self.genome.w_ih = genome['fix']['weights']['w_ih']  # Weights from input to hidden [-5, 5]
        self.genome.w_ho = genome['fix']['weights']['w_ho']  # Weights from hidden to output [-5, 5]
        self.genome.w_io = genome['fix']['weights']['w_io']  # Weights from input to output [-5, 5]

        # Action and general parameters
        self.parameters.energy = genome['cng']['spawn_energy']  # Energy level
        self.parameters.water = genome['cng']['spawn_water']  # Water level
        self.genome.energy_loss = genome['cng']['en_tick_loss']  # Energy consumed each tick
        self.genome.water_loss = genome['cng']['wt_tick_loss']  # Energy consumed each tick
        self.genome.repr_cost = genome['cng']['repr_cost']  # Energy used for reproduction
        self.genome.en_max = genome['cng']['max_energy']  # Maximum food level
        self.genome.wt_max = genome['cng']['max_water']  # Maximum water level

        # Sensor (inputs of mind)
        self.inputs.sense_food = 0  # Sense nearest food direction wrt heading [-180, 180] - [-1, 1]
        self.inputs.need_food = 1  # Scaling factor when hungry [input to mind] [0, 1]
        self.inputs.sense_water = 0  # Sense nearest water direction wrt heading [-180, 180] - [-1, 1]
        self.inputs.need_water = 1  # Scaling factor when thirsty [input to mind] [0, 1]
        self.inputs.sense_repr = 0  # Sense nearest mate wrt heading [-180, 180] - [-1, 1]
        self.inputs.need_repr = 1  # Scaling factor when "in heat" [input to mind] [0, 1]
        self.inputs.prm_nearby = 0  # Sense near pheromone if any [-1, 1]
        self.inputs.age_level = 0  # Scaling factor with age [0, 1]
        self.inputs.pop_level = 0  # Factor with population level nearby [0 - N]

        self.inputs.inputs = np.array([self.inputs])  # Input values that goes into mind function

        # Possible actions (outputs of mind)
        self.outputs.eat = 0  # Probability of eating action [0, 1]
        self.outputs.drink = 0  # Probability of drinking action [0, 1]
        self.outputs.release_prm = 0  # Quantity of pheromone released [0, 1]
        self.outputs.reproduce = 0  # Probability of reproducing action [0, 1]
        self.outputs.move_dir = 0  # Moving direction wrt heading (forward or backward) [0, 360]
        self.outputs.move_qt = 0  # Quantity of movement (right or left rotation) [-1, 1]
        self.outputs.move_random = 0  # Probability of random movement [0, 1]

        self.outputs.outputs = np.array([self.outputs])  # Out values that comes from mind function

        # Useful trace parameters
        self.parameters.eating = False  # Determine if creature eats or not [False - True]
        self.parameters.drinking = False  # Determine if creature drinks or not [False - True]
        self.parameters.reproducing = False  # Determine if creature is reproducing or not [False - True]
        self.parameters.task = False  # Determine if creature is occupied or free [False - True]

        # Other parameters
        self.name = name  # Name of the creature
        self.RGB = np.random.uniform(0, 256, 3)  # Color of the creature
        self.ID = 111  # TDB ID of creature (should contain generation, sex and genome)

    # NEURAL NETWORK
    def think(self):

        # MLP
        def af(x):
            return np.tanh(x)  # Activation function hyperbolic tangent
        h1 = af(np.matmul(self.genome.wg_h, self.inputs.inputs))  # Hidden layer
        out = af(np.matmul(self.genome.wg_o, h1) + np.matmul(self.genome.wg_d, self.inputs.inputs))  # Outputs
        self.outputs.outputs = out

        # Read and replace outputs
        (self.outputs.eat, self.outputs.drink, self.outputs.release_prm, self.outputs.reproduce, self.outputs.move_dir,
         self.outputs.move_qt, self.outputs.move_random) = out

    def update_inputs(self, res, creatures):

        # Update food
        check_food = np.argmin(np.linalg.norm(res.food - self.parameters.xy))
        if check_food < self.genome.sight:
            self.parameters.food_dist = np.linalg.norm(res.food[check_food] - self.parameters.xy)
            dist = res.food[check_food] - self.parameters.xy
            self.inputs.sense_food = np.arctan2(dist[1], dist[0])/180  # Update perceived nearest food direction
        else:
            self.parameters.food_dist = 100
            self.inputs.sense_food = rnd.uniform(-1, 1)  # Update no food seen, creature has straight input
        self.inputs.need_food = (self.genome.en_max - self.parameters.energy) / self.genome.en_max  # Update hunger

        # Update water
        check_wt = np.argmin(np.linalg.norm(res.water - self.parameters.xy))
        if check_wt < self.genome.sight:
            self.parameters.water_dist = np.linalg.norm(res.water[check_wt] - self.parameters.xy)
            dist = res.water[check_wt] - self.parameters.xy
            self.inputs.sense_water = np.arctan2(dist[1], dist[0]) / 180  # Update perceived nearest water direction
        else:
            self.parameters.water_dist = 100
            self.inputs.sense_water = rnd.uniform(-1, 1)  # Update no water seen, creature has straight input
        self.inputs.need_water = (self.genome.wt_max - self.parameters.energy) / self.genome.wt_max  # Update thirst

        # Update mates
        check_mate = np.argmin(np.linalg.norm(creatures - self.parameters.xy))
        if check_mate < self.genome.sight:
            self.parameters.mate_dist = np.linalg.norm(creatures[check_mate] - self.parameters.xy)
            dist = creatures[check_mate] - self.parameters.xy
            self.inputs.sense_repr = np.arctan2(dist[1], dist[0]) / 180  # Update perceived nearest mate direction
        else:
            self.parameters.mate_dist = 100
            self.inputs.sense_repr = rnd.uniform(-1, 1)  # Update no mate seen, creature has straight input
        self.inputs.need_repr = (self.parameters.food + self.parameters.water - 2000) / 1000  # Update "heat" level

        # Update follow pheromone (TBD)
        #self.inputs.prm_nearby =  0# Update perceived nearest pherormone direction

        # Update age level
        self.inputs.age_level = self.parameters.age / self.genome.age_death  # Scaling factor with age [0, 1]

        # Update perceived population nearby (sense of crowding)
        check_total_mate = np.sum(np.linalg.norm(creatures - self.parameters.xy))
        self.inputs.pop_level = check_total_mate/(np.pi * self.genome.sight**2)  # Factor with population level nearby

        # Save updated inputs
        self.inputs.inputs = np.array([self.inputs])

    def update_outputs(self, stg):

        # Generate random threshold to determine actions
        threshold = np.random.uniform(0, 1)  # Tick probability to determine if threshold is reached or not

        # Select action to be taken and update heading, velocity and position
        if not self.parameters.task:  # If pass just walk
            if threshold < self.outputs.move_random:
                # Update randomly head direction
                self.parameters.dir = np.random.uniform(-1, 1)
                drt = self.parameters.dir
                # Update randomly current velocity
                self.parameters.curr_v += self.genome.v*np.random.uniform(-0.25, 0.25)
                self.parameters.curr_v = out_of_bound(self.parameters.curr_v, 0, self.genome.v)
                # Update position
                self.parameters.xy += self.parameters.curr_v * stg['tick'] * [np.cos(drt), np.sin(drt)]
                self.parameters.xy[0] = out_of_bound(self.parameters.xy[0], stg['x_min'], stg['x_max'])
                self.parameters.xy[1] = out_of_bound(self.parameters.xy[1], stg['y_min'], stg['y_max'])
            else:  # Update movement as output of think
                # Update head direction
                self.parameters.dir = self.outputs.move_dir
                drt = self.parameters.dir
                # Update current velocity
                self.parameters.curr_v += self.genome.v * self.outputs.move_qt
                self.parameters.curr_v = out_of_bound(self.parameters.curr_v, 0, self.genome.v)
                # Update position
                self.parameters.xy += self.parameters.curr_v * stg['tick'] * [np.cos(drt), np.sin(drt)]
                self.parameters.xy[0] = out_of_bound(self.parameters.xy[0], stg['x_min'], stg['x_max'])
                self.parameters.xy[1] = out_of_bound(self.parameters.xy[1], stg['y_min'], stg['y_max'])
        #else:  # Perform action

    def reproduction(self):

        a = 2


class Mind1(nn.Module):
    def __init__(self, in_n, ly1, out_n):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(in_n, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
        )

    def forward(self, x):
        x = self.flatten(x)
        actions = self.linear_relu_stack(x)
        return actions


# Utility functions---------------------------------
def out_of_bound(x, low_lim, up_lim):
    """Check and correct out of bound condition of input value, given the lower and upper limit"""

    if x < low_lim:
        x = low_lim  # Set x value to lower limit
    elif x > up_lim:
        x = up_lim  # Set x value to upper limit

    return x


def check_grid_coord(pos, grid, stg):
    # ATTENTION: pos = [x, y], grid = [y, x]

    # Retrieve grid id from real position
    pos = np.flip(int(pos + np.array([0, 1])), axis=1)
    pos[:, 0] = - pos[:, 0]
    pos[:, 0] = pos[:, 0] + stg['terrain']['shape'][0] / 2
    pos[:, 1] = pos[:, 1] + stg['terrain']['shape'][1] / 2
    coord = pos
    grid_id = grid.grid[coord]

    return np.array([coord, grid_id])
