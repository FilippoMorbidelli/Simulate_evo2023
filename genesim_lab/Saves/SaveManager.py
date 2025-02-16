# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 11/01/2025
# Objectives:

# Import third party and Engine packages --------------|
from pathlib import Path
from datetime import datetime
from genesim_lab.Engine.world_gen.world import get_init_regions
from genesim_lab.Engine.scene.surfaces import SaveLoadMenu
from genesim_lab.Engine.scene.events import GS
from genesim_lab.Engine.settings import World
from pyglm import glm
import re
import ntpath
import numpy as np
from numba import uint8, types
from numba.typed import Dict
from numba import njit
from ast import literal_eval


# Save and Load Manager -------------------------------|
class SaveManager:

    def __init__(self, app):
        self.app = app
        self.info = app.stg.world

        self.current_save   = ""
        self.save_path      = Path(__file__).parent.parent.parent / app.stg.util.save_path
        self.path_world     = "World/"
        self.path_world_ext = ".npz"

        self.path_regions   = "Regions.npz"
        self.path_player    = "Player.txt"
        self.path_info      = "SaveInfo.txt"
        self.path_w_stg     = "WorldSettings.pkl"

        # Current save files data
        self.existing_saves = [None for _ in range(5)]

    def manage_sl(self, file_num, file_name = ""):
        # Strip Save File name to get file number
        num = re.sub(r"\D+", "", file_num)
        # Get Save Name
        if not file_name:
            file_name = self.existing_saves[int(num)]
        # Call Save or Load function
        if self.app.scene.sprite_util["SaveLoad"] == "load":
            # Load Whole file
            self.load_whole_file(file_name)
        else:
            # PUT OVERWRITE  CHOICE????
            # Save Whole file
            self.save_whole_file(num, file_name)
            # Reload save_load scene
            self.app.shader_prog_2D.saves_menu.empty()
            self.app.shader_prog_2D.saves_menu.gl_vertices.clear()
            self.app.scene.surf.saves_menu = SaveLoadMenu(self.app)

    def save_whole_file(self, num, name = ""):
        # Get real date
        date = datetime.today().strftime('%Y-%m-%d %H:%M')

        # Create save directory with input name
        path_to_create = self.save_path / name / self.path_world
        path_to_create.parent.mkdir(exist_ok=True, parents=True)
        path_to_create.mkdir(exist_ok=True, parents=True)

        # Save World settings
        with open(self.save_path / name / self.path_w_stg, 'w+') as f:
            self.info.save_to_pickle(self.save_path / name / self.path_w_stg)

        # Save World voxels
        for rid, r_voxels in self.app.scene.surf.main_game.world.voxels.items():
            r_name = self.get_name_from_index(rid)
            path = self.path_world + r_name + self.path_world_ext
            with open(self.save_path / name / path, 'w+') as f:
                voxels = save_encoder(r_voxels)
                np.savez_compressed(self.save_path / name / path, voxels)

        # Save player state
        with open(self.save_path / name / self.path_player, 'w+') as f:
            f.write(str(self.app.player.position.to_list()) + "; ")
            f.write(str(self.app.player.yaw) + "; ")
            f.write(str(self.app.player.pitch) + "; ")

        # Save Info
        with open(self.save_path / name / self.path_info, 'w+') as f:
            f.write(name + " ," + str(date) + " ," + num)

    def load_whole_file(self, name):
        # Retrieve directory
        save_dir = self.save_path / name / self.path_world #.glob('**/*.npz')

        # Load World settings
        self.info = World.load_from_pickle(self.save_path / name / self.path_w_stg)

        # Read player info (position) - necessary to retrieve active regions
        with open(self.save_path / name / self.path_player, 'r') as f:
            player = f.read().split("; ")[:-1]

        # Compute 27 regions adjacent to player (if existing)
        regions = get_init_regions(self.info, glm.vec3(literal_eval(player[0])))
        regions_save_name = []
        for r in regions.keys():
            regions_save_name.append(self.get_name_from_index(r))

        # Read whole file data and set data to voxel container
        voxels = Dict.empty(key_type = types.int64, value_type = types.uint8[:, :])
        for file in regions_save_name:
            r_index = self.get_index_from_name(file)
            voxels[r_index] = load_decoder(np.load(str(save_dir / (file + self.path_world_ext)))['arr_0'], self.info.r_vol, self.info.c_vol)

        # Init game
        self.app.scene.set_primary(GS.MainGame)
        self.app.custom_events.event_types.update_scene_logic()
        self.app.scene.surf.main_game.init_world(voxels)
        self.app.player.move(*player)


    def save_single_region(self, region):
        pass

    def load_single_region(self, region):
        pass

    def get_index_from_name(self, region_string):
        # Extract indexes from name and compute index to corresponding region
        x, y, z = re.findall(r'\d+', region_string)
        index = int(x) + self.info.width_rn * int(z) + self.info.width_rn * self.info.depth_rn * int(y)

        return index

    def get_name_from_index(self, region_index):
        # Get region coordinates from region index by inspecting a chunk
        y = region_index // self.info.depth_rn * self.info.width_rn
        z = (region_index - y * self.info.depth_rn * self.info.width_rn) // self.info.width_rn
        x = region_index - y * self.info.depth_rn * self.info.width_rn - z * self.info.width_rn

        r_name = "r_" + str(x) + "_" + str(y) + "_" + str(z)

        return r_name


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

