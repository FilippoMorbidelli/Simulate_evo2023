# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
# Import Third-Party
import multiprocessing as mp
import time
import re
import numpy as np

# From Third-Party
from pathlib import Path

# From Src
from src.Engine.saveLoadManager.saveManager import save_encoder

# All Processes to spawn -------------------------------|

# Processes on Save Chunks ----
class SaveProcess(mp.Process):

    def __init__(self, request_q, response_q):
        # Extend class
        super().__init__()

        # Init shared data
        self.rq_queue = request_q
        self.rsp_queue = response_q

        # Init other constant data
        self.app_path = Path(__file__).parent.parent.parent

    def run(self):
        while True:
            if self.rq_queue.empty():
                # Sleep
                time.sleep(1)
            else:
                # Retrieve data to process
                to_process = self.rq_queue.get()
                # Check if Kill command
                if to_process == "Kill":
                    self.terminate()
                else:
                    # Unwrap data
                    command, r_ids, r_vox, world_info, util = to_process

                    # Prepare save path
                    path = self.app_path / util.save_path / util.curr_save_name

                    # Save each region
                    for r in r_vox.keys():
                        r_name = asynch_name_from_index(world_info, r)
                        r_path = "World/" + r_name + ".npz"
                        with open(path / r_path, 'w+') as f:
                            voxels = save_encoder(r_vox[r])
                            np.savez_compressed(path / r_path, voxels)
                        # Load response of single region saved
                        self.rsp_queue.put(["Save", "InProgress", r])

                    # Load response to dedicated queue, process finished
                    self.rsp_queue.put(["Save", "Done", []])


# Functions called by Child Processes -----------------|
def asynch_save_region(region):
    pass

def asynch_name_from_index(info, region_index):
    # Get region coordinates from region index by inspecting a chunk
    y = region_index // (info.depth_rn * info.width_rn)
    z = (region_index - y * info.depth_rn * info.width_rn) // info.width_rn
    x = region_index - y * info.depth_rn * info.width_rn - z * info.width_rn

    r_name = "r_" + str(x) + "_" + str(y) + "_" + str(z)

    return r_name

def asynch_index_from_name(info, region_string):
    # Extract indexes from name and compute index to corresponding region
    x, y, z = re.findall(r'\d+', region_string)
    index = int(x) + info.width_rn * int(z) + info.width_rn * info.depth_rn * int(y)

    return index

# -- UNUSED FUNCTIONALITIES FOR MULTIPROCESSING
# -- THE MANAGER HAS BEEN CHOSEN TO BE DISCARDED DUE TO VERY LARGE OVERHEADS WHEN SHARING THE SETTINGS OF THE GAME
# -- SO TO EACH PROCESS THE SETTINGS ARE PASSED BY A QUEUE
#
# custom manager to support custom classes
# class CustomManager(BaseManager):
#     pass
#
# class TestProxy(BaseProxy):
#     _exposed_ = ('__getattribute__', '__setattr__', '__delattr__',)
#
#     def __getattr__(self, name):
#         return self._callmethod('__getattribute__', (name,))
#
#
# class SubProxy(BaseProxy):
#     _exposed_ = ('__getattribute__', '__setattr__', '__delattr__',)
#
#     def __getattr__(self, name):
#         return self._callmethod('__getattribute__', (name,))
#
#     def __setattr__(self, key, value):
#        if key.startswith('_'):
#            super().__setattr__(key, value)
#        else:
#            self._callmethod('__setattr__', (key, value))
#
# def init_manager_stg():
#     #Register to custom manager each class and subclass shared between processes
#     CustomManager.register('sh_settings', SharedGameSettings, TestProxy)
#     CustomManager.register('world'      , World       , SubProxy)
#     CustomManager.register('sim'        , Simulation  , SubProxy)
#     CustomManager.register('world_obj'  , WorldObj    , SubProxy)
#     CustomManager.register('interaction', Interaction , SubProxy)
#     CustomManager.register('window'     , Window      , SubProxy)
#     CustomManager.register('camera_data', CameraData  , SubProxy)
#     CustomManager.register('player_data', PlayerData  , SubProxy)
#     CustomManager.register('util'       , Util        , SubProxy)
#
#     # Init Manager
#     manager = CustomManager()
#     manager.start()
#
#     # Generate each subclass and then load main settings class
#     world       = manager.world()
#     simulation  = manager.sim()
#     world_obj   = manager.world_obj()
#     interaction = manager.interaction()
#     window      = manager.window()
#     camera_data = manager.camera_data()
#     player_data = manager.player_data()
#     util        = manager.util()
#
#     # Main settings class
#     shared_stg = manager.sh_settings(world, simulation,
#                                     world_obj, interaction, window,
#                                      camera_data, player_data, util)
#     # Generate Font util separately
#     stg = GameSettings()
#
#     return manager, shared_stg, stg

#@dataclass(slots=True, order=True)
# class SharedGameSettings:  # Main wrapped settings class
#     def __init__(self, world, simulation,
#                  world_obj, interaction, window,
#                  camera_data, player_data, util):
#         # Set from input each subclass since they need to be ProxyClass to support MultiProcessing
#         self.world       = world
#         self.sim         = simulation
#         self.world_obj   = world_obj
#         self.interaction = interaction
#         self.window      = window
#         self.camera      = camera_data
#         self.player      = player_data
#         self.util        = util
#
#         # Addition settings to compute after init
#         self.player.pos = glm.vec3(0, self.world.w_height * self.world.c_size * self.world.v_y / 2, 0)