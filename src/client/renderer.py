import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GLUT import c_void_p
import OpenGL.GL as gl

from src.shared.globals import *
from src.shared.textures import surface_to_texture
from src.shared.utilites import Vec2, matrices, create_transformation_matrix


class Renderer:
    def __init__(self):
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
        }
        self.postprocess_shader_uniforms = {
            "screenSize": glGetUniformLocation(self.postprocess_shader, "screenSize"),
            "projectionMatrix": glGetUniformLocation(self.postprocess_shader, "projectionMatrix"),
            "modelMatrix": glGetUniformLocation(self.postprocess_shader, "modelMatrix"),
            "uvTransform": glGetUniformLocation(self.postprocess_shader, "uvTransform"),
            "transparency": glGetUniformLocation(self.postprocess_shader, "transparency"),
        }

        pass

    def render(self):


        pass









def create_quad_buffers(centered=True):
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



def draw_with_outline_shader(outline_shader, default_shader, tex_width, tex_height, texture, matrix, start, end, color = (1.0, 1.0, 1.0, 1.0)):
    glUseProgram(outline_shader)
    # Update shader uniforms
    glUniform2f(glGetUniformLocation(outline_shader, "texelOffset"), 1.0 / tex_width, 1.0 / tex_height)
    glUniform4f(glGetUniformLocation(outline_shader, "outlineColor"), *color)  # White outline
    glUniform1f(glGetUniformLocation(outline_shader, "outlineThreshold"), 0.1)

    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture)
    glUniform1i(glGetUniformLocation(outline_shader, "texture1"), 0)  # Set to use texture unit 0

    glBegin(GL_QUADS)
    set_quad(matrix, start, end)
    glEnd()
    glUseProgram(default_shader)

# def draw_quad(texture, matrix, start, end):
#     glBindTexture(GL_TEXTURE_2D, texture)
#     glBegin(GL_QUADS)
#     set_quad(matrix, start, end)
#     glEnd()

# def draw_quad(quad_vao, quad_vbo, texture, position, size):
#     glBindTexture(GL_TEXTURE_2D, texture)  # Bind texture
#
#     glBindVertexArray(quad_vao)  # Bind VAO
#
#     # Apply transformations (position + scaling)
#     glPushMatrix()
#     glTranslatef(position.x, position.y, 0)
#     glScalef(size.x, size.y, 1)
#
#     # Draw using modern OpenGL
#     glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
#
#     glPopMatrix()
#     glBindVertexArray(0)  # Unbind VAO

# def draw_quad(quad_vao, quad_vbo, texture, uv_matrix, position, size):
#     # Apply the UV transformation
#     transformed_uvs = np.array([
#         uv_matrix[0],  # Bottom-left  (u, v)
#         uv_matrix[1],  # Bottom-right (u, v)
#         uv_matrix[2],  # Top-left     (u, v)
#         uv_matrix[3],  # Top-right    (u, v)
#     ], dtype=np.float32)
#
#     # Update buffer with new UVs (bind before updating)
#     glBindBuffer(GL_ARRAY_BUFFER, quad_vbo)
#     glBufferSubData(GL_ARRAY_BUFFER, 8, transformed_uvs.nbytes, transformed_uvs)
#     glBindBuffer(GL_ARRAY_BUFFER, 0)
#
#     # Draw as before
#     glBindTexture(GL_TEXTURE_2D, texture)
#     glBindVertexArray(quad_vao)
#
#     glPushMatrix()
#     glTranslatef(position.x, position.y, 0)
#     glScalef(size.x, size.y, 1)
#
#     glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
#
#     glPopMatrix()
#     glBindVertexArray(0)

# def draw_quad(shader_program, quad_vao, texture, uv_transform, position, size):
#     glUseProgram(shader_program)  # Use the shader program
#
#     # Bind texture
#     glActiveTexture(GL_TEXTURE0)
#     glBindTexture(GL_TEXTURE_2D, texture)
#
#     # Set texture uniform
#     texture_loc = glGetUniformLocation(shader_program, "ourTexture")
#     glUniform1i(texture_loc, 0)  # 0 corresponds to GL_TEXTURE0
#
#     # Set UV transformation uniform
#     uv_matrix = np.array(uv_transform, dtype=np.float32)
#     uv_loc = glGetUniformLocation(shader_program, "uvTransform")
#     glUniformMatrix3fv(uv_loc, 1, GL_FALSE, uv_matrix)
#
#     # Set position and size uniforms
#     pos_loc = glGetUniformLocation(shader_program, "objectPosition")
#     size_loc = glGetUniformLocation(shader_program, "objectSize")
#     glUniform2f(pos_loc, position.x, position.y)
#     glUniform2f(size_loc, size.x, size.y)
#
#     # Draw the quad
#     glBindVertexArray(quad_vao)
#     glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
#     glBindVertexArray(0)

