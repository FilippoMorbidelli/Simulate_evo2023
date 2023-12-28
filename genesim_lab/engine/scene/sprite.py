# Evolution simulation project - sprite module
# Author: Filippo Morbidelli
# Created on: 03/12/2023
# Last update: 03/12/2023
# Notes: Handles all 2D sprites like text or images to render onto the main surface. There are two types of sprites
#        used, the first one uses pygame surface.blit to apply 2D text to the surface, the second uses pygame image to
#        load a png/jpg as a surface to render.

# Import packages ------------------------------|
import ctypes
import pygame as pg


# Sprite shader program ------------------------|
class GLTextures2D(pg.sprite.Group):

    def __init__(self, app, sprites=None):
        if sprites is None:
            super().__init__()
        else:
            super().__init__(sprites)
        self.app = app
        self.gl_context = app.ctx
        self.gl_program = None
        self.gl_buffer = None
        self.gl_vao = None
        self.gl_textures = {}
        self.gl_vertices = {}

    def get_program(self):
        if self.gl_program is None:
            with open(f'genesim_lab/shaders/2D_sprite.vert') as file:
                vertex_shader_sprite = file.read()

            with open(f'genesim_lab/shaders/2D_sprite.frag') as file:
                fragment_shader_sprite = file.read()

            self.gl_program = self.gl_context.program(vertex_shader=vertex_shader_sprite,
                                                      fragment_shader=fragment_shader_sprite)
            self.gl_program['u_texture'] = 0
        return self.gl_program

    def get_buffer(self):
        if self.gl_buffer is None:
            self.gl_buffer = self.gl_context.buffer(None, reserve=6 * 4 * 4)
            self.gl_buffer.ctx.fbo.depth_mask = False
        return self.gl_buffer

    def get_vao(self):
        if self.gl_vao is None:
            self.gl_vao = self.gl_context.vertex_array(self.get_program(),
                                                       [(self.get_buffer(), "2f4 2f4", "in_position", "in_uv")])
        return self.gl_vao

    def get_texture(self, image):
        if image not in self.gl_textures:
            rgba_image = image.convert_alpha()
            texture = self.gl_context.texture(rgba_image.get_size(), 4, rgba_image.get_buffer())
            texture.swizzle = 'BGRA'
            self.gl_textures[image] = texture
        return self.gl_textures[image]

    def render(self, sprite, surface):
        # Check if VBO for sprite exists, in case builds it or update it (forced_reconstruct == True)
        if sprite.name not in self.gl_vertices or sprite.forced_reconstruct:
            w, h = surface.get_size()
            left, top, width, height = sprite.rect
            right = left + width
            bottom = top + height
            corners = [  # Convert vertex
                (left / w * 2 - 1, 1 - bottom / h * 2),  # Bottomleft corner
                (right / w * 2 - 1, 1 - bottom / h * 2),  # Bottomright corner
                (right / w * 2 - 1, 1 - top / h * 2),  # Topright corner
                (left / w * 2 - 1, 1 - top / h * 2),  # Topleft corner
            ]
            vertices_quad_2d = (ctypes.c_float * (6 * 4))(
                *corners[0], 0.0, 1.0,
                *corners[1], 1.0, 1.0,
                *corners[2], 1.0, 0.0,
                *corners[0], 0.0, 1.0,
                *corners[2], 1.0, 0.0,
                *corners[3], 0.0, 0.0)
            self.gl_vertices[sprite.name] = vertices_quad_2d

        self.get_buffer().write(self.gl_vertices[sprite.name])  # Build VBO for the sprite
        self.get_texture(sprite.image).use(location=0)  # Retrive the texture and overwrite it in loc=0
        self.get_vao().render()  # Render sprite

    def draw2d(self):
        for sprite in self:
            self.render(sprite, self.app.screen)

    def update(self, app):
        for sprite in self:
            sprite.update(app)


