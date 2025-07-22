# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
# From Src
from src.Engine.sl_manager.SaveManager import load_decoder
from src.Meshes.chunk_mesh_builder import build_chunk_mesh, let_settings_global, define_globals
from src.Engine.world_gen.chunk import ChunkProxy
from src.Meshes.chunk_mesh_builder_greedy import *

# Import Third-Party
import multiprocessing as mp
import numpy as np
import time

# From Third-Party
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from numba.typed import Dict as nDict

# All Processes to spawn -------------------------------|
class LoadProcess(mp.Process):

    def __init__(self, request_queue, response_queue):
        # Extend class
        super().__init__()

        # Init shared data
        self.requestQueue = request_queue
        self.responseQueue = response_queue
        #self.local_world = nDict.empty(key_type=types.int64, value_type=types.uint8[:, :])

    def run(self):
        while True:
            # Check if any request is present else put to Sleep
            if self.requestQueue.empty():
                time.sleep(1)
            else:
                # Retrieve data to process
                request_data = self.requestQueue.get()

                # Kill command
                if request_data == "Kill":
                    self.terminate()
                else:
                    # Unwrap data
                    command, RToLoad, r_coord, w_vox, world_info, util = request_data

                    # Compute specialized settings
                    stg = (world_info.depth_rn, world_info.width_rn, world_info.height_rn, world_info.w_width,
                           world_info.w_height, world_info.w_width, world_info.r_size, world_info.r_area)

                    # Create NJit dict with already known voxels
                    voxels = nDict.empty(key_type=types.int64, value_type=types.uint8[:, :])
                    for r_key, vox in w_vox.items():
                        voxels[r_key] = vox

                    for region in RToLoad:
                        # If region already exists load it (only voxels)
                        is_loaded, l_voxels = asynch_load_region(util, world_info, region)

                        # Build Chunks
                        voxels[region] = np.zeros([world_info.r_vol, world_info.c_vol], dtype='uint8')
                        if not is_loaded:
                            asynch_build_chunks(voxels, {region: r_coord[region]}, stg, world_info, new=True)
                        else:
                            asynch_build_chunks(voxels, l_voxels, stg, world_info, new=False)

                        # Send response to signal that loading has been initialized
                        self.responseQueue.put(["Load", "Init", [region, voxels[region]]])

                    # Define globals to be used by voxel mesh creator
                    define_globals()
                    let_settings_global(world_info)

                    # Build Chunks Mesh for each region
                    format_size = sum(int(fmt[:1]) for fmt in '1u4'.split())
                    for r in RToLoad:
                        # Vox meshes dict (to send)
                        vox_meshes = dict()
                        vox_meshes_greedy = dict()

                        # Loop over 8 chunks each
                        for cc in range(int(world_info.r_vol/8)):
                            RegPos = np.asarray(r_coord[r])

                            # Create ThreadPool to compute 8 chunks in parallel
                            with ThreadPoolExecutor(max_workers=8) as executor:
                                # Compute inputs for each task
                                ccIds = cc * 8 + np.linspace(0,7,8, dtype='uint32')
                                voxArray = voxels[r][ccIds]

                                # Compute Chunk Pos
                                chunkPos = []
                                for c in ccIds:
                                    y = c // world_info.r_area
                                    x = (c - y * world_info.r_area) & world_info.rMask
                                    z = (c - y * world_info.r_area) // world_info.r_size
                                    chunkPos.append((x, y, z))

                                # Submit Tasks
                                futures = [executor.submit(build_chunk_mesh_greedy, voxels[r][ccc], get_neighbors(voxels, np.array(RegPos), np.array(cPos), world_info), format_size, 32)
                                           for ccc, cPos in zip(ccIds, chunkPos)
                                           ]

                                # Get Results
                                for c in range(8):
                                    mesh = futures[c].result()
                                    vox_meshes[ccIds[c]] = mesh

                            self.responseQueue.put(["Load", "InProgress", [r, r_coord[r], vox_meshes, vox_meshes_greedy]])

                        # Load response to confirm computation of new region has ended
                        self.responseQueue.put(["Load", "DoneRegion", [r, r_coord[r]]])

                    # Load response to confirm computation of new region has ended
                    if command == "InitWorld":
                        self.responseQueue.put(["Load", "InitDone", []])
                    else:
                        self.responseQueue.put(["Load", "Done", []])


def asynch_load_region(util, info, region):
    # Retrieve directory
    save_dir = Path(__file__).parent.parent.parent / util.save_path / util.curr_save_name / "World/"
    save_name = asynch_name_from_index(info, region)

    loaded = False
    voxels = nDict.empty(key_type=types.int64, value_type=types.uint8[:, :])
    found = list(Path(save_dir).glob(save_name + '*'))
    if found:
        voxels[region] = load_decoder(np.load(str(save_dir / (found[0])))['arr_0'], info.r_vol, info.c_vol)
        loaded = True

    return loaded, voxels


def asynch_name_from_index(info, region_index):
    # Get region coordinates from region index by inspecting a chunk
    y = region_index // (info.depth_rn * info.width_rn)
    z = (region_index - y * info.depth_rn * info.width_rn) // info.width_rn
    x = region_index - y * info.depth_rn * info.width_rn - z * info.width_rn

    r_name = "r_" + str(x) + "_" + str(y) + "_" + str(z)

    return r_name


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