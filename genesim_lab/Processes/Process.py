# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
import multiprocessing as mp
import time
from multiprocessing.managers import BaseManager, BaseProxy

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

    def __init__(self, queue, settings, voxels=None):
        # Extend class
        super().__init__()

        # Init shared data
        self.stg = settings # Share world settings
        self.voxels = voxels # Share world voxels (dict of np array)
        self.queue = queue

    def run(self):
        while True:
            if self.queue.empty():
                # Sleep
                time.sleep(1)
            else:
                # Retrieve data to process
                to_process = self.queue.get()
                # Check if Kill command
                if to_process == "Kill":
                    self.terminate()
                else:
                    # Unwrap data
                    r_id, r_index = to_process
                    # Find if region is already existing
                    is_loaded = self.app.save_load.load_single_region(r_id)
                    # Create new
                    if not is_loaded:
                        # Build Chunk
                        self.world.voxels[r_id] = np.zeros([self.world.info.r_vol, self.world.info.c_vol],
                                                           dtype='uint8')
                        self.world.chunks[r_id] = [None for _ in range(self.world.info.r_vol)]
                        self.world.build_chunks({r_id: r_index})
                        # Build Chunk Mesh
                        for chunk in self.world.chunks[r_id]:
                            if chunk is not None:
                                chunk.build_mesh_threaded()
                        # Build SVO
                        self.world.svo[r_id] = build_svo(self.app, self.world.info, self.world.chunks[r_id], r_index)

