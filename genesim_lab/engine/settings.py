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


pg.font.init()

game_stgs = {
    'world': {
        'chunk_size': 32,
        'h_chunk_size': 16,
        'chunk_area': 32 * 32,
        'chunk_vol': 32 * 32 * 32,
    },
    'window': {  # Game window
        'h': 900,  # Height of window
        'l': 1600,  # Length of window
        'full_screen': True,  # Automatically opens engine in full screen
        'rect': None,  # Current rect of main window
    },
    'camera': {  # Camera settings
        'aspect_ratio': 1920/1080,  # Implement correct value not hard coded
        'fov_deg': 50,  # Field of view degrees
        'v_fov': glm.radians(50),  # Vertical FOV
        'h_fov': 2 * math.atan(math.tan(50 * 0.5) * 1920/1080),  # Horizontal FOV
        'near': 0.1,  # Near field
        'far': 2000.0,  # Far field
        'pitch_max': glm.radians(89),  # Max pitch of camera
    },
    'player': {  # Player settings
        'speed': 0.005,  # Limit player speed to move around
        'rot_speed': 0.003,  # Limit player speed to rotate
        'pos': glm.vec3(16, 32, 1.5 * 32),  # Player initial position
        'mouse_sensitivity': 0.002,  # Mouse sensitivity
    },
    'util': {  # Utilities
        'fps_limit': 144,  # Limit frame rate to value
        'text_font': pg.font.SysFont('Verdana', 16),  # Font and size for utility text
        'text_color': (255, 255, 255),  # Color of displayed text
    },
}


@dataclass(slots=True)
class World:
    chunk_size: float = 32
    h_chunk_size: float = chunk_size / 2
    chunk_area: float = chunk_size ** 2
    chunk_vol: float = chunk_size ** 3


@dataclass(slots=True)
class Window:
    h: int = 900  # Height of window
    l: int = 1600  # Length of window
    full_screen: bool = True  # Automatically opens engine in full screen
    rect: pg.Rect = None  # Current rect of main window


@dataclass(slots=True)
class CameraData:
    aspect_ratio: float = 1920/1080  # Implement correct value not hard coded
    fov_deg: float = 50  # Field of view degrees
    v_fov: float = glm.radians(fov_deg)  # Vertical FOV
    h_fov: float = 2 * math.atan(math.tan(fov_deg * 0.5) * aspect_ratio)  # Horizontal FOV
    near: float = 0.1  # Near field
    far: float = 2000.0  # Far field
    pitch_max: float = glm.radians(89)  # Max pitch of camera


@dataclass(slots=True)
class PlayerData:
    speed: float = 0.005  # Limit player speed to move around
    rot_speed: float = 0.003  # Limit player speed to rotate
    pos: float = glm.vec3(16, 32, 1.5 * 32)  # Player initial position
    mouse_sensitivity: float = 0.002  # Mouse sensitivity


@dataclass(slots=True)
class Util:
    fps_limit: int = 144  # Limit frame rate to value
    text_font: pg.font = pg.font.SysFont('Verdana', 16)  # Font and size for utility text
    text_color: tuple = (255, 255, 255)  # Color of displayed text


@dataclass(slots=True)
class GameSettings:
    world = World()
    window = Window()
    camera = CameraData()
    player = PlayerData()
    util = Util()
