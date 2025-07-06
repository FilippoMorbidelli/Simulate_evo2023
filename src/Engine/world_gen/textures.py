# Evolution simulation project
# Author: Filippo Morbidelli
# Last update: 31/07/2023
# Objectives:

# Import third party and Engine packages --------------|
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
        self.texture_cube_skybox = self.get_texture_cube(dir_path='terrain/skybox_', ext='svg')

        # Assign texture unit
        self.texture_0.use(location=1)
        self.texture_array_0.use(location=2)
        self.texture_array_sky.use(location=3)
        self.texture_cube_skybox.use(location=4)

    def get_texture_cube(self, dir_path, ext='png'):
        faces = ['right', 'left', 'top', 'bottom'] + ['front', 'back'][::-1]
        textures = []
        for face in faces:
            texture = pg.image.load('src/Assets/main_game/' + dir_path + f'{face}.{ext}').convert()
            if face in ['right', 'left', 'front', 'back']:
                texture = pg.transform.flip(texture, flip_x=True, flip_y=False)
            else:
                texture = pg.transform.flip(texture, flip_x=False, flip_y=True)
            textures.append(texture)

        size = textures[0].get_size()
        texture_cube = self.ctx.texture_cube(size=size, components=3, data=None)

        for i in range(6):
            texture_data = pg.image.tostring(textures[i], 'RGB')
            texture_cube.write(face=i, data=texture_data)

        return texture_cube

    def load(self, file_name, is_tex_array=False):
        texture = pg.image.load(f'src/Assets/main_game/{file_name}')
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
