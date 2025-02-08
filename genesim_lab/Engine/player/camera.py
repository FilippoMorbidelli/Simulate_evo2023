# Evolution simulation project - menu module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 17/12/2023
# Notes: Handles main menu, settings, play and other menu

# Import packages ------------------------------|
from genesim_lab.Engine.settings import *
from genesim_lab.Engine.player.frustum import Frustum


# All surfaces ---------------------------------|
class Camera:

    def __init__(self, app, position, yaw, pitch):
        self.app = app
        self.c_info = app.stg.camera

        self.position = glm.vec3(position)
        self.yaw = glm.radians(yaw)
        self.pitch = glm.radians(pitch)

        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        self.m_proj = glm.perspective(self.c_info.v_fov, self.c_info.aspect_ratio, self.c_info.near, self.c_info.far)
        self.m_view = glm.mat4()

        self.frustum = Frustum(self, self.c_info, app.stg.world)

    def update(self):
        self.update_vectors()
        self.update_view_matrix()

    def update_view_matrix(self):
        self.m_view = glm.lookAt(self.position, self.position + self.forward, self.up)

    def update_vectors(self):
        self.forward.x = glm.cos(self.yaw) * glm.cos(self.pitch)
        self.forward.y = glm.sin(self.pitch)
        self.forward.z = glm.sin(self.yaw) * glm.cos(self.pitch)

        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def rotate_pitch(self, delta_y):
        self.pitch -= delta_y
        self.pitch = glm.clamp(self.pitch, - self.c_info.pitch_max, self.c_info.pitch_max)

    def rotate_yaw(self, delta_x):
        self.yaw += delta_x

    def move_left(self, velocity):
        self.position -= self.right * velocity

    def move_right(self, velocity):
        self.position += self.right * velocity

    def move_up(self, velocity):
        self.position += self.up * velocity

    def move_down(self, velocity):
        self.position -= self.up * velocity

    def move_forward(self, velocity):
        self.position += self.forward * velocity

    def move_back(self, velocity):
        self.position -= self.forward * velocity

    def reset_camera(self, position, yaw, pitch):
        self.position = glm.vec3(position)
        self.yaw = glm.radians(yaw)
        self.pitch = glm.radians(pitch)

        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        self.m_proj = glm.perspective(self.c_info.v_fov, self.c_info.aspect_ratio, self.c_info.near, self.c_info.far)
        self.m_view = glm.mat4()

    def move_camera(self, position, yaw, pitch):
        self.position = position
        self.yaw = yaw
        self.pitch = pitch

        self.update_vectors()

        self.m_proj = glm.perspective(self.c_info.v_fov, self.c_info.aspect_ratio, self.c_info.near, self.c_info.far)
        self.m_view = glm.mat4()
