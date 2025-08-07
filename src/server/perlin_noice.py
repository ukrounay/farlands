import pygame
import math
import random
import numpy as np

# ---------- Perlin Noise Utilities ----------
def fade(t):
    return 6 * t**5 - 15 * t**4 + 10 * t**3

def lerp(a, b, t):
    return a + t * (b - a)

def grad(hash, x, y):
    h = hash & 7
    u = x if h < 4 else y
    v = y if h < 4 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

class Perlin2D:
    def __init__(self, seed=None):
        self.permutation = list(range(256))
        if seed is not None:
            random.seed(seed)
        random.shuffle(self.permutation)
        self.permutation += self.permutation  # duplicate for overflow

    def noise(self, x, y):
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255

        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = fade(xf)
        v = fade(yf)

        aa = self.permutation[self.permutation[xi] + yi]
        ab = self.permutation[self.permutation[xi] + yi + 1]
        ba = self.permutation[self.permutation[xi + 1] + yi]
        bb = self.permutation[self.permutation[xi + 1] + yi + 1]

        x1 = lerp(grad(aa, xf, yf), grad(ba, xf - 1, yf), u)
        x2 = lerp(grad(ab, xf, yf - 1), grad(bb, xf - 1, yf - 1), u)

        return (lerp(x1, x2, v) + 1) / 2  # Normalize to [0, 1]

# ---------- Chunk and Texture Generation ----------
CHUNK_SIZE = 128
NUM_CHUNKS_X = 2
NUM_CHUNKS_Y = 2
SCALE = 0.1  # Smaller = zoomed out

def generate_chunk(noise_func, x_offset, y_offset):
    chunk = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint8)
    for y in range(CHUNK_SIZE):
        for x in range(CHUNK_SIZE):
            nx = (x + x_offset * CHUNK_SIZE) * SCALE
            ny = (y + y_offset * CHUNK_SIZE) * SCALE
            value = noise_func(nx, ny)
            brightness = int(value * 255)
            chunk[y, x] = brightness
    return chunk

def combine_chunks(chunks, width, height):
    final_img = np.zeros((height * CHUNK_SIZE, width * CHUNK_SIZE), dtype=np.uint8)
    for j in range(height):
        for i in range(width):
            chunk = chunks[j * width + i]
            y_start = j * CHUNK_SIZE
            x_start = i * CHUNK_SIZE
            final_img[y_start:y_start + CHUNK_SIZE, x_start:x_start + CHUNK_SIZE] = chunk
    return final_img

# ---------- Main ----------
def main():
    pygame.init()

    noise_gen = Perlin2D(seed=42)
    chunks = []

    # Generate and store 4 chunks
    for j in range(NUM_CHUNKS_Y):
        for i in range(NUM_CHUNKS_X):
            chunk = generate_chunk(noise_gen.noise, i, j)
            chunks.append(chunk)

    # Combine chunks into one big image
    full_image = combine_chunks(chunks, NUM_CHUNKS_X, NUM_CHUNKS_Y)

    # Create Pygame surface
    surface = pygame.Surface((CHUNK_SIZE * NUM_CHUNKS_X, CHUNK_SIZE * NUM_CHUNKS_Y))
    for y in range(full_image.shape[0]):
        for x in range(full_image.shape[1]):
            v = full_image[y, x]
            surface.set_at((x, y), (v, v, v, v))

    # Save to file
    pygame.image.save(surface, "terrain_noise_chunks.png")
    print("Image saved as terrain_noise_chunks.png")

    pygame.quit()

if __name__ == "__main__":
    main()
