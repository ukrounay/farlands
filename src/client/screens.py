import enum

import pygame

from src.client.renderer import *
from src.shared.physics.objects import RigidBody
from src.shared.utilites import *

class Image(RigidBody):
    def __init__(self, x, y, offset, width, height, texture, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, width, height, texture, 0, gravity_enabled, is_immovable, is_physical)
        self.saved_screen_size = None
        self.saved_scale = None
        self.pos_px = Vec2(int(self.position.x), int(self.position.y))
        self.offset_pr = self.position - self.pos_px
        self.offset = offset + self.offset_pr
        self.children = []
        self.model_matrix = None

    def get_pos(self, screen_size):
        return self.pos_px

    def get_offset(self, screen_size):
        return self.offset + self.offset_pr * screen_size

    def update_model_matrix(self):
        self.model_matrix = create_transformation_matrix(
            position=self.get_pos(self.saved_screen_size),
            offset=self.get_offset(self.saved_screen_size),
            size=self.size,
            scale=self.saved_scale
        )

    def get_matrix(self, screen_size, scale):
        if self.model_matrix is None or self.saved_scale != scale or self.saved_screen_size != screen_size:
            self.saved_scale = scale
            self.saved_screen_size = screen_size
            self.update_model_matrix()
        return self.model_matrix


    def draw(self, renderer: Renderer, screen_size, scale, hovered, centered=True):
        model_matrix = self.get_matrix(screen_size, scale)
        renderer.draw_quad(self.texture, model_matrix)
        for child in self.children:
            child.draw(renderer, screen_size, scale, hovered, centered)

class Screen:
    def __init__(self, bg: Image | None, images, buttons):
        self.bg = bg
        self.images = images
        self.buttons = buttons
        pass

    def draw(self, renderer: Renderer, camera, mouse_pos, centered=True, custom_scale=0):
        screen_size = Vec2(camera.renderBounds.width, camera.renderBounds.height)
        if self.bg is not None:
            renderer.draw_image_cover(self.bg.texture, self.bg.size, screen_size, camera.scale)
        scale = camera.get_scale() if custom_scale==0 else custom_scale
        for image in self.images:
            image.draw(renderer, screen_size, scale, False, centered)

        for button in self.buttons:
            button.draw(renderer, screen_size, scale, button.is_hovered(screen_size, mouse_pos, scale, centered), centered)


class ButtonForm(enum.Enum):
    RECT = 1
    SQ45 = 2

class Button(Image):
    def __init__(self, x, y, offset, width, height, texture, form=ButtonForm.RECT, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, offset, width, height, texture, gravity_enabled, is_immovable, is_physical)
        self.form = form
        # if text != "":
        #     self.children += TextLabel()

    def is_pressed(self, mouse_pressed, screen_size, mouse_pos, scale):
        return mouse_pressed and self.is_hovered(screen_size, mouse_pos, scale)

    def is_hovered(self, screen_size, mouse_pos, scale, centered=True):
        of = self.get_offset(screen_size)
        pos = self.get_pos(screen_size) * scale + of
        size = self.size * scale
        mouse_pos = mouse_pos
        if self.form == ButtonForm.RECT:
            return \
                (pos.x - size.x * 0.5 < mouse_pos.x < pos.x + size.x * 0.5
                and pos.y - size.y * 0.5 < mouse_pos.y < pos.y + size.y * 0.5) \
                    if centered else \
                (pos.x < mouse_pos.x < pos.x + size.x
                and pos.y < mouse_pos.y < pos.y + size.y)

        if self.form == ButtonForm.SQ45:
            # print(mouse_pos, pos if centered else pos - size / 2, (size.x + size.y) / 2)
            return is_inside_rotated_square(mouse_pos, pos if centered else pos - size / 2, (size.x + size.y) / 2)
        return False


    def draw(self, renderer: Renderer, screen_size, scale, hovered, centered=True):
        model_matrix = self.get_matrix(screen_size, scale)

        if hovered:
            renderer.use_shader("outline")
            loc = renderer.get_current_uniform_locations()
            glUniform1f(loc["centered"], centered)
            glUniform1f(loc["outlineThickness"], 1)
            glUniform4f(loc["outlineColor"], 1,1,1,0.5)
            renderer.draw_quad(self.texture, model_matrix)
            renderer.use_shader("default")
        else:
            renderer.draw_quad(self.texture, model_matrix)


