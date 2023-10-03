# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:
import random

# Import packages -----------------------------------
import numpy as np
import scipy as sc
import numpy.random as rnd
import plotly.graph_objects as go


# Class definition ----------------------------------
class Wildlife:
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


class SimGrid:
    def __init__(self, settings):

        # Preallocate attributes
        self.masks = type("Terrain masks", (), {})()

        # Preallocate grid
        n = settings['terrain']['shape']
        grid = np.ones(n, dtype=np.int32)

        # Compute noise
        noise = fractal_noise(settings)
        noise = (noise - noise.min()) / (noise.max() - noise.min())

        # Generate water
        threshold = settings['terrain']['water_threshold']
        grid[noise < threshold] = settings['terrain']['water_ID']

        # Generate vegetation
        potential = ((noise - threshold) / (1 - threshold)) ** 4 * 0.7
        mask = (noise > threshold) * (rnd.rand(n[0], n[1]) < potential)
        grid[mask] = settings['terrain']['vegetation_ID']
        self.grid = grid

        # Extract terrain masks
        veg_mask = np.argwhere(mask)
        veg_mask[:, 0] = veg_mask[:, 0] - n[0]/2  # change y values (on rows)
        veg_mask[:, 0] = - veg_mask[:, 0]
        veg_mask[:, 1] = veg_mask[:, 1] - n[1]/2  # change x values (on columns)
        self.masks.veg_mask = veg_mask

        grass_mask = np.argwhere(grid == 1)
        grass_mask[:, 0] = grass_mask[:, 0] - n[0] / 2
        grass_mask[:, 0] = - grass_mask[:, 0]
        grass_mask[:, 1] = grass_mask[:, 1] - n[1] / 2
        self.masks.grass_mask = grass_mask

        water_mask = np.argwhere(grid == 0)
        water_mask[:, 0] = water_mask[:, 0] - n[0] / 2
        water_mask[:, 0] = - water_mask[:, 0]
        water_mask[:, 1] = water_mask[:, 1] - n[1] / 2
        self.masks.water_mask = water_mask


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
        self.food.extend(np.hstack((rnd.uniform(grs_f_grid[:, 1], grs_f_grid[:, 1] - 1).reshape(-1, 1),
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


# Grid generation functions-------------------------
def generate_perlin_noise_2d(shape, res):

    f = lambda tt: 6 * tt ** 5 - 15 * tt ** 4 + 10 * tt ** 3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1

    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)

    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)

    # Interpolation
    t = f(grid)
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)


def fractal_noise(settings):

    # Get grid settings
    shape = settings['terrain']['shape']
    res = settings['terrain']['resolution']
    octaves = settings['terrain']['octaves']
    persistence = settings['terrain']['persistence']

    # Compute fractal noise
    noise = np.zeros(shape)
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        noise += amplitude * generate_perlin_noise_2d(shape, (frequency * res[0], frequency * res[1]))
        frequency *= 2
        amplitude *= persistence
    return noise


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


# Utility functions---------------------------------
def out_of_bound(x, low_lim, up_lim):
    """Check and correct out of bound condition of input value, given the lower and upper limit"""

    if x < low_lim:
        x = low_lim  # Set x value to lower limit
    elif x > up_lim:
        x = up_lim  # Set x value to upper limit

    return x


# Settings and genome-------------------------------
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


# Main simulation-----------------------------------
def simulate():
    """Main simulation, here everything is contained"""

    # Settings and genome
    gen_settings = sim_settings()
    init_genome = basic_genome()

    # Spawn creatures, grid and resources
    grid = SimGrid(gen_settings)
    resources = Resources(gen_settings, grid.masks)
    #creatures = [Wildlife(gen_settings, grid, genome) for i in range(gen_settings['creatures']['spawn_creatures'])]

    # Simulation

        # Plot frame (save each step)
    food_x = [item[0] for item in resources.food]
    food_y = [item[1] for item in resources.food]
    fig = go.Figure(data=[go.Heatmap(z=grid.grid), go.Scatter(x=food_x, y=food_y, mode='markers')])
    fig.update_layout(yaxis=dict(scaleanchor='x', scaleratio=1))
    fig.show()

        # Update inputs (perceive)

        # Update mind (think)

        # Update outputs (act)

    return


# Main ----------------------------------------------
if __name__ == '__main__':
    simulate()
