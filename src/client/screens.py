import enum

from src.client.renderer import *
from src.shared.physics.objects import RigidBody
from src.shared.utilites import *

class Image(RigidBody):
    def __init__(self, x, y, width, height, texture, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, width, height, texture, 0, gravity_enabled, is_immovable, is_physical)
        self.pos_px = Vec2(int(self.position.x), int(self.position.y))
        self.pos_pr = self.position - self.pos_px

    def get_pos(self, screen_size):
        return self.pos_px + self.pos_pr * screen_size

class Screen:
    def __init__(self, bg: Image, images, buttons):
        self.bg = bg
        self.images = images
        self.buttons = buttons
        pass

    def draw(self, renderer: Renderer, camera, mouse_pos, centered=True):
        screen_size = Vec2(camera.renderBounds.width, camera.renderBounds.height)
        renderer.draw_image_cover(renderer.default_shader_uniforms, self.bg.texture, self.bg.size, screen_size, camera.scale)
        scale = camera.get_scale()
        for image in self.images:
            model_matrix = create_transformation_matrix(
                          offset=image.get_pos(screen_size),
                          size=image.size,
                          scale=scale
                      )
            renderer.draw_quad(renderer.default_shader_uniforms, image.texture, matrices["normal"], model_matrix)

        for button in self.buttons:
            model_matrix = create_transformation_matrix(
                          offset=button.get_pos(screen_size),
                          size=button.size,
                          scale=scale
                      )
            if button.is_hovered(screen_size, mouse_pos, scale, centered):
                glUseProgram(renderer.outline_shader)
                glUniform1f(renderer.outline_shader_uniforms["centered"], centered)
                glUniform1f(renderer.outline_shader_uniforms["outlineThickness"], 1)
                glUniform4f(renderer.outline_shader_uniforms["outlineColor"], 1,1,1,0.5)
                renderer.draw_quad(renderer.outline_shader_uniforms, button.texture, matrices["normal"], model_matrix)
                glUseProgram(renderer.default_shader)
            else:
                renderer.draw_quad(renderer.default_shader_uniforms, button.texture, matrices["normal"], model_matrix)



class ButtonForm(enum.Enum):
    RECT = 1
    SQ45 = 2

class Button(Image):
    def __init__(self, x, y, width, height, texture, form=ButtonForm.RECT, gravity_enabled=False, is_immovable=True, is_physical=False):
        super().__init__(x, y, width, height, texture, gravity_enabled, is_immovable, is_physical)
        self.form = form

    def is_pressed(self, mouse_pressed, screen_size, mouse_pos, scale):
        return mouse_pressed and self.is_hovered(screen_size, mouse_pos, scale)

    def is_hovered(self, screen_size, mouse_pos, scale, centered=True):
        pos = self.get_pos(screen_size)
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

