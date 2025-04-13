# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
import multiprocessing as mp
import time
import re
import numpy as np

from pathlib import Path
from numba import types
from numba.typed import Dict
from concurrent.futures import ThreadPoolExecutor

from genesim_lab.Engine.sl_manager.SaveManager import load_decoder, save_encoder
from genesim_lab.Meshes.chunk_mesh_builder import build_chunk_mesh, let_settings_global, define_globals
from genesim_lab.Engine.world_gen.chunk import ChunkProxy

# All Processes to spawn -------------------------------|

# Processes ----
class LoadProcess(mp.Process):

    def __init__(self, request_q, response_q):
        # Extend class
        super().__init__()

        # Init shared data
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
                    command, Regions, r_coord, w_vox, world_info, util = to_process

                    # Compute specialized settings
                    stg = (world_info.depth_rn, world_info.width_rn, world_info.height_rn, world_info.w_width,
                           world_info.w_height, world_info.w_width, world_info.r_size, world_info.r_area)

                    send_iter = max(2, world_info.r_vol/16)

                    # Create NJit dict with already known voxels
                    voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])
                    for r_key, vox in w_vox.items():
                        voxels[r_key] = vox

                    for r in Regions:
                        # If region already exists load it (only voxels)
                        is_loaded, l_voxels = asynch_load_region(util, world_info, r)

                        # Build Chunks
                        voxels[r] = np.zeros([world_info.r_vol, world_info.c_vol], dtype='uint8')
                        if not is_loaded:
                            asynch_build_chunks(voxels, {r: r_coord[r]}, stg, world_info, new=True)
                        else:
                            asynch_build_chunks(voxels, l_voxels, stg, world_info, new=False)

                        # Send response to signal that loading has been initialized
                        self.rsp_queue.put(["Load", "Init", [r, voxels[r]]])

                    # Define globals to be used by voxel mesh creator
                    define_globals()
                    let_settings_global(world_info)

                    # Build Chunks Mesh for each region
                    format_size = [sum(int(fmt[:1]) for fmt in '1u4'.split()) for _ in range(8)]
                    for r in Regions:
                        # Vox meshes dict (to send)
                        vox_meshes = dict()
                        vox_meshes_greedy = dict()

                        # Loop over 8 chunks each
                        for cc in range(int(world_info.r_vol/8)):

                            # Create ThreadPool to compute 8 chunks in parallel
                            with ThreadPoolExecutor(max_workers=8) as executor:
                                # Compute inputs for each task
                                ccIds = cc * 8 + np.linspace(0,7,8, dtype='uint32')
                                voxArray = voxels[r][ccIds]
                                regionPos = [np.asarray(r_coord[r]) for _ in range(8)]

                                # Compute Chunk Pos
                                chunkPos = []
                                for c in ccIds:
                                    y = c // world_info.r_area
                                    x = (c - y * world_info.r_area) & world_info.rMask
                                    z = (c - y * world_info.r_area) // world_info.r_size
                                    chunkPos.append((x, y, z))

                                # Submit Tasks
                                futures = [executor.submit(build_chunk_mesh, Vox, FormatS, cPos, rPos, voxels)
                                           for Vox, FormatS, cPos, rPos in zip(voxArray, format_size, chunkPos, regionPos)
                                           ]

                                # Get Results
                                for c in range(8):
                                    mesh, meshGreedy = futures[c].result()
                                    vox_meshes[ccIds[c]] = mesh
                                    vox_meshes_greedy[ccIds[c]] = meshGreedy

                            self.rsp_queue.put(["Load", "InProgress", [r, r_coord[r], vox_meshes, vox_meshes_greedy]])

                        # Load response to confirm computation of new region has ended
                        self.rsp_queue.put(["Load", "DoneRegion", [r, r_coord[r]]])

                    # Load response to confirm computation of new region has ended
                    if command == "InitWorld":
                        self.rsp_queue.put(["Load", "InitDone", []])
                    else:
                        self.rsp_queue.put(["Load", "Done", []])


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
def asynch_build_chunks(vx, load_voxels, stg, world_info, new=True):
    depth_rn, width_rn, height_rn, w_width, w_height, w_width, r_size, r_area = stg
    for r in load_voxels.keys():

        # Compute region chunk distribution
        if new:
            w, h, d = load_voxels[r]
        else:
            h = r // depth_rn * width_rn
            d = (r - h * depth_rn * width_rn) // width_rn
            w = r - h * depth_rn * width_rn - d * width_rn

        width = int(w_width - w * r_size) if w == width_rn - 1 else r_size
        height = int(w_height - h * r_size) if h == height_rn - 1 else r_size
        depth = int(w_width - d * r_size) if d == depth_rn - 1 else r_size

        for x in range(width):
            for y in range(height):
                for z in range(depth):

                    chunk_index = x + r_size * z + r_area * y

                    # Put the chunk voxels in a separate array
                    if new:
                        chunk = ChunkProxy(world_info, index=(x, y, z), r_index=(w, h, d))
                        vx[r][chunk_index] = chunk.build_voxels()
                    else:
                        vx[r][chunk_index] = load_voxels[r][chunk_index, :]

def asynch_save_region(region):
    pass

def asynch_load_region(util, info, region):
    # Retrieve directory
    save_dir = Path(__file__).parent.parent.parent / util.save_path / util.curr_save_name / "World/"
    save_name = asynch_name_from_index(info, region)

    loaded = False
    voxels = Dict.empty(key_type=types.int64, value_type=types.uint8[:, :])
    found = list(Path(save_dir).glob(save_name + '*'))
    if found:
        voxels[region] = load_decoder(np.load(str(save_dir / (found[0])))['arr_0'],
                                 info.r_vol, info.c_vol)
        loaded = True

    return loaded, voxels

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