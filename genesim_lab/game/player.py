# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
import pygame as pg
from genesim_lab.game.camera import *
from genesim_lab.game.settings import *


# All surfaces ---------------------------------|
class Player(Camera):

    def __init__(self, app, position=game_stgs['player']['pos'], yaw=-90, pitch=0):
        self.app = app
        super().__init__(position, yaw, pitch)

    def update(self):
        self.keyboard_control()
        self.mouse_control()
        super().update()

    def mouse_control(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        if mouse_dx:
            self.rotate_yaw(delta_x=mouse_dx * game_stgs['player']['mouse_sensitivity'])
        if mouse_dy:
            self.rotate_pitch(delta_y=mouse_dy * game_stgs['player']['mouse_sensitivity'])

    def keyboard_control(self):
        key_state = pg.key.get_pressed()
        vel = game_stgs['player']['speed'] * self.app.delta_time
        if key_state[pg.K_w]:
            self.move_forward(vel)
        if key_state[pg.K_s]:
            self.move_back(vel)
        if key_state[pg.K_d]:
            self.move_right(vel)
        if key_state[pg.K_a]:
            self.move_left(vel)
        if key_state[pg.K_SPACE]:
            self.move_up(vel)
        if key_state[pg.K_LCTRL]:
            self.move_down(vel)