# 2D Sprite classes ----------------------------|
class OverlaySprite(pg.sprite.Sprite):
    def __init__(self, app, scene, name, ext, flag):
        super().__init__()
        self.sprite = pg.image.load(f'genesim_lab/assets/{scene}/overlay_{name}.{ext}').convert_alpha()
        self.rect = self.sprite.get_rect(center=app.stg.window.rect.center)  # Generate sprite rect from main window
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        self.name = f"overlay_{name}"
        self.flag = flag  # Flag to determine if button is dynamic or not
        self.forced_reconstruct = False  # Flag to determine if vertices for vbo must be reconstructed every frame

    def update(self, *args):
        pass


class BackgroundSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, button, ext, flag):
        super().__init__()
        self.rect = app.stg.window.rect  # Generate sprite rect from main window
        self.sprite = pg.image.load(f'genesim_lab/assets/{scene}/background_{button}.{ext}').convert_alpha()
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        self.name = f"background_{button}"
        self.flag = flag  # Flag to determine if button is dynamic or not
        self.forced_reconstruct = False  # Flag to determine if vertices for vbo must be reconstructed every frame

    def update(self, *args):
        pass


class ButtonSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, button, ext, flag):
        super().__init__()
        self.rect = app.stg.window.rect  # Generate sprite rect from main window
        self.sprite_F = pg.image.load(f'genesim_lab/assets/{scene}/button_{button}_F.{ext}').convert_alpha()
        self.sprite_T = pg.image.load(f'genesim_lab/assets/{scene}/button_{button}_T.{ext}').convert_alpha()
        self.image = self.sprite_F
        self.mask = pg.mask.from_surface(self.image)
        self.over = self.mask.get_at(app.mouse)  # Add check if mouse is over from start
        self.name = f"button_{button}"
        self.flag = flag  # Flag to determine if sprite is dynamic or not
        self.forced_reconstruct = False  # Flag to determine if vertices for vbo must be reconstructed every frame

    def update(self, *args):
        pass


class UtilityStaticText(pg.sprite.Sprite):
    def __init__(self, app, name, text, rect=None, align="left"):
        super().__init__()

        # Generate context window
        self.rect = app.stg.window.rect  # Generate sprite rect from main window
        self.image = pg.Surface(self.rect.size, pg.SRCALPHA, 32)  # Surface on which sprite is blit on
        collection = [line.split('\n') for line in text.splitlines()]  # Get single lines from text
        x, y = rect.topleft  # Initial blit coordinates
        self.name = name
        self.forced_reconstruct = False  # Flag to determine if vertices for vbo must be reconstructed every frame

        # adjust x blit position depending on align
        if align == "left":
            pass
        elif align == "right":
            x += rect.width
        elif align == "center":
            x = rect.centerx

        # Extract each line and blit to surface
        for lines in collection:
            words = lines[0]
            w_surf = app.stg.util.text_font.render(words, True, app.stg.util.text_color)
            w_width, w_height = w_surf.get_size()

            # adjust x blit position depending on line length
            if align == "left":
                pass
            elif align == "right":
                x -= w_width
            elif align == "center":
                x -= w_width/2

            # Blit line of text to surface
            self.image.blit(w_surf, (x, y))

            # Update blit x and y position for successive line
            if align == "left":
                x = rect.topleft[0]
            elif align == "right":
                x = rect.topleft[0] + rect.width
            elif align == "center":
                x = rect.centerx
            y += w_height

    def update(self, app):
        pass


class FpsSprite(pg.sprite.Sprite):
    def __init__(self, app):
        super().__init__()
        self.image = pg.Surface((100, 100), pg.SRCALPHA, 32)
        self.image.blit(app.stg.util.text_font.render(f'{app.clock.get_fps() :.0f}',
                                                              True, app.stg.util.text_color), (0, 0))
        self.rect = pg.Rect(0, 0, 100, 100)
        self.name = "fps_counter"
        self.forced_reconstruct = False  # Flag to determine if vertices for vbo must be reconstructed every frame

    def update(self, app):
        if app.custom_events.FPS_EVENT in [e.type for e in app.event_list]:
            self.image = pg.Surface((100, 100), pg.SRCALPHA, 32)
            self.image.blit(app.stg.util.text_font.render(f'{app.clock.get_fps() :.0f}',
                                                                  True, app.stg.util.text_color), (0, 0))
