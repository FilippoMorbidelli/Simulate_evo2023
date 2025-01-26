# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.Engine.player.camera import *
from genesim_lab.Engine.settings import *
from ast import literal_eval


# All surfaces ---------------------------------|
class Player(Camera):

    def __init__(self, app, position=stg.player.pos, yaw=-135, pitch=0):
        self.app = app
        super().__init__(position, yaw, pitch)

    def update(self):
        self.keyboard_control()
        self.mouse_control()
        super().update()

    def handle_event(self, event):
        # Adding and Removing voxels with clicks
        if event.type == pg.MOUSEBUTTONDOWN:
            voxel_handler = self.app.scene.surfaces.surf.main_game.world.voxel_handler
            if event.button == 1:
                voxel_handler.set_voxel()
            if event.button == 3:
                voxel_handler.switch_mode()

    def mouse_control(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        if mouse_dx:
            self.rotate_yaw(delta_x=mouse_dx * stg.player.mouse_sensitivity)
        if mouse_dy:
            self.rotate_pitch(delta_y=mouse_dy * stg.player.mouse_sensitivity)

    def keyboard_control(self):
        key_state = pg.key.get_pressed()
        vel = stg.player.speed * self.app.delta_time
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

    def reset(self):
        self.reset_camera(position=stg.player.pos, yaw=-90, pitch=0)

    def move(self, pos, yaw, pitch):
        self.reset_camera(position=glm.vec3(literal_eval(pos)), yaw=float(yaw), pitch=float(pitch))