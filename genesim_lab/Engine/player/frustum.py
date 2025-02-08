# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.Engine.settings import *
from numba.experimental import jitclass

# All surfaces ---------------------------------|
class Frustum:

    def __init__(self, camera, c_info, w_info):
        self.c_info = c_info
        self.w_info = w_info

        self.cam = camera
        self.near = self.c_info.near
        self.far = self.c_info.far

        self.factor_y = 1.0 / math.cos(half_y := self.c_info.v_fov * 0.5)
        self.tan_y = math.tan(half_y)

        self.factor_x = 1.0 / math.cos(half_x := self.c_info.h_fov * 0.5)
        self.tan_x = math.tan(half_x)

    def is_on_frustum(self, center, sphere_radius=None):  #chunk
        # Set sphere radius
        if sphere_radius is None:
            sphere_radius = self.w_info.c_sphere_radius

        # Vector to sphere center
        sphere_vec = center - self.cam.position

        # Outside the NEAR and FAR planes?
        sz = glm.dot(sphere_vec, self.cam.forward)
        if not (self.near - sphere_radius <= sz <= self.far + sphere_radius):
            return False

        # Outside the TOP and BOTTOM planes?
        sy = glm.dot(sphere_vec, self.cam.up)
        dist = self.factor_y * sphere_radius + sz * self.tan_y
        if not (-dist <= sy <= dist):
            return False

        # Outside the LEFT and RIGHT planes?
        sx = glm.dot(sphere_vec, self.cam.right)
        dist = self.factor_x * sphere_radius + sz * self.tan_x
        if not (-dist <= sx <= dist):
            return False

        return True
