# Evolution simulation project - chunk generation module
# Author: Filippo Morbidelli
# Created on: 20/11/2023
# Last update: 20/11/2023
# Notes: Contains the engine, engine start and world_objects generation

# Import packages ------------------------------|
from genesim_lab.engine.settings import *
from genesim_lab.engine.world_objects.world_clock import WorldClock
from genesim_lab.meshes.celestial_mesh import CelestialMesh


# Import packages ------------------------------|
class CelestialBody(WorldClock):

    def __init__(self, app):
        super().__init__(app)
        self.bodies: list = [None for _ in range(3)]
        self.build_bodies()
        self.build_bodies_mesh()

        self.is_on_frustum = self.app.player.frustum.is_on_frustum

    def update(self):
        for body in self.bodies:
            body.update_body()

    def build_bodies(self):
        i = 0
        for data in self.app.stg.world_obj.bodies:
            body = Body(self, data)
            self.bodies[i] = body
            i += 1

    def build_bodies_mesh(self):
        for body in self.bodies:
            body.build_mesh()

    def render(self):
        for body in self.bodies:
            if body.is_active:  # and self.is_on_frustum(body):
                body.set_uniform()
                body.mesh.render()


class Body:

    def __init__(self, world, data):
        self.world = world
        name, b_id, dist, orb_t, b_scale, init = data

        self.mesh: CelestialMesh = None
        self.is_active = True

        # Extract properties
        self.name = name
        self.body_id = b_id
        self.dist = dist
        self.orbit = orb_t
        self.scale = b_scale
        self.position: glm.vec3 = init * self.dist  # Initial position of the body

    def update_body(self):
        if self.body_id == 0:
            self.position = self.world.app.player.position
        pass

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), glm.vec3(self.position))
        return m_model

    def set_uniform(self):
        self.mesh.program['m_model'].write(self.get_model_matrix())

    def build_mesh(self):
        self.mesh = CelestialMesh(self.world.app, b_id=self.body_id)
