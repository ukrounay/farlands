import math
from enum import Enum

import numpy as np

from src.shared.globals import TILE_SIZE


class Vec2:
    __slots__ = ('x', 'y', "xy")
    x: float
    y: float
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
        self.xy = [x,y]

    def __add__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        return Vec2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x - other.x, self.y - other.y)
        return Vec2(self.x - other, self.y - other)
    
    def __mul__(self, multiplier):
        if isinstance(multiplier, Vec2):
            return Vec2(self.x * multiplier.x, self.y * multiplier.y)
        return Vec2(self.x * multiplier, self.y * multiplier)
    
    def __div__(self, multiplier):
        if isinstance(multiplier, Vec2):
            return Vec2(self.x / multiplier.x, self.y / multiplier.y)
        return Vec2(self.x / multiplier, self.y / multiplier)
    def __truediv__(self, multiplier):
        if isinstance(multiplier, Vec2):
            return Vec2(self.x / multiplier.x, self.y / multiplier.y)
        return Vec2(self.x / multiplier, self.y / multiplier)

    def length(self):
        return np.sqrt(self.x ** 2 + self.y ** 2)
    
    def distance_to(self, other):
        return (self - other).length()

    def normalized(self):
        length = self.length()
        if length > 0:
            return Vec2(self.x / length, self.y / length)
        return Vec2()
    
    def __str__(self) -> str:
        return f"[{self.x}, {self.y}]"
    
    def copy(self):
        return Vec2(self.x, self.y)

    def get_normalized(self):
        return Vec2(self.x / abs(self.x), self.y / abs(self.y))

    def get_rotated(self, angle_degrees):
        theta = math.radians(angle_degrees)
        x_new = self.x * math.cos(theta) - self.y * math.sin(theta)
        y_new = self.x * math.sin(theta) + self.y * math.cos(theta)
        return Vec2(x_new, y_new)

    def get_rotation_deg(self):
        angle_rad = math.atan2(self.y, -self.x)
        angle_deg = math.degrees(angle_rad)
        # if angle_deg < 0:
        #     angle_deg += 360
        return angle_deg

    def __eq__(self, other):
        return isinstance(other, Vec2) and self.x == other.x and self.y == other.y

