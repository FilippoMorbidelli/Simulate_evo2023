# Evolution simulation project - GENESIM LAB v0.1
# Author: Filippo Morbidelli
# Created on: 31/07/2023
# Last update: 17/12/2023
# Notes: Main module to run simulation Engine

# Import third party and Engine packages ---------|
from genesim_lab.Engine.world_gen.sparsevoxeloctree import build_svo

import numpy as np
import threading
import time

# Game start -------------------------------------|
class LoadThread(threading.Thread):

    def __init__(self, app, t_queue):
        threading.Thread.__init__(self)
        self.app = app
        self.world = None
        self.queue = t_queue
        self.daemon = True

    def run(self):
        t_running = True

        while t_running:
            # Check if queue is empty
            if self.queue.empty():
                time.sleep(1)
                pass
            else:
                queue_data = self.queue.get()
                if queue_data == "Stop":
                    t_running = False
                else:
                    self.world = self.app.scene.surfaces.surf.main_game.world
                    r_id, r_index = queue_data
                    # Find if region is already existing
                    is_loaded = self.app.save_load.load_single_region(r_id)
                    # Create new
                    if not is_loaded:
                        # Build Chunk
                        self.world.voxels[r_id] = np.zeros([self.world.info.r_vol, self.world.info.c_vol], dtype='uint8')
                        self.world.chunks[r_id] = [None for _ in range(self.world.info.r_vol)]
                        self.world.build_chunks({r_id: r_index})
                        # Build Chunk Mesh
                        for chunk in self.world.chunks[r_id]:
                            if chunk is not None:
                                chunk.build_mesh_threaded()
                        # Build SVO
                        self.world.svo[r_id] = build_svo(self.app, self.world.info, self.world.chunks[r_id], r_index)
                    # Dequeue from mimic queue
                    self.world.mimic_load_q.pop(r_id)
                    self.world.mesh_load_q.append(r_id)


