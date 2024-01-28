# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and engine packages --------------|
from numba import njit
import numpy as np
import glm
import math
import pygame as pg
import dataclasses
from dataclasses import dataclass


# Settings ------------------------------------------|
def sim_settings():
    """ """

    # Values are reported in SI units if they have a dimension [m, s, kg, ...]
    settings = {
        'tick': 1,  # [s] tick conversion to seconds
        'x_min': -128,  # [m]
        'y_min': -128,  # [m]
        'x_max': 128,  # [m]
        'y_max': 128,  # [m]
        'terrain': {
            'shape': (256, 256),
            'resolution': (1, 1),
            'octaves': 6,
            'persistence': 0.5,
            'grass_ID': 1,
            'grass_RGB': [],
            'water_threshold': 0.2,
            'water_ID': 0,
            'water_RGB': [],
            'vegetation_ID': 2,
            'vegetation_RGB': [],
        },
        'resources': {
            'init_food_veg': 50,
            'init_food_grass': 10,
            'init_pond': 25,
            'food_max': 150,
            'pond_max': 75,
            'food_radius': 0.05,
            'pond_radius': 0.2,
            'food_sp_ticks': 2,
            'pond_sp_ticks': 10,
        },
        'creatures': {
            'spawn_creatures': 50,
        },
    }

    return settings


pg.font.init()  # Init pygame fonts to create font inside settings


@dataclass(slots=True, order=True)
class WorldObj:
    # Celestial bodies
    bodies: tuple = (
        # [Name, id, distance, orbit time, scale, init_pos]
        ("Skybox", 0, 0 * 5 * 32, 0                     , 1000, glm.vec3(0, 0, 0)),
        ("Sun"   , 1, 5 * 5 * 32, 12 * 30 * 24 * 60 * 60, 75  , glm.vec3(1, 0, 0)),
        ("Moon"  , 2, 2 * 5 * 32, 28 * 24 * 60 * 60     , 25  , glm.vec3(-1, 0, 0))
    )

    # Earth revolution
    revolution: int = 24 * 60 * 60

    # World Clock
    speedup: int = 120  # Number of seconds in game for each real second


@dataclass(slots=True, order=True)
class Interaction:
    # Ray casting
    max_ray_dist: int = 6


@dataclass(slots=True, order=True)
class World:
    # Chunk data
    c_size: float = 32  # Chunk size == number of cubes along a dimension [N x N x N]
    c_half: float = c_size // 2
    c_area: float = c_size ** 2
    c_vol: float = c_size ** 3
    c_sphere_radius: float = c_half * math.sqrt(3)

    # Voxel data (stretching factor along each dimension)
    v_x: float = 1.0
    v_y: float = 0.5
    v_z: float = 1.0
    scale: glm.vec3 = glm.vec3(v_x, v_y, v_z)
    c_scale: glm.vec3 = c_size * scale
    v_x_i: float = 1 / v_x
    v_y_i: float = 1 / v_y
    v_z_i: float = 1 / v_z
    scale_i: glm.vec3 = glm.vec3(v_x_i, v_y_i, v_z_i)

    # World data
    w_width: int = 10
    w_height: int = 3
    w_depth: int = w_width
    w_area: int = w_width * w_depth
    w_vol: int = w_area * w_height

    # World center data
    center_xz: float = w_width * c_half
    center_y: float = w_height * c_half
    offset: glm.vec3 = glm.vec3(w_width/2, 0, w_depth/2)

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class Window:
    h: int = 900  # Height of window
    l: int = 1600  # Length of window
    full_screen: bool = True  # Automatically opens engine in full screen
    rect: pg.Rect = None  # Current rect of main window

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class CameraData:
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
class PlayerData:
    speed: float = 0.01  # Limit player speed to move around
    rot_speed: float = 0.003  # Limit player speed to rotate
    pos: float = glm.vec3(0, 0, 0)  # Player initial position
    mouse_sensitivity: float = 0.002  # Mouse sensitivity

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class Util:
    fps_limit: int = 144  # Limit frame rate to value
    text_font: pg.font = pg.font.SysFont('Verdana', 16)  # Font and size for utility text
    text_color: tuple = (255, 255, 255)  # Color of displayed text

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclass(slots=True, order=True)
class GameSettings:
    world = World()
    world_obj = WorldObj()
    interaction = Interaction()
    window = Window()
    camera = CameraData()
    player = PlayerData()
    util = Util()

    # Addition settings to compute after init
    player.pos = glm.vec3(0, world.w_height * world.c_size * world.v_y, 0)
    world_obj.bodies

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


stg = GameSettings()

(c_size, c_half, c_area, c_vol, c_sphere_radius, v_x, v_y, v_z, scale, c_scale, v_x_i, v_y_i, v_z_i, scale_i,
 w_width, w_height, w_depth, w_area, w_vol, center_xz, center_y, offset) = stg.world