class ProgressBar(Image):
    def __init__(self, x, y, offset, width, height, texture, texture_fg, value=None, max_value=None, draw_text=True, font=None,
                 text_color=(255,255,255,255),
                 percents=False, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, offset, width, height, texture, gravity_enabled, is_immovable, is_physical)
        self.texture_fg = texture_fg
        self.value = value
        self.max_value = max_value
        self.draw_text = draw_text
        self.percents = percents
        self.text_color = text_color
        self.shadow_color = [max(0, self.text_color[x]-128) for x in range(3)] + [255]
        self.text_label = TextLabel(x, y, offset, font, "")
        if draw_text:
            self.children.append(self.text_label)

    # def get_matrix(self, screen_size, scale):
    #     return create_transformation_matrix(
    #         position=self.get_pos(screen_size),
    #         offset=self.get_offset(screen_size),
    #         size=self.size,
    #         scale=scale
    #     )

    def draw(self, renderer: Renderer, screen_size, scale, hovered=False, centered=True):
        model_matrix = self.get_matrix(screen_size, scale)
        value = self.value()
        value_coef = value / self.max_value
        progress = min(1, max(0, value_coef))
        cropped_model_matrix = create_transformation_matrix(
            position = self.get_pos(screen_size) + Vec2(self.size.x * (progress * 0.5 - 0.5)) if centered else Vec2(),
            offset=self.get_offset(screen_size),
            size=self.size*Vec2(progress, 1),
            scale=scale
        )
        renderer.draw_quad(self.texture, model_matrix)
        renderer.draw_quad(self.texture_fg, cropped_model_matrix, Vec4(0,0, progress, 1))
        if self.draw_text:
            of = (self.get_pos(screen_size) ) * scale
            of += self.get_offset(screen_size)
            text = f"{int(progress*100.0)}%" if self.percents else f"{value}"
            self.text_label.set_text(text)
        for child in self.children:
            child.draw
            # renderer.draw_text(renderer.default_shader_uniforms, of.x + scale, of.y + scale,
            #                     text, renderer.default_font, self.shadow_color,
            #                     DEBUG_FONT_SIZE, True)
            # renderer.draw_text(renderer.default_shader_uniforms, of.x, of.y,
            #                     text, renderer.default_font, self.text_color,
            #                     DEBUG_FONT_SIZE, True)

class TextLabel(Image):
    def __init__(self, x, y, offset, font, text, color=(255, 255, 255, 255), gravity_enabled=False):
        # Width/height will be overwritten on text update
        self.font = font
        self.color = color
        self.text = text
        self.surface = None
        self.texture_id = None
        self._dirty = True

        # Dummy texture and size init (will update later)
        super().__init__(x, y, offset, width=1, height=1, texture=0, gravity_enabled=gravity_enabled)
        self.update_texture()  # Initializes texture and correct size

    def set_text(self, text, color=None):
        if text != self.text or (color and color != self.color):
            self.text = text
            if color:
                self.color = color
            self._dirty = True

    # def update_texture(self):
    #     if not self._dirty or self.font is None:
    #         return
    #
    #     self.surface = self.font.render(self.text, True, self.color)
    #     surf = self.surface
    #     width, height = surf.get_width(), surf.get_height()
    #     self.size = Vec2(width, height)
    #
    #     if self.texture_id is None:
    #         self.texture_id = glGenTextures(1)
    #
    #     previous_texture = glGetIntegerv(GL_TEXTURE_BINDING_2D)
    #
    #     glBindTexture(GL_TEXTURE_2D, self.texture_id)
    #     surf_data = pygame.image.tostring(surf, "RGBA", True)
    #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, surf_data)
    #
    #     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    #     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    #
    #     glBindTexture(GL_TEXTURE_2D, previous_texture)
    #
    #     self.texture = self.texture_id
    #
    #     if self.saved_screen_size is not None or self.saved_scale is not None:
    #         self.update_model_matrix()
    #         self._dirty = False

    def update_texture(self):
        if not self._dirty or self.font is None:
            return

        lines = self.text.split("\n")
        line_surfaces = [self.font.render(line, True, self.color) for line in lines]

        # Calculate total size
        line_height = self.font.get_linesize()
        width = max(s.get_width() for s in line_surfaces)
        height = line_height * len(line_surfaces)

        # Create full surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for i, line_surf in enumerate(line_surfaces):
            self.surface.blit(line_surf, (0, i * line_height))

        surf = self.surface
        self.size = Vec2(width, height)

        if self.texture_id is None:
            self.texture_id = glGenTextures(1)

        previous_texture = glGetIntegerv(GL_TEXTURE_BINDING_2D)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        surf_data = pygame.image.tostring(surf, "RGBA", True)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, surf_data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glBindTexture(GL_TEXTURE_2D, previous_texture)

        self.texture = self.texture_id

        if self.saved_screen_size is not None or self.saved_scale is not None:
            self.update_model_matrix()

        self._dirty = False

    def update_model_matrix(self):
        self.model_matrix = create_transformation_matrix(
            position=self.get_pos(self.saved_screen_size),
            offset=self.get_offset(self.saved_screen_size),
            size=self.size,
            scale=1
        )

    def draw(self, renderer: Renderer, screen_size, scale, hovered=False, centered=True):
        if self._dirty:
            self.update_texture()
        if not centered: renderer.use_vao(renderer.non_centered_vao)
        model_matrix = self.get_matrix(screen_size, scale)
        renderer.draw_quad(self.texture_id, model_matrix)
        if not centered: renderer.use_vao(renderer.quad_vao)

    def dispose(self):
        if self.texture_id:
            glDeleteTextures([self.texture_id])
            self.texture_id = None
