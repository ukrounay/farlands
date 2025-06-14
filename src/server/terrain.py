from perlin_noise import PerlinNoise

from src.shared.utilites import *






tile_type_codes = {
    0: "air", "air": 0,
    255: "ground", "ground": 255,
    254: "dirt", "dirt": 254,
    253: "grass_dirt", "grass_dirt": 253,
    128: "stone", "stone": 128,
    252: "cave_dirt", "cave_dirt": 252,
    251: "cave_grass_dirt", "cave_grass_dirt": 251,
    127: "cave_stone", "cave_stone": 127,
}


def generate_platforms(seed=1, terrain_delta=20, terrain_quality=5, offset=Vec2(0, 0), size=Vec2(0, 0)):
    # Parameters
    octaves = 4  # Higher octaves for smoother noise
    scale = 100  # Smaller scale for larger, smoother features

    # Create Perlin noise generator
    caves = PerlinNoise(octaves=octaves, seed=seed)
    materials = PerlinNoise(octaves=octaves + 3, seed=seed + 1)
    land_limiter = PerlinNoise(octaves=octaves + 2, seed=seed + 2)

    # Generate a heightmap with Perlin noise
    width, height = size.x, size.y
    heightmap = np.zeros((height, width))
    materialmap = np.zeros((height, width))
    heightline = np.zeros(width)
    upperline = np.zeros(width)

    for x in range(width):
        nx = (offset.x + x) / scale

        for quality in range(terrain_quality):
            heightline[x] += land_limiter([nx, quality])
        heightline[x] /= terrain_quality
        heightline[x] = (heightline[x] + 1) / 2 * terrain_delta

        upperline[x] = ((caves([nx, (offset.y - 1) / scale]) + 1) / 2 * 255)

        for y in range(height):

            ny = (offset.y + y) / scale
            heightmap[y, x] = ((caves([nx, ny]) + 1) / 2 * 255)
            materialmap[y, x] = materials([nx, ny])

            cave = heightmap[y, x] < 100
            if heightline[x] > y + offset.y:
                heightmap[y, x] = tile_type_codes["air"]
            else:
                stone = "cave_stone" if cave else "stone"
                grass_dirt = "cave_grass_dirt" if cave else "grass_dirt"
                dirt = "cave_dirt" if cave else "dirt"
                if abs(y + offset.y - heightline[x]) > terrain_delta:
                    heightmap[y, x] = tile_type_codes[stone]
                else:
                    if (upperline[x] if y==0 else heightmap[y-1, x]) == tile_type_codes["air"]:
                        heightmap[y, x] = tile_type_codes[grass_dirt]
                    else: heightmap[y, x] = tile_type_codes[dirt]

    # Normalize the heightmap to the range [0, 255] for image saving

    # print(heightmap.max(), heightmap.min(), heightline.max(), materialmap.min(), materialmap.max(), materialmap.min())

    # heightmap = np.array([heightmap])
    # heightmap = 255 - heightmap  # Invert to make higher values represent higher platforms

    # for x in range(width):
    #     for y in range(height):

    # for y in range(height):
    #     for x in range(width):
    #         heightmap[x, y] = ((heightmap[x, y] - 128) / 128.0) * platform_height if heightmap[x, y] > 127 else 0
    #
    # platforms = np.zeros_like(heightmap)
    #
    # for y in range(width):
    #     h = max(heightmap[y, :])
    #     for x in range(int(height/2 - h), height):
    #         platforms[x, y] = 255

    # Save the heightmap as an image
    # image = Image.fromarray(heightmap, mode='L')
    #
    # image.save(f'data/terrain/{offset}.png')

    return heightmap




