# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
import multiprocessing as mp
import time

from multiprocessing.managers import BaseManager, BaseProxy
from genesim_lab.Engine.settings import *
from genesim_lab.Engine.world_gen.chunk import Chunk
from genesim_lab.Engine.world_gen.sparsevoxeloctree import build_svo

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
                    r_id, r_coord = to_process
                    stg = (self.stg.world.depth_rn, self.stg.world.width_rn, self.stg.world.w_width,
                           self.stg.world.w_height, self.stg.world.w_width, self.stg.world.r_size, self.stg.world.r_area)

                    # If region already exists load it (only voxels)
                    is_loaded, voxels = asynch_load_region(self.stg.util, self.stg.world, r_id)

                    # Preallocate Chunks and voxels
                    chunks = [None for _ in range(self.stg.world.r_vol)]
                    svo = dict()

                    # Build Chunks
                    if not is_loaded:
                        voxels = np.zeros([self.stg.world.r_vol, self.stg.world.c_vol], dtype='uint8')
                        asynch_build_chunks({r_id: r_coord}, stg, new=True)
                    else:
                        asynch_build_chunks({r_id: voxels}, stg, new=False)

                    # Build Chunks Mesh
                    for chunk in chunks[r_id]:
                        if chunk is not None:
                            chunk.build_mesh_threaded()

                    # Build SVO
                    svo[r_id] = build_svo(self.app, self.world.info, self.world.chunks[r_id], r_index)

                    # Load response to dedicated queue (to be read by main process)
                    self.rsp_queue.put([result, voxels, chunk, svo])

# Functions called by Child Processes -----------------|
def asynch_build_chunks(load_voxels, stg, new=True):
    depth_rn, width_rn, w_width, w_height, w_width, r_size, r_area = stg
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
                        chunk = Chunk(self, index=(x, y, z), r_index=(w, h, d))

                        chunk_index = x + r_size * z + r_area * y
                        self.chunks[r][chunk_index] = chunk

                        # Put the chunk voxels in a separate array
                        if new:
                            self.voxels[r][chunk_index] = chunk.build_voxels()
                        else:
                            self.voxels[r][chunk_index] = load_voxels[r][chunk_index, :]
                            chunk.is_empty = False

                        # Get pointer to voxels
                        chunk.voxels = self.voxels[r][chunk_index]

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
    y = region_index // info.depth_rn * info.width_rn
    z = (region_index - y * info.depth_rn * info.width_rn) // info.width_rn
    x = region_index - y * info.depth_rn * info.width_rn - z * info.width_rn

    r_name = "r_" + str(x) + "_" + str(y) + "_" + str(z)

    return r_name

def asynch_index_from_name(info, region_string):
    # Extract indexes from name and compute index to corresponding region
    x, y, z = re.findall(r'\d+', region_string)
    index = int(x) + info.width_rn * int(z) + info.width_rn * info.depth_rn * int(y)

    return index

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