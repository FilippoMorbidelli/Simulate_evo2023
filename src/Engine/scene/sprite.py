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
            with open(f'src/shaders/2D_sprite.vert') as file:
                vertex_shader_sprite = file.read()

            with open(f'src/shaders/2D_sprite.frag') as file:
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
        if sprite.to_render:
            if sprite.name not in self.gl_vertices or sprite.to_rebuild or sprite.oneshot_rebuild:
                sprite.oneshot_rebuild = False
                self.scale_sprite(sprite)
                w, h = surface.get_size()
                left, top, width, height = sprite.rect
                right = left + width
                bottom = top + height
                corners = [  # Convert vertex
                    (left / w * 2 - 1, 1 - bottom / h * 2),  # Bottom-left corner
                    (right / w * 2 - 1, 1 - bottom / h * 2),  # Bottom-right corner
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
            self.get_texture(sprite.image).use(location=0)  # Retrieve the texture and overwrite it in loc=0
            self.get_vao().render()  # Render sprite

    def draw2d(self):
        try:
            self.gl_buffer.ctx.fbo.depth_mask = False  # TO DO - find better way
        except Exception:
            pass
        for sprite in self:
            self.render(sprite, self.app.screen)
        try:
            self.gl_buffer.ctx.fbo.depth_mask = True  # TO DO - find better way
        except Exception:
            pass

    def update(self, app):
        for sprite in self:
            sprite.update(app)

    def scale_sprite(self, sprite):
        # Get Screen size
        w, h = self.app.screen.get_size()
        # Compute scale factor
        sf_w = w / self.app.stg.window.w_ref
        sf_h = h / self.app.stg.window.h_ref
        # Get Sprite size
        sp_left, sp_top, sp_w, sp_h = sprite.rect
        # Scale dims and anchor
        sp_left = sp_left * sf_w
        sp_top = sp_top * sf_h
        sp_w = sp_w * sf_w
        sp_h = sp_h * sf_h
        # Update sprite
        sprite.image = pg.transform.scale(sprite.image, (sp_w, sp_h))
        sprite.rect = pg.Rect(sp_left, sp_top, sp_w, sp_h)
        sprite.mask = pg.mask.from_surface(sprite.image)


# 2D Sprite classes ----------------------------|
class DynamicSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, name, ext, flag):
        super().__init__()
        self.sprite = pg.image.load(f'src/assets/{scene}/{name}.{ext}').convert_alpha()
        self.rect = self.sprite.get_rect(topleft=app.mouse)  # Generate sprite rect from main window
        self.rect.size = (48, 48)
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        self.name = f"dynamic_{name}"

        # Flags
        self.to_render = True
        self.to_interact = flag  # Flag to determine if button is dynamic or not
        self.to_rebuild = True  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def update(self, app):
        self.rect.topleft = app.mouse


class OverlaySprite(pg.sprite.Sprite):
    def __init__(self, app, scene, name, ext, flag):
        super().__init__()
        self.sprite = pg.image.load(f'src/assets/{scene}/overlay_{name}.{ext}').convert_alpha()
        self.rect = self.sprite.get_rect(center=(960, 540))  # Generate sprite rect from main window
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        self.name = f"overlay_{name}"

        # Flags
        self.to_render = True
        self.to_interact = flag  # Flag to determine if button is dynamic or not
        self.to_rebuild = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def update(self, *args):
        pass


class BackgroundSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, button, ext, flag, anchor = (0, 0), name_add = ""):
        super().__init__()
        #self.rect = app.stg.window.rect  # Generate sprite rect from main window
        self.sprite = pg.image.load(f'src/assets/{scene}/background_{button}.{ext}').convert_alpha()
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        wh = self.sprite.get_size()
        self.rect = pg.Rect(anchor[0], anchor[1], wh[0], wh[1])
        self.name = f"background_{button}" + name_add

        # Flags
        self.to_render = True
        self.to_interact = flag  # Flag to determine if button is dynamic or not
        self.to_rebuild = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def update(self, *args):
        pass


class ButtonSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, name, ext, flag, anchor = (0, 0), name_add = "", threshold = 127):
        super().__init__()
        self.app = app
        self.sprite_F = pg.image.load(f'src/assets/{scene}/button_{name}_F.{ext}').convert_alpha()
        self.sprite_T = pg.image.load(f'src/assets/{scene}/button_{name}_T.{ext}').convert_alpha()
        self.image    = self.sprite_F
        self.mask = pg.mask.from_surface(self.image, threshold)
        wh = self.sprite_F.get_size()
        self.rect = pg.Rect(anchor[0], anchor[1], wh[0], wh[1])

        self.over : int  = 0 #self.mask.get_at(app.mouse)  # Add check if mouse is over from start
        self.name : str  = f"button_{name}" + name_add

        # Flags
        self.to_render = True
        self.to_interact : bool = flag  # Flag to determine if sprite is dynamic or not
        self.to_rebuild : bool = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild : bool = False # Flag to rebuild sprite oneshot

    def update(self, *args):
        pass

    def blit_text(self, text = "", anchor=(0, 0)):
        blit_text_to_surf(self.app, self, text, anchor=anchor)
        self.oneshot_rebuild = True


class StaticAltSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, flag, alts, xy, ext = "svg"):
        super().__init__()
        # Save app pointer
        self.app = app
        # Generate rect and load associated textures
        self.sprite_dict = {}
        for a in alts:
            self.sprite_dict[a] = pg.image.load(f'src/assets/{scene}/static_alt_{a}.{ext}').convert_alpha()
        wh = self.sprite_dict[a].get_size()
        # Sprite render data (set to default sprite)
        self.rect = pg.Rect(xy[0], xy[1], wh[0], wh[1])  # Generate sprite rect from main window
        self.image = self.sprite_dict[a]
        # Set other data/info
        self.alt = a
        self.mask = pg.mask.from_surface(self.image)
        self.name = f"static_alt_{a}"

        # Flags
        self.to_render = True
        self.to_interact = flag  # Flag to determine if sprite is dynamic or not
        self.to_rebuild = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def alternate(self, alt):
        # Switch active sprite
        self.image = self.sprite_dict[alt]
        self.rect.size = self.sprite_dict[alt].get_size()
        self.alt = alt
        # Update pointer in Scene
        self.app.scene.sprite_util["SaveLoad"] = alt


class UtilityStaticText(pg.sprite.Sprite):
    def __init__(self, app, name, text, rect=None, align="left"):
        super().__init__()

        # Generate context window
        self.rect = app.stg.window.rect  # Generate sprite rect from main window
        self.image = pg.Surface(self.rect.size, pg.SRCALPHA, 32)  # Surface on which sprite is blit on
        collection = [line.split('\n') for line in text.splitlines()]  # Get single lines from text
        x, y = rect.topleft  # Initial blit coordinates
        self.name = name

        # Flags
        self.to_render = True
        self.to_interact = False
        self.to_rebuild = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild = False  # Flag to rebuild sprite oneshot

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
            w_surf = app.stg.font_util.text_font.render(words, True, app.stg.font_util.text_color)
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
        self.image.blit(app.stg.font_util.text_font.render(f'{app.clock.get_fps() :.0f}',
                                                      True, app.stg.font_util.text_color), (0, 0))
        self.rect = pg.Rect(0, 0, 100, 100)
        self.name = "fps_counter"

        # Flags
        self.to_render = True
        self.to_interact = False
        self.to_rebuild = False  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def update(self, app):
        if app.custom_events.FPS_EVENT in [e.type for e in app.event_list]:
            self.image = pg.Surface((100, 100), pg.SRCALPHA, 32)
            self.image.blit(app.stg.font_util.text_font.render(f'{app.clock.get_fps() :.0f}',
                                                                  True, app.stg.font_util.text_color), (0, 0))


class MovingSprite(pg.sprite.Sprite):
    def __init__(self, app, scene, name, ext, anchor, mov, rot):
        super().__init__()
        self.app = app
        self.sprite = pg.image.load(f'src/assets/{scene}/mov_{name}.{ext}').convert_alpha()
        self.image = self.sprite
        self.mask = pg.mask.from_surface(self.image)
        self.or_rect = pg.Rect(anchor[0], anchor[1], self.sprite.get_width(), self.sprite.get_height())
        self.rect = pg.Rect(anchor[0], anchor[1], self.sprite.get_width(), self.sprite.get_height())

        self.over: int = 0  # self.mask.get_at(app.mouse)  # Add check if mouse is over from start
        self.name: str = f"button_{name}"

        # Attributes used to compute movement
        self.mov_logic = mov[0]  # Lambda function that determines sprite behaviour
        self.mov_speed = mov[1]  # Speed in frames

        self.rot_logic = rot[0]  # Lambda function that determines sprite behaviour
        self.rot_speed = rot[1]  # Speed in frames

        # Flags
        self.to_render   = True
        self.to_interact = False  # Flag to determine if sprite is dynamic or not
        self.to_rebuild  = True  # Flag to determine if vertices for vbo must be reconstructed every frame
        self.oneshot_rebuild = False  # Flag to rebuild sprite oneshot

    def update(self, app):
        # Init image
        mr_image = self.sprite
        mr_rect = self.or_rect

        # Compute motion
        if self.mov_logic:
            anchor = self.mov_logic(self.mov_speed, self.app.time)
            mr_rect.x = anchor[0]
            mr_rect.y = anchor[1]

        # Compute rotation
        if self.rot_logic:
            angle = self.rot_logic(self.rot_speed, self.app.time)
            mr_image = pg.transform.rotate(self.sprite, angle)
            mr_rect = mr_image.get_rect(center=mr_rect.center)

        # Finalize image
        self.image = mr_image
        self.rect = mr_rect

    def reset(self):
        self.image = self.sprite
        self.rect = self.or_rect

class UITextSprite(pg.sprite.Sprite):
    def __init__(self, app, blit_rect, xy, string_ptr, font, color = (255, 255, 255), dim = 22, name = ""):
        super().__init__()
        # Save Text Info
        self.app     = app
        self.string  = string_ptr
        self.font    = font
        self.color   = color
        self.dim     = dim
        self.topleft = xy
        self.name    = name
        self.image = pg.Surface((500, 120), pg.SRCALPHA, 32)
        self.rect = pg.Rect(blit_rect.left, blit_rect.top, 500, 120)

        # Sprite flags
        self.to_render = True
        self.to_interact = False
        self.to_rebuild = False
        self.oneshot_rebuild: bool = False  # Flag to rebuild sprite oneshot

    def update(self, app):
        _, rect = self.font.render(self.string["ui_string"], self.color)
        self.image = pg.Surface((500, 120), pg.SRCALPHA, 32)
        self.app.stg.font_util.ui_font.render_to(self.image, (self.topleft[0], self.topleft[1] - rect.height/2.2), self.string["ui_string"], (250,50,50))

def blit_text_to_surf(app, sprite, text, anchor = (0, 0)):
    text_surf = app.stg.font_util.ui_font.render(text, app.stg.font_util.text_color, size = 22)[0]
    # Blit text to sprite image
    sprite.image.blit(text_surf, anchor)
    sprite.sprite_F.blit(text_surf, anchor)
    sprite.sprite_T.blit(text_surf, anchor)