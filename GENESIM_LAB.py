# Evolution simulation project - GENESIM LAB 0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 20/11/2023
# Notes: Main module to run simulation game

# Import third party and game packages --------------
import genesim_lab.life as lf
import genesim_lab.world as wld
import genesim_lab.resources as rsc
import genesim_lab.settings as stg
import genesim_lab.genetic_db as gdb
import genesim_lab.graphic_interface as gph


# Main simulation-----------------------------------
def simulate():
    """Main simulation, here everything is contained"""

    # Settings and genome
    gen_settings = stg.sim_settings()
    init_genome = gdb.basic_genome()

    # Spawn creatures, grid and resources
    grid = wld.SimGrid(gen_settings)
    resources = rsc.Resources(gen_settings, grid.masks)
    #creatures = [Wildlife(gen_settings, grid, genome) for i in range(gen_settings['creatures']['spawn_creatures'])]

    # Simulation

        # Plot frame (save each step)
    #food_x = [item[0] for item in resources.food]
    #food_y = [item[1] for item in resources.food]
    #fig = go.Figure(data=[go.Heatmap(z=grid.grid), go.Scatter(x=food_x, y=food_y, mode='markers')])
    #fig.update_layout(yaxis=dict(scaleanchor='x', scaleratio=1))
    #fig.show()

        # Update inputs (perceive)

        # Update mind (think)

        # Update outputs (act)

    return


# Main ----------------------------------------------
if __name__ == '__main__':
    simulate()