class Vec4:
    __slots__ = ('r', 'g', 'b', 'a', "xyz", "rgb", "rgba")
    r: float
    g: float
    b: float
    a: float
    def __init__(self, r=0.0, g=0.0, b=0.0, a=0.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        self.xyz = [r, g, b]
        self.rgb = [r, g, b]
        self.rgba = [r, g, b, a]

    def combine(self, other):
        x0, y0, x1, y1 = self.r, self.g, self.b, self.a
        x2, y2, x3, y3 = other.r, other.g, other.b, other.a
        w1 = x1 - x0
        h1 = y1 - y0
        w2 = x3 - x2
        h2 = y3 - y2

        return Vec4(
            self.r + other.r,   # new x0
            self.g + other.g,   # new y0
            self.r + other.r + w1 * w2,   # new x1
            self.g + other.g + h1 * h2,   # new y1
        )
    def transform(self, other):
        translate_original = Vec2(self.r, self.g)
        translate = Vec2(other.r, other.g)
        size_original = Vec2(self.b - self.r, self.a - self.g)
        size = Vec2(other.b, other.a)
        return Vec4(
            translate_original.x + translate.x,   # new x0
            translate_original.y + translate.y,   # new y0
            translate_original.x + translate.x + size_original.x * size.x,   # new x1
            translate_original.y + translate.y + size_original.y * size.y,   # new y1
        )
    # def transform(self, other):
    #     return Vec4(
    #         other.r + self.r * other.b,  # new x0
    #         other.g + self.g * other.a,  # new y0
    #         other.r + self.b * other.b,  # new x1
    #         other.g + self.a * other.a,  # new y1
    #     )

    def __str__(self) -> str:
        return f"{self.r}, {self.g}, {self.b}, {self.a}"


class Vec2i:
    __slots__ = ('x', 'y')
    x: int
    y: int
    def __init__(self, x=0, y=0):
        self.x = int(x)
        self.y = int(y)

    def __add__(self, other):
        if isinstance(other, Vec2i):
            return Vec2i(self.x + other.x, self.y + other.y)
        return Vec2i(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2i):
            return Vec2i(self.x - other.x, self.y - other.y)
        return Vec2i(self.x - other, self.y - other)
    def __mul__(self, multiplier):
        if isinstance(multiplier, Vec2i):
            return Vec2i(self.x * multiplier.x, self.y * multiplier.y)
        return Vec2i(self.x * multiplier, self.y * multiplier)

    def __truediv__(self, multiplier):
        if isinstance(multiplier, Vec2i):
            return Vec2i(self.x / multiplier.x, self.y / multiplier.y)
        return Vec2i(self.x / multiplier, self.y / multiplier)


    def length(self):
        return np.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        length = self.length()
        if length > 0:
            return Vec2i(self.x / length, self.y / length)
        return Vec2i()
    
    def __str__(self) -> str:
        return f"{self.x}, {self.y}"
    
    def from_vec2(vec):
        return Vec2i(int(vec.x), int(vec.y))


def line_intersects_line(A, B, C, D):
    """Returns the intersection point of (A-B) and (C-D), or None if no intersection."""
    x1, y1 = A.x, A.y
    x2, y2 = B.x, B.y
    x3, y3 = C.x, C.y
    x4, y4 = D.x, D.y

    # Compute denominator
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denominator == 0:
        return None  # Lines are parallel

    # Compute intersection point
    Px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    Py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator

    # Check if intersection is within both line segments
    if (min(x1, x2) <= Px <= max(x1, x2) and min(y1, y2) <= Py <= max(y1, y2) and
        min(x3, x4) <= Px <= max(x3, x4) and min(y3, y4) <= Py <= max(y3, y4)):
        return Vec2(Px, Py)  # Return the intersection point

    return None  # No valid intersection



def line_intersects_rect(start, end, rect_x, rect_y, rect_w, rect_h):
    """Checks if a line (start-end) intersects a rectangle and returns the penetration vector."""
    rect_edges = [
        (Vec2(rect_x, rect_y), Vec2(rect_x + rect_w, rect_y), Vec2(0, -1)),  # Top, normal (0, -1)
        (Vec2(rect_x, rect_y + rect_h), Vec2(rect_x + rect_w, rect_y + rect_h), Vec2(0, 1)),  # Bottom, normal (0, 1)
        (Vec2(rect_x, rect_y), Vec2(rect_x, rect_y + rect_h), Vec2(-1, 0)),  # Left, normal (-1, 0)
        (Vec2(rect_x + rect_w, rect_y), Vec2(rect_x + rect_w, rect_y + rect_h), Vec2(1, 0)),  # Right, normal (1, 0)
    ]

    penetration_vector = None
    intersection_point = None
    min_distance = float('inf')
    edge_normal = None
    # Check for intersection with each rectangle edge
    for edge_start, edge_end, normal in rect_edges:
        intersection = line_intersects_line(start, end, edge_start, edge_end)
        if intersection is not None:
            # Compute penetration depth

            distance = (intersection - start).length()

            # Keep the smallest penetration depth (closest intersection)
            if distance < min_distance:
                min_distance = distance
                penetration_vector = end - intersection
                intersection_point = intersection
                edge_normal = normal
    return penetration_vector, intersection_point, edge_normal  # Returns both penetration vector and intersection point


def parametric_blend(t):
    sqr = t * t
    return sqr / (2.0 * (sqr - t) + 1.0)


# def create_transformation_matrix(
#     position=Vec2(), size=Vec2(TILE_SIZE, TILE_SIZE), offset=Vec2(), scale=1,
#     rotation=0.0, skew_x=0.0, skew_y=0.0,
#     flip_x=False, flip_y=False
# ):
#     """
#     Create a transformation matrix for 2D rendering with optional flipping.
#
#     Args:
#         position: Vector2 with x,y position
#         size: Vector2 with width,height
#         offset: Vector2, current camera offset
#         scale: float, current camera scale
#         rotation: Rotation angle in degrees
#         skew_x: Horizontal skew factor
#         skew_y: Vertical skew factor
#         flip_x: Flip horizontally
#         flip_y: Flip vertically
#
#     Returns:
#         4x4 transformation matrix as numpy array
#     """
#     matrix = np.identity(4, dtype=np.float32)
#
#     # Flip (reflection)
#     if flip_x or flip_y:
#         flip_matrix = np.identity(4, dtype=np.float32)
#         if flip_x:
#             flip_matrix[0, 0] = -1.0
#             flip_matrix[3, 0] = 1.0
#         if flip_y:
#             flip_matrix[1, 1] = -1.0
#             flip_matrix[3, 1] = 1.0
#         matrix = np.matmul(matrix, flip_matrix)
#
#     # Skew (if any)
#     if skew_x != 0.0 or skew_y != 0.0:
#         skew_matrix = np.identity(4, dtype=np.float32)
#         skew_matrix[0, 1] = np.tan(np.radians(skew_x))
#         skew_matrix[1, 0] = np.tan(np.radians(skew_y))
#         matrix = np.matmul(matrix, skew_matrix)
#
#     # Scale
#     scale_matrix = np.identity(4, dtype=np.float32)
#     scale_matrix[0, 0] = size.x * scale
#     scale_matrix[1, 1] = size.y * scale
#     scale_matrix[2, 2] = scale
#     matrix = np.matmul(matrix, scale_matrix)
#
#     # Rotation (if any)
#     if rotation != 0.0:
#         rotation_matrix = np.identity(4, dtype=np.float32)
#         rad = np.radians(rotation)
#         cos_r = np.cos(rad)
#         sin_r = np.sin(rad)
#         rotation_matrix[0, 0] = cos_r
#         rotation_matrix[0, 1] = -sin_r
#         rotation_matrix[1, 0] = sin_r
#         rotation_matrix[1, 1] = cos_r
#         matrix = np.matmul(matrix, rotation_matrix)
#
#     # Translation
#     translation_matrix = np.identity(4, dtype=np.float32)
#     translation_matrix[3, 0] = position.x * scale + offset.x
#     translation_matrix[3, 1] = position.y * scale + offset.y
#     matrix = np.matmul(matrix, translation_matrix)
#
#     return matrix

class MatrixPool:
    def __init__(self):
        self.flip = np.identity(4, dtype=np.float32)
        self.origin = np.identity(4, dtype=np.float32)
        self.skew = np.identity(4, dtype=np.float32)
        self.scale = np.identity(4, dtype=np.float32)
        self.rotation = np.identity(4, dtype=np.float32)
        self.translation = np.identity(4, dtype=np.float32)
        self.result = np.identity(4, dtype=np.float32)

    def reset(self, mat):
        mat.fill(0.0)
        for i in range(4):
            mat[i, i] = 1.0

default_transform_matrix_pool = MatrixPool()

def create_transformation_matrix(
    position=Vec2(), size=Vec2(TILE_SIZE, TILE_SIZE), offset=Vec2(), scale=1,
    rotation=0.0, skew_x=0.0, skew_y=0.0,
    flip_x=False, flip_y=False,
    origin=Vec2(0, 0),
    matrix=None,
    pool=default_transform_matrix_pool
):
    """
    Create a transformation matrix for 2D rendering with optional flipping, skewing, and origin pivot.

    Args:
        position: World position
        size: Local size
        offset: Camera offset
        scale: Camera scale
        rotation: Rotation angle in degrees
        skew_x: Horizontal skew angle
        skew_y: Vertical skew angle
        flip_x: Mirror on X
        flip_y: Mirror on Y
        origin: Vec2 in [0, 1] space relative to size — pivot point (e.g., (0.5, 0.5) is center)
        pool: MatrixPool object where temporary matrices used for each transformation step stored
    Returns:
        4x4 transformation matrix as numpy array
    """
    if matrix is None:
        matrix = pool.result


    # Step 2: Flip
    if flip_x or flip_y:
        pool.reset(pool.flip)
        if flip_x:
            pool.flip[0, 0] = -1.0
            pool.flip[3, 0] = 1.0

        if flip_y:
            pool.flip[1, 1] = -1.0
            pool.flip[3, 1] = 1.0
        matrix = np.matmul(matrix, pool.flip)

    # Step 1: Apply origin offset (move origin to 0,0)
    pool.reset(pool.origin)
    pool.origin[3, 0] = -origin.x
    pool.origin[3, 1] = -origin.y
    matrix = np.matmul(matrix, pool.origin)

    # Step 3: Skew
    if skew_x != 0.0 or skew_y != 0.0:
        pool.reset(pool.skew)
        pool.skew[0, 1] = np.tan(np.radians(skew_x))
        pool.skew[1, 0] = np.tan(np.radians(skew_y))
        matrix = np.matmul(matrix, pool.skew)

    # Step 4: Scale
    pool.reset(pool.scale)
    pool.scale[0, 0] = size.x * scale
    pool.scale[1, 1] = size.y * scale
    pool.scale[2, 2] = scale
    matrix = np.matmul(matrix, pool.scale)

    # Step 5: Rotation
    if rotation != 0.0:
        pool.reset(pool.rotation)
        rad = np.radians(rotation)
        cos_r = np.cos(rad)
        sin_r = np.sin(rad)
        pool.rotation[0, 0] = cos_r
        pool.rotation[0, 1] = -sin_r
        pool.rotation[1, 0] = sin_r
        pool.rotation[1, 1] = cos_r
        matrix = np.matmul(matrix, pool.rotation)

    # Step 6: Final translation to world space
    pool.reset(pool.translation)
    pool.translation[3, 0] = (position.x + origin.x * size.x) * scale + offset.x
    pool.translation[3, 1] = (position.y + origin.y * size.y) * scale + offset.y
    matrix = np.matmul(matrix, pool.translation)


    return matrix

def is_inside_rotated_square(mouse, box_center, box_size):
    dx = mouse.x - box_center.x
    dy = mouse.y - box_center.y
    # Rotate mouse point -45 degrees around center (undo the texture rotation)
    rx = (dx + dy) / math.sqrt(2)
    ry = (dy - dx) / math.sqrt(2)
    # Now check if the rotated point is inside the unrotated square
    half_side = box_size / 2
    return abs(rx) <= half_side and abs(ry) <= half_side


matrices = {
    "uv": Vec4(0,0,
               1,1),
    "uv_flipped_v": Vec4(1,0,
                         0,1)
}


class DirectionX(Enum):
    RIGHT = 1
    LEFT = -1

class DirectionY(Enum):
    DOWN = 1
    UP = -1

def coord_round(value):
    return math.floor(value) if value >= 0 else math.floor(value) - 1


def pos_world_to_map(pos):
    pos = pos / TILE_SIZE
    return Vec2(coord_round(pos.x), coord_round(pos.y))


def clamp(x, min, max):
    if x < min: x = min
    elif x > max: x = max
    return x


def norm(y):
    if y == 0: return 0
    else: return y / y
