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
        self.texture_0 = self.load('terrain/voxel_blank.svg')  # Blank voxel (used by voxel handler)
        self.texture_array_0 = self.load('terrain/terrain_array.svg', is_tex_array=True)  # Terrain
        self.texture_array_sky = self.load('terrain/sky_array.svg', is_tex_array=True)  # Sky objects

        # Assign texture unit
        self.texture_0.use(location=1)
        self.texture_array_0.use(location=2)
        self.texture_array_sky.use(location=3)

    def load(self, file_name, is_tex_array=False):
        texture = pg.image.load(f'genesim_lab/assets/main_game/{file_name}')
        texture = pg.transform.flip(texture, flip_x=True, flip_y=False)

        if is_tex_array:
            # If voxels are not cubic remember to stretch sides texture!
            num_layers = 3 * texture.get_height() // texture.get_width()  # 3 textures per layer
            texture = self.ctx.texture_array(
                size=(texture.get_width(), texture.get_height() // num_layers, num_layers),
                components=4,
                data=pg.image.tostring(texture, 'RGBA')
            )
        else:
            texture = self.ctx.texture(
                size=texture.get_size(),
                components=4,
                data=pg.image.tostring(texture, 'RGBA', False)
            )
        texture.anisotropy = 32.0
        texture.build_mipmaps()
        texture.filter = (mgl.NEAREST, mgl.NEAREST)

        return texture
