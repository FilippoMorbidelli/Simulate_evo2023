# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and Engine packages --------------|
import numpy as np
from pyglm import glm
import math
import pygame as pg
import dataclasses
import pickle

from dataclasses import dataclass
from numba.experimental import jitclass
from numba import float64, int32
from pygame import freetype
from pathlib import Path


# Settings ------------------------------------------|

# Initializations required ----------|
pg.font.init()  # Init pygame fonts to create font inside settings
freetype.init() # Init pygame fonts to create font inside settings


# All game settings -----------------|
@dataclass(slots=True, order=True)
class WorldObj:  # Contains settings about any world object
    # Skybox
    Skybox: tuple = ("Skybox", 0, 0 * 5 * 32, 0, 1000, glm.vec3(0, 0, 0))

    # Celestial bodies
    bodies: tuple = (
        # [Name, id, distance, orbit time, scale, init_pos]
        ("Sun"   , 0, 5 * 5 * 32, 12 * 30 * 24 * 60 * 60, 75  , glm.vec3(1, 0, 0)),
        ("Moon"  , 1, 2 * 5 * 32, 28 * 24 * 60 * 60     , 25  , glm.vec3(-1, 0, 0))
    )

    # Earth revolution
    revolution: int = 24 * 60 * 60

    # World Clock
    speedup: int = 1200  # Number of seconds in game for each real second


@dataclass(slots=True, order=True)
class Interaction:  # Contains settings about player interaction inside world
    # Ray casting
    max_ray_dist: int = 6


@dataclass(slots=True, order=True)
class World:  # Contains settings about world generation, chunks, regions, ecc
    # Chunk data
    c_size          : float = 48  # Chunk size == number of cubes along a dimension [N x N x N]
    c_half          : float = c_size // 2
    c_area          : float = c_size ** 2
    c_vol           : float = c_size ** 3
    c_sphere_radius : float = c_half * math.sqrt(3)
    c_threshold     : float = c_size * 12 # Camera-Chunk distance from which the greedy mesh can be used

    # Voxel data (stretching factor along each dimension)
    v_x     : float = 1.0
    v_y     : float = 0.5
    v_z     : float = 1.0
    scale   : glm.vec3 = glm.vec3(v_x, v_y, v_z)
    c_scale : glm.vec3 = c_size * scale
    v_x_i   : float = 1 / v_x
    v_y_i   : float = 1 / v_y
    v_z_i   : float = 1 / v_z
    scale_i : glm.vec3 = 1 / scale

    # World data
    w_width  : int = 4
    w_height : int = 4
    w_depth  : int = w_width
    w_area   : int = w_width * w_depth
    w_vol    : int = w_area * w_height

    # World center data
    center_xz : float = w_width * c_half
    center_y  : float = w_height * c_half
    offset    : glm.vec3 = glm.vec3(w_width/2, 0, w_depth/2)

    # Region data
    r_size   : int = 4  # Number of chunks per dimension per region
    r_area   : int = r_size ** 2
    r_vol    : int = r_size ** 3
    rc_size  : int = r_size * c_size
    width_rn : int = int(np.ceil(w_width / r_size))
    height_rn: int = int(np.ceil(w_height / r_size))
    depth_rn : int = int(np.ceil(w_depth / r_size))
    r_number : int = width_rn * height_rn * depth_rn

    # Octree creation data
    vso_depth    : int = int(np.log2(r_size) - 1)  # log2(r_size)
    vso_p_sides  : glm.vec3 = r_size * c_scale
    vso_p_pos    : glm.vec3 = - offset * c_scale

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def save_to_pickle(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)  # Save the entire object

    @classmethod
    def load_from_pickle(cls, filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)  # Load the entire object


@dataclass(slots=True, order=True)
class Simulation:  # Contains settings about simulation parameters
    pass


