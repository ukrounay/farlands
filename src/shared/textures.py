import os
import json
from typing import Any

import pygame
import numpy as np
from numpy import ndarray, dtype
from pygame.locals import *
from OpenGL.GL import *

from src.shared.globals import *
from src.shared.utilites import *







def get_abs_path(path):
    return path
    return os.path.join(os.path.dirname(__file__), path)


def surface_to_texture(text_surface):
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_size()

    # Generate a new texture ID
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    # Upload the texture data
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    return texture_id, width, height


def create_test_texture(color=(255, 0, 0, 255)):
    texture_surface = pygame.Surface((64, 64))
    texture_surface.fill(color)
    texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
    width, height = texture_surface.get_size()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    return texture, width, height

# Helper function to load textures
def load_texture(file):
    try:
        file = get_abs_path(file)
        texture_surface = pygame.image.load(file)
        texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
        width, height = texture_surface.get_size()

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        print(f"Loaded texture: {file} ({width}x{height})")
        return texture, width, height

    except pygame.error as e:
        print(f"Failed to load texture: {file} - {e}")
        return create_test_texture()




# Load texture paths from JSON
def load_textures_from_json(json_file):
    json_file = get_abs_path(json_file)

    with open(json_file) as f:
        texture_map = json.load(f)

    textures = {}
    texture_dict = {}
    for key, value in texture_map.items():
        if isinstance(value, dict):
            textures[key] = {}
            if key == "tiles": texture_dict = value
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    textures[key][sub_key] = []
                    for entry in sub_value:
                        textures[key][sub_key].append(load_texture(os.path.join('assets/textures', entry)))
                else:
                    textures[key][sub_key] = load_texture(os.path.join('assets/textures', sub_value))

        else:
            textures[key] = load_texture(os.path.join('assets/textures', value))

    return textures, texture_dict


class Tilemap:
    uv_data: dict
    atlas_texture: tuple[Any | None, int, int]
    
    def __init__(self, tiles_dict):

        tile_keys = list(tiles_dict.keys())
        tile_images = [pygame.image.load(str(os.path.join('assets/textures', path))).convert_alpha() for path in tiles_dict.values()]

        atlas_columns = int(np.ceil(np.sqrt(len(tile_images))))
        atlas_rows = int(np.ceil(len(tile_images) / atlas_columns))

        atlas_width = atlas_columns * TILE_SIZE
        atlas_height = atlas_rows * TILE_SIZE

        atlas_surface = pygame.Surface((atlas_width, atlas_height), pygame.SRCALPHA)

        self.uv_data = {}

        for idx, (key, img) in enumerate(zip(tile_keys, tile_images)):
            x = (idx % atlas_columns) * TILE_SIZE
            y = (idx // atlas_columns) * TILE_SIZE
            atlas_surface.blit(img, (x, y))

            u = x / atlas_width
            v = y / atlas_height
            w = TILE_SIZE / atlas_width
            h = TILE_SIZE / atlas_height

            self.uv_data[key] = {
                "uv": (u, v, w, h),
                "matrix": uv_transform_matrix(u, v, w, h)
            }

        # Convert the atlas surface to OpenGL texture
        self.atlas_texture = surface_to_texture(atlas_surface)[0]


def uv_transform_matrix(u, v, w, h):
    return np.array([
        [w, 0, 0, 0],
        [0, h, 0, 0],
        [0, 0, 1, 0],
        [u, v, 0, 1]
    ], dtype=np.float32)