# import numpy as np
# from perlin_noise import PerlinNoise
#
# from src.shared.utilites import *
#
#
# # Define the tile registry
# # tile_registry = {
# #     "grass": "assets/textures/grass.png",
# #     "ground": "assets/textures/ground.png",
# #     "stone": "assets/textures/stone.png"
# # }
#
# # # Load a texture from a file
# # def load_texture(file):
# #     texture_surface = pygame.image.load(file)
# #     texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
# #     width, height = texture_surface.get_size()
# #
# #     texture = glGenTextures(1)
# #     glBindTexture(GL_TEXTURE_2D, texture)
# #     glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
# #
# #     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
# #     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
# #
# #     return texture, width, height
#
# # def generate_terrain(width, height, biome, output_file):
# #     terrain = {
# #         "biome": biome,
# #         "tiles": []
# #     }
# #
# #     for y in range(height):
# #         for x in range(width):
# #             tile_id = random.choice(list(tile_registry.keys()))  # Randomly choose a tile ID
# #             terrain["tiles"].append({
# #                 "id": tile_id,
# #                 "pos": [x, y]
# #             })
# #
# #     # Save terrain to a JSON file
# #     with open(output_file, 'w') as f:
# #         json.dump(terrain, f, indent=4)
# #
# #     print(f"Terrain generated and saved to {output_file}")
# #
#
#
# # Generate terrain using Perlin Noise
# def generate_terrain_with_noise(width, height, biome, output_file):
#     # terrain = {
#     #     "biome": biome,
#     #     "tiles": []
#     # }
#
#     # # Parameters for Perlin noise
#     # scale = 100.0
#     # octaves = 6
#     # persistence = 0.5
#     # lacunarity = 2.0
#
#     # for y in range(height):
#     #     for x in range(width):
#     #         # Generate a height value using Perlin noise
#     #         block_value = noise.pnoise2(x / scale, y / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=width, repeaty=height, base=0)
#
#     #         # Normalize the height value to be between 0 and 1
#     #         height_value = (height_value + 1) / 2
#
#     #         # Determine the tile based on the height value
#     #         if height_value > 0.7:
#     #             tile_id = "grass"
#     #         elif height_value > 0.4:
#     #             tile_id = "ground"
#     #         else:
#     #             tile_id = "stone"
#
#     #         terrain["tiles"].append({
#     #             "id": tile_id,
#     #             "pos": [x, y]
#     #         })
#
#     # # Save terrain to a JSON file
#     # with open(output_file, 'w') as f:
#     #     json.dump(terrain, f, indent=4)
#     pass
#
#
# tile_type_codes = {
#     0: "air", "air": 0,
#
#     81: "cave_stone", "cave_stone": 81,
#     82: "cave_ground", "cave_ground": 82,
#     83: "cave_grass", "cave_grass": 83,
#
#     180: "ground", "ground": 180,
#     200: "grass", "grass": 200,
#
#     128: "stone", "stone": 128,
#
#     129: "metal_ore", "metal_ore": 129,
#     130: "precious_stone", "precious_stone": 130,
# }
#
#
# def generate_platforms(seed=1, terrain_delta=10, terrain_quality=5, offset=Vec2(0, 0), size=Vec2(0, 0)):
#     # Parameters
#     octaves = 4  # Higher octaves for smoother noise
#     scale = 100  # Smaller scale for larger, smoother features
#
#     # Create Perlin noise generator
#     caves = PerlinNoise(octaves=octaves, seed=seed)
#     materials = PerlinNoise(octaves=octaves + 3, seed=seed + 1)
#     land_limiter = PerlinNoise(octaves=octaves + 2, seed=seed + 2)
#
#     # Generate a heightmap with Perlin noise
#     width, height = size.x, size.y
#     heightmap = np.zeros((height, width))
#     materialmap = np.zeros((height, width))
#     heightline = np.zeros(width)
#
#     for y in range(height):
#         for x in range(width):
#             nx = (offset.x + x) / scale
#             ny = (offset.y + y) / scale
#             for quality in range(terrain_quality):
#                 heightline[x] += land_limiter([nx, quality])
#             heightline[x] /= terrain_quality
#             heightline[x] = (heightline[x] + 1) / 2 * terrain_delta
#
#             up = ((caves([nx - 1, ny]) + 1) / 2 * 255) if y == 0 else heightmap[y - 1, x]
#             heightmap[y, x] = ((caves([nx, ny]) + 1) / 2 * 255)
#             materialmap[y, x] = ((materials([nx, ny]) + 1) / 2 * 255)
#
#             if heightline[x] > y + offset.y or (heightmap[y, x] < 100):
#                 heightmap[y, x] = tile_type_codes["air"]
#             else:
#                 if abs(y + offset.y - heightline[x]) > terrain_delta:
#                     heightmap[y, x] = tile_type_codes["stone"]
#                     if materialmap[y, x] > 250: heightmap[y, x] = tile_type_codes["metal_ore"]
#                     if materialmap[y, x] < 2: heightmap[y, x] = tile_type_codes["precious_stone"]
#                 else:
#                     if up == tile_type_codes["air"]:
#                         heightmap[y, x] = tile_type_codes["grass"]
#                     else:
#                         heightmap[y, x] = tile_type_codes["ground"]
#
#     # Normalize the heightmap to the range [0, 255] for image saving
#
#     # print(heightmap.max(), heightmap.min(), heightline.max(), materialmap.min(), materialmap.max(), materialmap.min())
#
#     # heightmap = np.array([heightmap])
#     # heightmap = 255 - heightmap  # Invert to make higher values represent higher platforms
#
#     # for x in range(width):
#     #     for y in range(height):
#
#     # for y in range(height):
#     #     for x in range(width):
#     #         heightmap[x, y] = ((heightmap[x, y] - 128) / 128.0) * platform_height if heightmap[x, y] > 127 else 0
#     #
#     # platforms = np.zeros_like(heightmap)
#     #
#     # for y in range(width):
#     #     h = max(heightmap[y, :])
#     #     for x in range(int(height/2 - h), height):
#     #         platforms[x, y] = 255
#
#     # Save the heightmap as an image
#     # image = Image.fromarray(heightmap, mode='L')
#     #
#     # image.save(f'data/terrain/{offset}.png')
#
#     return heightmap
#
# # Generate platform terrain
# # platforms = generate_platforms(10, offset=vec2(10,0), size=vec2(16,16))
#
# # def load_terrain(input_file):
# #     with open(input_file, 'r') as f:
# #         terrain = json.load(f)
# #
# #     game_objects = []
# #
# #     for tile in terrain['tiles']:
# #         tile_id = tile['id']
# #         pos = tile['pos']
# #
# #         if tile_id in tile_registry:
# #             texture, width, height = load_texture(tile_registry[tile_id])
# #             game_object = GameObject(pos[0] * width, pos[1] * height, width, height, texture, 1, False)
# #             game_objects.append(game_object)
# #
# #     return game_objects
#
