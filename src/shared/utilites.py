import math

import numpy as np

from src.shared.globals import TILE_SIZE


class Vec2:
    x: float
    y: float
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

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
        angle_rad = math.atan2(self.y, self.x)  # Returns angle in radians
        angle_deg = math.degrees(angle_rad)  # Convert to degrees
        if angle_deg < 0:
            angle_deg += 360  # Normalize to [0, 360)
        return angle_deg


class Vec2i:
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

def create_transformation_matrix(
    position=Vec2(), size=Vec2(TILE_SIZE, TILE_SIZE), offset=Vec2(), scale=1,
    rotation=0.0, skew_x=0.0, skew_y=0.0,
    flip_x=False, flip_y=False,
    origin=Vec2(0, 0)
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

    Returns:
        4x4 transformation matrix as numpy array
    """
    matrix = np.identity(4, dtype=np.float32)

    # Step 1: Apply origin offset (move origin to 0,0)
    origin_offset_matrix = np.identity(4, dtype=np.float32)
    origin_offset_matrix[3, 0] = -origin.x
    origin_offset_matrix[3, 1] = -origin.y
    matrix = np.matmul(matrix, origin_offset_matrix)

    # Step 2: Flip
    if flip_x or flip_y:
        flip_matrix = np.identity(4, dtype=np.float32)
        if flip_x:
            flip_matrix[0, 0] = -1.0
        if flip_y:
            flip_matrix[1, 1] = -1.0
        matrix = np.matmul(matrix, flip_matrix)

    # Step 3: Skew
    if skew_x != 0.0 or skew_y != 0.0:
        skew_matrix = np.identity(4, dtype=np.float32)
        skew_matrix[0, 1] = np.tan(np.radians(skew_x))
        skew_matrix[1, 0] = np.tan(np.radians(skew_y))
        matrix = np.matmul(matrix, skew_matrix)

    # Step 4: Scale
    scale_matrix = np.identity(4, dtype=np.float32)
    scale_matrix[0, 0] = size.x * scale
    scale_matrix[1, 1] = size.y * scale
    scale_matrix[2, 2] = scale
    matrix = np.matmul(matrix, scale_matrix)

    # Step 5: Rotation
    if rotation != 0.0:
        rotation_matrix = np.identity(4, dtype=np.float32)
        rad = np.radians(rotation)
        cos_r = np.cos(rad)
        sin_r = np.sin(rad)
        rotation_matrix[0, 0] = cos_r
        rotation_matrix[0, 1] = -sin_r
        rotation_matrix[1, 0] = sin_r
        rotation_matrix[1, 1] = cos_r
        matrix = np.matmul(matrix, rotation_matrix)

    # Step 6: Final translation to world space
    translation_matrix = np.identity(4, dtype=np.float32)
    translation_matrix[3, 0] = (position.x + origin.x * size.x) * scale + offset.x
    translation_matrix[3, 1] = (position.y + origin.y * size.y) * scale + offset.y
    matrix = np.matmul(matrix, translation_matrix)


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
    "normal": [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 0, 0, 1]
    ]
}