@dataclass(slots=True, order=True)
class Window:  # Contains settings about app window
    h : int            = 900  # Height of window
    w : int            = 1600  # Width of window
    full_screen : bool = True  # Automatically opens Engine in full screen
    rect : pg.Rect     = None  # Current rect of main window
    w_ref : int        = 1920 # Sprite reference width
    h_ref : int        = 1080 # Sprite reference height

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class CameraData:  # Contains settings about player camera parameters
    aspect_ratio: float = 1920/1080  # Implement correct value not hard coded
    fov_deg: float = 50  # Field of view degrees
    v_fov: float = glm.radians(fov_deg)  # Vertical FOV
    h_fov: float = 2 * math.atan(math.tan(v_fov * 0.5) * aspect_ratio)  # Horizontal FOV
    near: float = 0.1  # Near field
    far: float = 2000.0  # Far field
    pitch_max: float = glm.radians(89)  # Max pitch of camera

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class PlayerData:  # Contains settings about player data
        speed: float = 0.1  # Limit player speed to move around
        rot_speed: float = 0.003  # Limit player speed to rotate
        pos: glm.vec3 = glm.vec3(0, 0, 0)  # Player initial position
        mouse_sensitivity: float = 0.002  # Mouse sensitivity


@dataclass(slots=True, order=True)
class Util:  # Contains settings about util parameters and functions
    fps_limit  : int = 1000  # Limit frame rate to value
    save_path  : str = "SaveFiles/"  # Path in Game directory containing the save files
    curr_save_name : str = ""  # Temporary save name of current loaded game name

class FontUtil:
    def __init__(self):
        self.text_font : pg.font = pg.font.SysFont('Verdana', 16)  # Font and size for utility text
        self.ui_font: freetype.Font = freetype.Font(Path(__file__).parent.parent / "Assets/Fonts/Stormfaze.otf", 28)
        self.text_color: tuple = (255, 255, 255)  # Color of displayed text


#@dataclass(slots=True, order=True)
class SharedGameSettings:  # Main wrapped settings class
    def __init__(self, world, simulation,
                 world_obj, interaction, window,
                 camera_data, player_data, util):
        # Set from input each subclass since they need to be ProxyClass to support MultiProcessing
        self.world       = world
        self.sim         = simulation
        self.world_obj   = world_obj
        self.interaction = interaction
        self.window      = window
        self.camera      = camera_data
        self.player      = player_data
        self.util        = util

        # Addition settings to compute after init
        self.player.pos = glm.vec3(0, self.world.w_height * self.world.c_size * self.world.v_y, 0)


class GameSettings:  # Main settings class
    def __init__(self):
        self.world       = World()
        self.sim         = Simulation()
        self.world_obj   = WorldObj()
        self.interaction = Interaction()
        self.window      = Window()
        self.camera      = CameraData()
        self.player      = PlayerData()
        self.util        = Util()
        self.font_util   = FontUtil()

        # Addition settings to compute after init
        self.player.pos = glm.vec3(0, self.world.w_height * self.world.c_size * self.world.v_y, 0)


# Mesh builder util functions ----------------------------------------|
powers = 1 << np.array(range(48), dtype="int64")

# World Settings for njit --------------------------------------------|
spec = [
    ("c_size"   , int32), ("c_area"   , int32), ("c_vol"    , int32),
    ("off_x"    , int32), ("off_y"    , int32), ("off_z"    , int32),
    ("v_x"      , float64), ("v_y"    , float64), ("v_z"    , float64),
    ("r_size"   , int32), ("r_area"   , int32), ("rc_size"  , int32),
    ("width_rn" , int32), ("height_rn", int32), ("depth_rn" , int32),
]

@jitclass(spec)
class ChunkMeshSettings:
    def __init__(self, c_size, c_area, c_vol,
                       off_x, off_y, off_z,
                       v_x, v_y, v_z,
                       r_size, r_area, rc_size,
                       width_rn, height_rn, depth_rn):
        # Manually set each setting needed for mesh creation (GPU)
        self.c_size    = c_size
        self.c_area    = c_area
        self.c_vol     = c_vol
        self.off_x     = off_x
        self.off_y     = off_y
        self.off_z     = off_z
        self.v_x       = v_x
        self.v_y       = v_y
        self.v_z       = v_z
        self.r_size    = r_size
        self.r_area    = r_area
        self.rc_size   = rc_size
        self.width_rn  = width_rn
        self.height_rn = height_rn
        self.depth_rn  = depth_rn

# Settings functions ----------|

# Change Setting Value

# Reset to Basic