@njit
def run_length_encoding(voxels):
    # Define max encoded array
    length = voxels.shape[0]
    rle_voxels = np.empty(2 * length, dtype = 'uint8')
    # Define variables
    count = 1
    rle_pos = 0
    # Main loop
    for i in range(length - 1):
        if voxels[i] == voxels[i + 1] and count < 254:
            count += 1
        else:
            rle_voxels[rle_pos] = uint8(count)
            rle_voxels[rle_pos + 1] = voxels[i]
            rle_pos += 2
            count = 1
    # Insert last run length
    rle_voxels[rle_pos] = uint8(count)
    rle_voxels[rle_pos + 1] = voxels[i+1]
    rle_pos += 2
    # Truncate array
    rle_voxels = rle_voxels[ : rle_pos]
    # Compression
    # None
    return rle_voxels

@njit
def run_length_decoding(rle_voxels):
    # Reshape
    pairs = rle_voxels.reshape(-1, 2)
    # Extract counts and values
    counts = pairs[:, 0]
    values = pairs[:, 1]
    # Use np.repeat to repeat each value according to its count
    voxels = np.repeat(values, counts)

    return voxels

@njit
def save_encoder(chunks):
    rle_chunks = np.empty(1, dtype='uint8')
    # Iterate over each chunk and apply rle encoding, then append
    for voxels in chunks:
        rle_chunks = np.append(rle_chunks, run_length_encoding(voxels))
        rle_chunks = np.append(rle_chunks, uint8(255))

    return rle_chunks[1:-1]

@njit
def load_decoder(chunks, w, c):
    # Split array into single chunks
    separator = np.array(255, dtype='uint8')
    separator_size = 1
    # Create a sliding window view to find the separator
    window_view = np.lib.stride_tricks.sliding_window_view(chunks, separator_size)
    # Manually apply np.all along axis=1 since njit cannot handle axis arg of np.all
    mask = np.empty(len(window_view), dtype=np.bool_)
    for i in range(len(window_view)):
        mask[i] = np.all(window_view[i] == separator)
    #mask = np.all(np.lib.stride_tricks.sliding_window_view(chunks, separator_size) == separator, axis = 1) Used without Njit
    separator_indices = np.where(mask)[0]
    sequences = []
    start = 0
    for idx in separator_indices:
        # Extract the sequence before the separator
        sequences.append(chunks[start : idx])
        # Update the start index to skip the separator
        start = idx + separator_size
    # Append the last sequence after the final separator
    sequences.append(chunks[start : ])
    # Decode each chunk
    decoded_chunks = np.empty((w, c), dtype='uint8')
    for idx, seq in enumerate(sequences):
        decoded_chunks[idx] = run_length_decoding(seq)

    return decoded_chunks

@njit
def pack_data(c1, v1, c2, v2, c3):
    # c1: 6bit, v1: 6bit, c2: 6bit, v2: 6bit, c3: 6bit, void --> 2bit
    a, b, c, d, e = c1, v1, c2, v2, c3

    b_bit, c_bit, d_bit, e_bit = 6, 6, 6, 6
    de_bit = d_bit + e_bit
    cde_bit = c_bit + de_bit
    bcde_bit = b_bit + cde_bit

    packed_data = (
            a << bcde_bit |
            b << cde_bit |
            c << de_bit |
            d << e_bit | e
    )

    return packed_data