import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GLUT import c_void_p

from src.shared.globals import *
from src.shared.textures import surface_to_texture
from src.shared.utilites import Vec2, matrices, create_transformation_matrix


class Renderer:
    def __init__(self, default_font):
        self.default_font = default_font
        # Load Shaders
        self.default_shader = load_shader("default.vert", "default.frag")
        self.outline_shader = load_shader("outline.vert", "outline.frag")
        self.postprocess_shader = load_shader("postprocess.vert", "postprocess.frag")

        self.default_shader_uniforms = {
            "screenSize": glGetUniformLocation(self.default_shader, "screenSize"),
            "projectionMatrix": glGetUniformLocation(self.default_shader, "projectionMatrix"),
            "modelMatrix": glGetUniformLocation(self.default_shader, "modelMatrix"),
            "uvTransform": glGetUniformLocation(self.default_shader, "uvTransform"),
            "transparency": glGetUniformLocation(self.default_shader, "transparency"),
            "fogColor": glGetUniformLocation(self.default_shader, "fogColor"),
        }
        self.outline_shader_uniforms = {
            "screenSize": glGetUniformLocation(self.outline_shader, "screenSize"),
            "projectionMatrix": glGetUniformLocation(self.outline_shader, "projectionMatrix"),
            "modelMatrix": glGetUniformLocation(self.outline_shader, "modelMatrix"),
            "uvTransform": glGetUniformLocation(self.outline_shader, "uvTransform"),
            "transparency": glGetUniformLocation(self.outline_shader, "transparency"),
            "outlineThickness": glGetUniformLocation(self.outline_shader, "outlineThickness"),
            "outlineColor": glGetUniformLocation(self.outline_shader, "outlineColor"),
            "fogColor": glGetUniformLocation(self.outline_shader, "fogColor"),
            "centered": glGetUniformLocation(self.outline_shader, "centered"),
        }
        self.postprocess_shader_uniforms = {
            "screenSize": glGetUniformLocation(self.postprocess_shader, "screenSize"),
            "projectionMatrix": glGetUniformLocation(self.postprocess_shader, "projectionMatrix"),
            "modelMatrix": glGetUniformLocation(self.postprocess_shader, "modelMatrix"),
            "uvTransform": glGetUniformLocation(self.postprocess_shader, "uvTransform"),
            "transparency": glGetUniformLocation(self.postprocess_shader, "transparency"),
        }

        # Create VAO and VBO
        self.non_centered_vao, _ = self.create_quad_buffers(centered=False)
        self.quad_vao, quad_vbo = self.create_quad_buffers()













    def create_quad_buffers(self, centered=True):
        # Vertices for a centered quad from (-0.5,-0.5) to (0.5,0.5)
        # This makes positioning and rotation more intuitive
        if centered:
            vertices = np.array([
                # positions (x, y)  # texture coords (u, v)
                -0.5, -0.5, 0.0, 0.0,  # Bottom left
                0.5, -0.5, 1.0, 0.0,  # Bottom right
                -0.5, 0.5, 0.0, 1.0,  # Top left
                0.5, 0.5, 1.0, 1.0  # Top right
            ], dtype=np.float32)
        else:
            vertices = np.array([
                # positions (x, y)  # texture coords (u, v)
                0.0, 0.0, 0.0, 0.0,  # Bottom left
                1.0, 0.0, 1.0, 0.0,  # Bottom right
                0.0, 1.0, 0.0, 1.0,  # Top left
                1.0, 1.0, 1.0, 1.0  # Top right
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



    def draw_quad(self, u_loc, texture, uv_transform, model_matrix, transparency=0):
        """
        Draw a textured quad with the specified transformation
            :param u_loc: current OpenGL shader program uniforms locations
            :param texture: OpenGL texture ID
            :param uv_transform: 3x3 matrix for UV transformation
            :param model_matrix: 4x4 model transformation matrix
            :param transparency: from 0 = fully opaque, to 1 = fully transparent
        """

        # Bind texture
        glBindTexture(GL_TEXTURE_2D, texture)

        # # Set texture uniform
        # texture_loc = glGetUniformLocation(shader_program, "ourTexture")
        # glUniform1i(texture_loc, 0)

        # Set UV transformation uniform
        uv_matrix = np.array(uv_transform, dtype=np.float32)
        glUniformMatrix4fv(u_loc["uvTransform"], 1, GL_FALSE, uv_matrix)

        # Set model matrix uniform
        glUniformMatrix4fv(u_loc["modelMatrix"], 1, GL_FALSE, model_matrix)

        glUniform1f(u_loc["transparency"], transparency)

        # Draw the quad
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        # print(model_matrix)


    def draw_text(self, shader_program_uniforms, x, y, text, font, color, font_size=DEBUG_FONT_SIZE, centered=False):
        scale = font_size/DEBUG_FONT_SIZE
        text_surface = font.render(str(text), True, color)
        texture_id, text_width, text_height = surface_to_texture(text_surface)
        size = Vec2(text_width, text_height)
        start = Vec2(x, y) if centered else Vec2(x, y) + size/2
        self.draw_quad(shader_program_uniforms, texture_id, matrices["normal"],
                  create_transformation_matrix(offset=start, size=size, scale=scale))
        # print(text)

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

        for i in range(0, len(text)):
            self.draw_text(shader_program_uniforms, 4, 4 + i * DEBUG_FONT_SIZE, text[i], font, (255, 255, 255, 255))

    def draw_image_cover(self, shader_program_uniforms, texture, image_size, screen_size, scale, uv_offset=0, uv_skew=0, transparency=0):
        self.draw_quad(shader_program_uniforms, texture,
                  matrices["normal"]
                  if uv_offset == 0 and uv_skew == 0
                  else create_transformation_matrix(Vec2(), Vec2(1, 1), Vec2(uv_offset, 0), skew_y=uv_skew),
                  create_transformation_matrix(offset=(screen_size / 2), size=image_size, scale=scale),
                  transparency)




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
    return shader

