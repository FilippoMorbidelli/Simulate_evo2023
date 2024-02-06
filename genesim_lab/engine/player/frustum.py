# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from numba.experimental import jitclass
import numba as nb


# All surfaces ---------------------------------|
spec = [
    ('camera', nb.types.Array(nb.float32, 2, 'C')),
    ('near', nb.float32),
    ('far', nb.float32),
    ('v_fov', nb.float32),
    ('h_fov', nb.float32),
    ('factor_y', nb.float32),
    ('tan_y', nb.float32),
    ('factor_x', nb.float32),
    ('tan_x', nb.float32),
]


@jitclass(spec)
class Frustum:

    def __init__(self, camera):
        self.camera = camera
        self.near = near
        self.far = far
        self.v_fov = v_fov
        self.h_fov = h_fov

        self.factor_y = 1.0 / np.cos(self.v_fov * 0.5)
        self.tan_y = np.tan(self.v_fov * 0.5)

        self.factor_x = 1.0 / np.cos(self.h_fov * 0.5)
        self.tan_x = np.tan(self.h_fov * 0.5)

    def is_on_frustum(self, center, sphere_radius=c_sphere_radius):  #chunk
        # Vector to sphere center
        sphere_vec = center - self.camera[0, :]  #.position

        # Outside the NEAR and FAR planes?
        sz = np.dot(sphere_vec, self.camera[3, :])  #.forward)
        if not (self.near - sphere_radius <= sz <= self.far + sphere_radius):
            return False

        # Outside the TOP and BOTTOM planes?
        sy = np.dot(sphere_vec, self.camera[1, :])  #.up)
        dist = self.factor_y * sphere_radius + sz * self.tan_y
        if not (-dist <= sy <= dist):
            return False

        # Outside the LEFT and RIGHT planes?
        sx = np.dot(sphere_vec, self.camera[2, :])  #.right)
        dist = self.factor_x * sphere_radius + sz * self.tan_x
        if not (-dist <= sx <= dist):
            return False

        return True

    def update(self, camera):
        self.camera = camera
