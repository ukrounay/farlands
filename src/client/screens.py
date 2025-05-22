import enum

from src.client.renderer import *
from src.shared.physics.objects import RigidBody
from src.shared.utilites import *

class Image(RigidBody):
    def __init__(self, x, y, offset, width, height, texture, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, width, height, texture, 0, gravity_enabled, is_immovable, is_physical)
        self.pos_px = Vec2(int(self.position.x), int(self.position.y))
        self.offset_pr = self.position - self.pos_px
        self.offset = offset + self.offset_pr

    def get_pos(self, screen_size):
        return self.pos_px

    def get_offset(self, screen_size):
        return self.offset + self.offset_pr * screen_size

    def get_matrix(self, screen_size, scale):
        return create_transformation_matrix(
            position=self.get_pos(screen_size),
            offset=self.get_offset(screen_size),
            size=self.size,
            scale=scale
        )

    def draw(self, renderer: Renderer, screen_size, scale, hovered, centered=True):
        model_matrix = self.get_matrix(screen_size, scale)
        renderer.draw_quad(renderer.default_shader_uniforms, self.texture, matrices["normal"], model_matrix)


class Screen:
    def __init__(self, bg: Image | None, images, buttons):
        self.bg = bg
        self.images = images
        self.buttons = buttons
        pass

    def draw(self, renderer: Renderer, camera, mouse_pos, centered=True, custom_scale=0):
        screen_size = Vec2(camera.renderBounds.width, camera.renderBounds.height)
        if self.bg is not None:
            renderer.draw_image_cover(renderer.default_shader_uniforms, self.bg.texture, self.bg.size, screen_size, camera.scale)
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
            print(mouse_pos, pos if centered else pos - size / 2, (size.x + size.y) / 2)
            return is_inside_rotated_square(mouse_pos, pos if centered else pos - size / 2, (size.x + size.y) / 2)
        return False


    def draw(self, renderer: Renderer, screen_size, scale, hovered, centered=True):
        model_matrix = self.get_matrix(screen_size, scale)

        if hovered:
            glUseProgram(renderer.outline_shader)
            glUniform1f(renderer.outline_shader_uniforms["centered"], centered)
            glUniform1f(renderer.outline_shader_uniforms["outlineThickness"], 1)
            glUniform4f(renderer.outline_shader_uniforms["outlineColor"], 1,1,1,0.5)
            renderer.draw_quad(renderer.outline_shader_uniforms, self.texture, matrices["normal"], model_matrix)
            glUseProgram(renderer.default_shader)
        else:
            renderer.draw_quad(renderer.default_shader_uniforms, self.texture, matrices["normal"], model_matrix)


class ProgressBar(Image):
    def __init__(self, x, y, offset, width, height, texture, texture_fg, value=None, max_value=None, draw_text=True,
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
        crop_matrix = create_transformation_matrix(size=Vec2(progress, 1))
        cropped_model_matrix = create_transformation_matrix(
            position = self.get_pos(screen_size) + Vec2(self.size.x * (progress * 0.5 - 0.5)) if centered else Vec2(),
            offset=self.get_offset(screen_size),
            size=self.size*Vec2(progress, 1),
            scale=scale
        )
        renderer.draw_quad(renderer.default_shader_uniforms, self.texture, matrices["normal"], model_matrix)
        renderer.draw_quad(renderer.default_shader_uniforms, self.texture_fg, crop_matrix, cropped_model_matrix)
        if self.draw_text:
            of = (self.get_pos(screen_size) ) * scale
            of += self.get_offset(screen_size)
            text = f"{int(progress*100.0)}%" if self.percents else f"{value}"
            renderer.draw_text(renderer.default_shader_uniforms, of.x + scale, of.y + scale,
                                text, renderer.default_font, self.shadow_color,
                                DEBUG_FONT_SIZE, True)
            renderer.draw_text(renderer.default_shader_uniforms, of.x, of.y,
                                text, renderer.default_font, self.text_color,
                                DEBUG_FONT_SIZE, True)