#
#
# def draw_quad(shader_program, quad_vao, texture, uv_transform, position, size):
#     glUseProgram(shader_program)  # Use the shader program
#
#     # Bind texture
#     glActiveTexture(GL_TEXTURE0)
#     glBindTexture(GL_TEXTURE_2D, texture)
#
#     # Set texture uniform
#     texture_loc = glGetUniformLocation(shader_program, "ourTexture")
#     glUniform1i(texture_loc, 0)  # 0 corresponds to GL_TEXTURE0
#
#     # Set UV transformation uniform
#     uv_matrix = np.array(uv_transform, dtype=np.float32)
#     uv_loc = glGetUniformLocation(shader_program, "uvTransform")
#     glUniformMatrix3fv(uv_loc, 1, GL_FALSE, uv_matrix)
#
#     # Set position and size uniforms for shader
#     pos_loc = glGetUniformLocation(shader_program, "objectPosition")
#     size_loc = glGetUniformLocation(shader_program, "objectSize")
#     glUniform2f(pos_loc, position.x, position.y)
#     glUniform2f(size_loc, size.x, size.y)
#
#     # Draw the quad
#     glBindVertexArray(quad_vao)
#     glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
#     glBindVertexArray(0)


def draw(shader_program, texture, uv_transform, model_matrix):
    """
    Draw a textured quad with the specified transformation

    Args:
        shader_program: OpenGL shader program
        quad_vao: Vertex Array Object for the quad
        texture: OpenGL texture ID
        uv_transform: 3x3 matrix for UV transformation
        model_matrix: 4x4 model transformation matrix
    """

    # Bind texture
    glBindTexture(GL_TEXTURE_2D, texture)

    # Set texture uniform
    texture_loc = glGetUniformLocation(shader_program, "ourTexture")
    glUniform1i(texture_loc, 0)

    # Set UV transformation uniform
    uv_matrix = np.array(uv_transform, dtype=np.float32)
    uv_loc = glGetUniformLocation(shader_program, "uvTransform")
    glUniformMatrix4fv(uv_loc, 1, GL_FALSE, uv_matrix)

    # Set model matrix uniform
    model_loc = glGetUniformLocation(shader_program, "modelMatrix")
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_matrix)

    # Draw the quad
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    # print(model_matrix)



