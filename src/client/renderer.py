import math
import os
from enum import Enum

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GLUT import c_void_p
from OpenGL.raw.GL.VERSION.GL_2_0 import glUniform4f, glUseProgram, glUniform1f
from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray

from src.shared.globals import TILE_SIZE, DEBUG_FONT_SIZE, UI_GAP
from src.shared.textures import uv_transform_matrix
from src.shared.utilites import Vec2, matrices, create_transformation_matrix, Vec4


def create_quad_buffers(centered=True):
    # Vertices for a centered quad from (-0.5,-0.5) to (0.5,0.5)
    # This makes positioning and rotation more intuitive
    if centered:
        vertices = np.array([
            # positions (x, y)  # texture coords (u, v)
            -0.5, -0.5, 0.0, 1.0,  # Bottom left
            0.5, -0.5, 1.0, 1.0,  # Bottom right
            -0.5, 0.5, 0.0, 0.0,  # Top left
            0.5, 0.5, 1.0, 0.0  # Top right
        ], dtype=np.float32)
    else:
        vertices = np.array([
            # positions (x, y)  # texture coords (u, v)
            0.0, 0.0, 0.0, 1.0,  # Bottom left
            1.0, 0.0, 1.0, 1.0,  # Bottom right
            0.0, 1.0, 0.0, 0.0,  # Top left
            1.0, 1.0, 1.0, 0.0  # Top right
        ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Position attribute
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), None)
    glEnableVertexAttribArray(0)

    # Texture coordinate attribute
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), c_void_p(2 * sizeof(GLfloat)))
    glEnableVertexAttribArray(1)

    return vao, vbo



# Load Shader Function
def load_shader(vertex_path, fragment_path):
    with open(os.path.join("shaders/", vertex_path), 'r') as v_file:
        vertex_src = v_file.read()
    with open(os.path.join("shaders/", fragment_path), 'r') as f_file:
        fragment_src = f_file.read()

    shader = compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER)
    )

    print(f"Loaded shader: {vertex_path}, {fragment_path}")
    return shader


class CursorType(Enum):
    DEFAULT = 0
    CROSSHAIR = 1


class Renderer:
    def __init__(self, default_font):
        self.shaders = {}
        self.uniform_locations = {}
        self.current_shader = None
        self.current_uniform_locations = None
        self.default_font = default_font
        self.bound_texture = None

        # Load Shaders

        self.add_shader_program("default", ["screenSize", "projectionMatrix", "modelMatrix", "uvTransform", "transparency", "fogColor"])
        self.add_shader_program("outline", ["screenSize", "projectionMatrix", "modelMatrix", "uvTransform", "transparency", "outlineThickness", "outlineColor", "fogColor", "centered"])
        self.add_shader_program("postprocess", ["screenSize", "projectionMatrix", "modelMatrix", "uvTransform", "transparency"])

        self.use_shader("default")

        # Create VAO and VBO
        self.non_centered_vao, _ = create_quad_buffers(centered=False)
        self.quad_vao, quad_vbo = create_quad_buffers()

    def use_vao(self, vao):
        glBindVertexArray(vao)

    def add_shader_program(self, name, uniforms: list):
        shader = load_shader(f"{name}.vert", f"{name}.frag")
        locations = {}
        for uniform_name in uniforms:
            locations[uniform_name] = glGetUniformLocation(shader, uniform_name)
        self.shaders[name] = shader
        self.uniform_locations[shader] = locations
        # print("locations: ", locations)

    def use_shader(self, shader_name):
        if shader_name == "" or shader_name not in self.shaders: return
        new_shader = self.shaders[shader_name]
        if new_shader != self.current_shader:
            glUseProgram(new_shader)
            self.current_shader = new_shader
            self.current_uniform_locations = self.uniform_locations[new_shader]

    def get_current_uniform_locations(self):
        return  self.current_uniform_locations

    def use_texture(self, texture):
        if self.bound_texture != texture:
            glBindTexture(GL_TEXTURE_2D, texture)
            self.bound_texture = texture


    def draw_quad(self, texture, model_matrix, uv_transform: Vec4 = Vec4(0,0,1,1), transparency=0, shader_program_name="default"):
        """
        Draw a textured quad with the specified transformation
            :param shader_program_name: shader program name to override default
            :param texture: OpenGL texture ID
            :param uv_transform: Vec4 representing texture starting point and size
            :param model_matrix: 4x4 model transformation matrix
            :param transparency: from 0 = fully opaque, to 1 = fully transparent
        """
        self.use_shader(shader_program_name)
        self.use_texture(texture)
        u_loc = self.get_current_uniform_locations()
        glUniform4f(u_loc["uvTransform"], *uv_transform.rgba)
        glUniformMatrix4fv(u_loc["modelMatrix"], 1, GL_FALSE, model_matrix)
        glUniform1f(u_loc["transparency"], transparency)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        err = glGetError()
        if err != GL_NO_ERROR:
            print(f"OpenGL error after binding texture: {hex(err)}")

    # def draw_text(self, shader_program_uniforms, x, y, text, font, color, font_size=DEBUG_FONT_SIZE, centered=False):
    #     scale = font_size/DEBUG_FONT_SIZE
    #     text_surface = font.render(str(text), True, color)
    #     texture_id, text_width, text_height = surface_to_texture(text_surface)
    #     size = Vec2(text_width, text_height)
    #     start = Vec2(x, y) if centered else Vec2(x, y) + size/2
    #     self.draw_quad(shader_program_uniforms, texture_id, matrices["normal"],
    #               create_transformation_matrix(offset=start, size=size, scale=scale))
    #     # print(text)

    # Render your debug info with OpenGL
    def draw_debug_info(self, shader_program_uniforms, font, clock, server_clock, player):
        text = []
        if clock is not None:
            text.append(f"FPS: {clock.get_fps():.2f}")
        if server_clock is not None:
            text.append(f"TPS: {server_clock.get_fps():.2f}")
        if player is not None:
            text.extend([
                f"pos (world): [x: {player.position.x:.0f} y: {player.position.y:.0f}]",
                f"pos (map): [x: {player.position.x/TILE_SIZE:.0f} y: {player.position.y/TILE_SIZE:.0f}]",
                f"vel: [x: {player.get_velocity().x:} y: {player.get_velocity().y:}]",
            ])

        # for i in range(0, len(text)):
        #     self.draw_text(shader_program_uniforms, 4, 4 + i * DEBUG_FONT_SIZE, text[i], font, (255, 255, 255, 255))

    def draw_image_cover(self, texture, image_size, screen_size, scale, uv_offset=0, uv_skew=0, transparency=0):
        uv_transform = Vec4(uv_offset, 0, uv_offset + 1, 1)
        self.draw_quad(texture,
                  create_transformation_matrix(offset=(screen_size / 2), size=image_size, scale=scale), uv_transform,
                  transparency=transparency)




