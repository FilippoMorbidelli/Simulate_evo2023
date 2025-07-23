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
class Proxy:
    pass

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
    c_size          : float = 32  # Chunk size == number of cubes along a dimension [N x N x N] -- reduced to 32 from 48 for performances
    cSizeBin        : int   = int(math.log2(c_size))
    cMask           : bin   = (1 << cSizeBin) - 1
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
    iv_x    : float = 1 / v_x
    iv_y    : float = 1 / v_y
    iv_z    : float = 1 / v_z
    scale_i : glm.vec3 = 1 / scale

    # World data
    w_width  : int = 16
    w_height : int = 16
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
    rSizeBin : int = int(math.log2(r_size))
    rcSzBin  : int = int(math.log2(r_size * c_size))
    rMask    : bin = (1 << rSizeBin) - 1
    rcMask   : bin = (1 << rcSzBin) - 1

    rc_size  : int = r_size * c_size
    width_rn : int = int(np.ceil(w_width / r_size))
    height_rn: int = int(np.ceil(w_height / r_size))
    depth_rn : int = int(np.ceil(w_depth / r_size))

    r_number : int = width_rn * height_rn * depth_rn
    r_limit  = []
    for x in range(r_size):
        for y in range(r_size):
            for z in range(r_size):
                if x == 0 or x == r_size - 1 or z == 0 or z == r_size - 1:
                    r_limit.append(x + z * r_size + y * r_size**2)

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
    save_path  : str = "saveFiles/"  # Path in Game directory containing the save files
    curr_save_name : str = ""  # Temporary save name of current loaded game name


class FontUtil:
    def __init__(self):
        self.text_font : pg.font = pg.font.SysFont('Verdana', 16)  # Font and size for utility text
        self.ui_font: freetype.Font = freetype.Font(Path(__file__).parent.parent / "Assets/Fonts/Stormfaze.otf", 28)
        self.text_color: tuple = (255, 255, 255)  # Color of displayed text


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
        self.player.pos = glm.vec3(0, 47, 0)


# Mesh builder util functions ----------------------------------------|
powers = 1 << np.array(range(32), dtype="int64")

# Settings functions ----------|

# Change Setting Value

# Reset to Basic