def draw_quad(u_loc, quad_vao, texture, uv_transform, model_matrix, transparency=0):
    """
    Draw a textured quad with the specified transformation

    Args:
        shader_program: OpenGL shader program
        quad_vao: Vertex Array Object for the quad
        texture: OpenGL texture ID
        uv_transform: 3x3 matrix for UV transformation
        model_matrix: 4x4 model transformation matrix
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

def draw_quad_without_texture(matrix, start, end):
    glBindTexture(GL_TEXTURE_2D, 0)
    glBegin(GL_QUADS)
    set_quad(matrix, start, end)
    glEnd()

def set_quad(matrix, start, end):
    glTexCoord2f(matrix[0][0], matrix[0][1]); glVertex2f(start.x, start.y)
    glTexCoord2f(matrix[1][0], matrix[1][1]); glVertex2f(end.x, start.y)
    glTexCoord2f(matrix[2][0], matrix[2][1]); glVertex2f(end.x, end.y)
    glTexCoord2f(matrix[3][0], matrix[3][1]); glVertex2f(start.x, end.y)



def draw_text(shader_program_uniforms, quad_vao, x, y, text, font, color, font_size=DEBUG_FONT_SIZE, centered=False):
    scale = font_size/DEBUG_FONT_SIZE
    text_surface = font.render(str(text), True, color)
    texture_id, text_width, text_height = surface_to_texture(text_surface)
    size = Vec2(text_width, text_height)
    start = Vec2(x, y) if centered else Vec2(x, y) + size/2
    draw_quad(shader_program_uniforms, quad_vao, texture_id, matrices["normal"],
              create_transformation_matrix(offset=start, size=size, scale=scale))
    # print(text)

# Render your debug info with OpenGL
def draw_debug_info(shader_program_uniforms, quad_vao, font, clock, server_clock, player):
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
        draw_text(shader_program_uniforms, quad_vao, 4, 4 + i * DEBUG_FONT_SIZE, text[i], font, (255, 255, 255, 255))

def draw_image_cover(shader_program_uniforms, quad_vao, texture, image_size, screen_size, scale, uv_offset=0, uv_skew=0, transparency=0):
    # return
    # ratio = screen_size.x / screen_size.y
    # self_ratio = image_size.x / image_size.y
    # # h = screen_size.x / self_ratio if ratio > self_ratio else screen_size.y
    # # w = screen_size.y * self_ratio if ratio < self_ratio else screen_size.x
    # if ratio > self_ratio:
    #     h = screen_size.x / self_ratio
    #     w = screen_size.x
    # else:
    #     h = screen_size.y
    #     w = screen_size.y * self_ratio

    draw_quad(shader_program_uniforms, quad_vao, texture,
              matrices["normal"]
              if uv_offset == 0 and uv_skew == 0
              else create_transformation_matrix(Vec2(), Vec2(1, 1), Vec2(uv_offset, 0), skew_y=uv_skew),
              create_transformation_matrix(offset=(screen_size / 2), size=image_size, scale=scale),
              transparency)


# def draw_interface(camera, player, textures):
#     health = player.health/player.max_health
#     height = textures["ui"]["healthbar"][2]*0.5*camera.get_scale()
#     width = textures["ui"]["healthbar"][1]*camera.get_scale()
#     hb_bottom = screenHeight - 8;
#     hb_top = hb_bottom - height
#     hb_left = (screenWidth - width) / 2
#     hb_right = hb_left + width
#     top_half_matrix = [
#         [0, 0],
#         [1, 0],
#         [1, 0.5],
#         [0, 0.5]
#     ]
#     bottom_half_matrix = [
#         [0, 0.5],
#         [health, 0.5],
#         [health, 1],
#         [0, 1]
#     ]
#
#     draw_quad(textures["ui"]["healthbar"][0], bottom_half_matrix, Vec2(hb_left, hb_top), Vec2(hb_right, hb_bottom))
#     draw_quad(textures["ui"]["healthbar"][0], top_half_matrix, Vec2(hb_left, hb_top), Vec2(hb_right, hb_bottom))
#
#     text_surface = font.render(f"{int(player.health)}", True, (255, 255, 255, 255))
#     texture_id, text_width, text_height = surface_to_texture(text_surface)
#     needed_text_height = height-2*camera.get_scale()
#     scale = needed_text_height/text_height
#     start = Vec2(hb_top, hb_left) + camera.get_scale()
#     end = start + Vec2(text_width * scale, needed_text_height)
#     draw_quad(texture_id, matrices["normal"], start, end)
#
#     pass






# a try



    # def create_fbo_with_texture(width, height):
    #
    #     # Create texture
    #     texture = gl.glGenTextures(1)
    #     gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    #     gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0,
    #                     gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
    #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    #
    #     # Create framebuffer
    #     fbo = gl.glGenFramebuffers(1)
    #     gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    #     gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, texture, 0)
    #
    #     assert gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE
    #
    #     gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    #     return fbo, texture
    #
    #
    #
    #
    # def render_full_pipeline(sceneFBO, bloomFBO):
    #     # 1. Render scene to sceneFBO
    #     gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, sceneFBO)
    #     gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    #     render_scene()
    #
    #     # 2. Extract bright parts to bloomFBO
    #     gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, bloomFBO)
    #     gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    #     glUseProgram(bright_shader)
    #     draw_fullscreen_quad(sceneTexture)
    #
    #     # 3. Blur bloom (ping-pong)
    #     horizontal = True
    #     blur_amount = 10
    #     for i in range(blur_amount):
    #         gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, blurFBO1 if horizontal else blurFBO2)
    #         use_shader(blur_shader)
    #         set_uniform('direction', (1.0, 0.0) if horizontal else (0.0, 1.0))
    #         draw_fullscreen_quad(blurTexture2 if horizontal else blurTexture1)
    #         horizontal = not horizontal
    #
    #     # 4. Combine final image to screen
    #     gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    #     gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    #     use_shader(combine_shader)
    #     set_uniform('scene', sceneTexture)
    #     set_uniform('bloom', blurTexture1 if horizontal else blurTexture2)
    #     draw_fullscreen_quad()
