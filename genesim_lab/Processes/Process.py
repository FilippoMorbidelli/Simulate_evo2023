# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
import multiprocessing as mp
import time

from multiprocessing.managers import BaseManager, BaseProxy
from genesim_lab.Engine.settings import *
from genesim_lab.Saves.SaveManager import asynch_load_region, asynch_save_region

# All Processes to spawn -------------------------------|
# custom manager to support custom classes
class CustomManager(BaseManager):
    pass

class TestProxy(BaseProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__',)

    def __getattr__(self, name):
        return self._callmethod('__getattribute__', (name,))


class SubProxy(BaseProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__',)

    def __getattr__(self, name):
        return self._callmethod('__getattribute__', (name,))

    def __setattr__(self, key, value):
       if key.startswith('_'):
           super().__setattr__(key, value)
       else:
           self._callmethod('__setattr__', (key, value))


class LoadProcess(mp.Process):

    def __init__(self, request_q, response_q, settings, voxels=None):
        # Extend class
        super().__init__()

        # Init shared data
        self.stg = settings # Share world settings
        self.voxels = voxels # Share world voxels (dict of np array)
        self.rq_queue = request_q
        self.rsp_queue = response_q

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
                    r_id = to_process
                    # Find if region is already existing
                    is_loaded, voxels = asynch_load_region(self.stg.util, self.stg.world, r_id)
                    # Create new region
                    chunk = [None for _ in range(self.stg.world.r_vol)]
                    if not is_loaded:
                        # Build Chunk
                        voxels = np.zeros([self.stg.world.r_vol, self.stg.world.c_vol], dtype='uint8')
                        self.world.build_chunks({r_id: r_index})
                    # Build Chunk Mesh
                    for chunk in self.world.chunks[r_id]:
                        if chunk is not None:
                            chunk.build_mesh_threaded()
                    # Build SVO
                    self.world.svo[r_id] = build_svo(self.app, self.world.info, self.world.chunks[r_id], r_index)

                    # Load response to dedicated queue (to be read by main process)
                    self.rsp_queue.put([result, voxels, chunk, svo])


# --
def init_manager_stg():
    #Register to custom manager each class and subclass shared between processes
    CustomManager.register('sh_settings', SharedGameSettings, TestProxy)
    CustomManager.register('world'      , World       , SubProxy)
    CustomManager.register('sim'        , Simulation  , SubProxy)
    CustomManager.register('world_obj'  , WorldObj    , SubProxy)
    CustomManager.register('interaction', Interaction , SubProxy)
    CustomManager.register('window'     , Window      , SubProxy)
    CustomManager.register('camera_data', CameraData  , SubProxy)
    CustomManager.register('player_data', PlayerData  , SubProxy)
    CustomManager.register('util'       , Util        , SubProxy)

    # Init Manager
    manager = CustomManager()
    manager.start()

    # Generate each subclass and then load main settings class
    world       = manager.world()
    simulation  = manager.sim()
    world_obj   = manager.world_obj()
    interaction = manager.interaction()
    window      = manager.window()
    camera_data = manager.camera_data()
    player_data = manager.player_data()
    util        = manager.util()

    # Main settings class
    shared_stg = manager.sh_settings(world, simulation,
                                    world_obj, interaction, window,
                                     camera_data, player_data, util)
    # Generate Font util separately
    stg = GameSettings()

    return manager, shared_stg, stg