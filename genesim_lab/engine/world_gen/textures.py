# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and engine packages --------------|
import pygame as pg
import moderngl as mgl


# Textures --------------------------------------------|
class Textures:

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # Load texture
        self.texture_0 = self.load('terrain/voxel_blank.svg')

        # Assign texture unit
        self.texture_0.use(location=1)

    def load(self, file_name):
        texture = pg.image.load(f'genesim_lab/assets/main_game/{file_name}')
        texture = pg.transform.flip(texture, flip_x=True, flip_y=False)

        texture = self.ctx.texture(
            size=texture.get_size(),
            components=4,
            data=pg.image.tostring(texture, 'RGBA', False)
        )
        texture.anisotropy = 32.0
        texture.build_mipmaps()
        texture.filter = (mgl.NEAREST, mgl.NEAREST)

        return texture
