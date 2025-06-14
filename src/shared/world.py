from collections import defaultdict
from operator import contains

from src.server.terrain import *
from src.shared.physics.objects import *

class World:
    def __init__(self):
        self.map_manager = None
        self.environment = Environment(None)
        self.player = None

    def create_map(self, init_range, client):
        self.map_manager = MapManager(self)
        self.environment.map_manager = self.map_manager
        d = (1 - client.loaded) / (init_range*init_range * 4)
        for cx in range(-init_range, init_range):
            for cy in range(-init_range, init_range):
                self.map_manager.initialize_chunk(cx, cy)
                client.loaded += d
        # for cx in range(1 - init_range, init_range - 1):
        #     for cy in range(1 - init_range, init_range - 1):
        #         self.map_manager.update_chunk(cx, cy)
        #         client.loaded += d


# -------------------------------------------------------------------------------------------
# MAP
# -------------------------------------------------------------------------------------------


class TileTypeGroups:
    TRANSPARENT = [
        "grass",
        "grass_high",
        "grass_water",
        "mushroom",
        "tree"
    ]


class MapManager:
    def __init__(self, world, chunk_size=16, seed=1):
        self.is_plants_planted = {}
        self.seed = seed
        random.seed(self.seed)
        self.chunk_size = chunk_size
        self.map = {}
        self.bg_map = {}
        self.fg_map = {}
        self.render_meshes = [{},{},{}]
        self.physical_meshes = {}
        self.dirty_chunks = set()
        self.world = world
        # for cx in range(-4, 4):
        #     for cy in range(-4, 4):
        #         self.initialize_chunk(cx, cy)

    def update(self, cx, cy, sim_range, max_chunks_number=4):
        updated = 0

        for x in range(cx - sim_range, cx + sim_range):
            for y in range(cy - sim_range, cy + sim_range):
                if (x, y) in self.dirty_chunks:
                    self.update_chunk(x, y)
                    self.dirty_chunks.remove((x, y))
                    updated += 1
                    if updated >= max_chunks_number:
                        print("Update stopped.", self.dirty_chunks)
                        return
        if updated > 0:
            print("update finished", self.dirty_chunks)

    def initialize_chunk(self, cx, cy):
        # Initialize map with chunks of tiles
        print(f"initializing chunk ({cx}, {cy})")
        global_x, global_y = cx * self.chunk_size, cy * self.chunk_size

        platforms = generate_platforms(self.seed, offset=Vec2(global_x, global_y),
                                       size=Vec2(self.chunk_size, self.chunk_size))

        self.bg_map[(cx, cy)] = [[None for _ in range(self.chunk_size)] for _ in range(self.chunk_size)]
        self.map[(cx, cy)] = [[None for _ in range(self.chunk_size)] for _ in range(self.chunk_size)]
        self.fg_map[(cx, cy)] = [[None for _ in range(self.chunk_size)] for _ in range(self.chunk_size)]

        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                t = tile_type_codes[platforms[y, x]]
                if t != "air":
                    if t == "dirt" or t == "grass_dirt" or t == "stone":
                        self.bg_map[(cx, cy)][x][y] = Tile(global_x + x, global_y + y, "cave_"+t)
                        self.map[(cx, cy)][x][y] = Tile(global_x + x, global_y + y, t)
                    elif t == "cave_dirt" or t == "cave_grass_dirt" or t == "cave_stone":
                        self.bg_map[(cx, cy)][x][y] = Tile(global_x + x, global_y + y, t)
                    # elif t == "grass" or t == "grass_high" or t == "grass_water":
                    #     self.map[(cx, cy)][x][y] = Tile(global_x + x, global_y + y, t, require_support=True)
                    else: self.map[(cx, cy)][x][y] = Tile(global_x + x, global_y + y, t)

        self.mark_chunk_dirty(cx, cy)

    def place_plants(self, cx, cy):
        global_x, global_y = cx * self.chunk_size, cy * self.chunk_size
        if (cx, cy) in self.is_plants_planted and self.is_plants_planted[(cx, cy)] == True:
            print("plants was already placed")

            return

        for x in range(self.chunk_size):
            for y in range(self.chunk_size):
                # continue

                grass_tile = self.get_tile(global_x + x, global_y + y)
                if grass_tile is not None and grass_tile.tile_type == "grass_dirt":
                    # grass_tile.update_state(
                    #     neighbours=self.get_neighbors(global_x + x, global_y + y + 1),
                    #     d_neighbours=self.get_diagonal_neighbors(global_x + x, global_y + y + 1)
                    # )
                    tile_above = self.get_tile(global_x + x, global_y + y - 1)

                    if tile_above is None:
                        can_place_tree = True
                        decoration_tile_type = "grass_high"
                        print("placing plant on ", grass_tile.tile_pos)

                        for yy in range(-1, -20, -1):
                            tile_higher = self.get_tile(global_x + x, global_y + y + yy)
                            if tile_higher is not None and tile_higher.is_physical:
                                can_place_tree = False
                                print("tree can't be placed")

                                break
                        r = random.random()
                        if r > 0.7: decoration_tile_type = "grass_water"
                        if r > 0.8 and can_place_tree: decoration_tile_type = "tree"
                        if r > 0.9 and can_place_tree: decoration_tile_type = "mushroom"

                        if y == self.chunk_size:
                            self.get_chunk(cx, cy - 1)
                        match decoration_tile_type:
                            case "tree" | "mushroom":
                                r = random.random()
                                if r > 0.5:
                                    self.bg_map[(cx, cy)][x][y - 1] = Tile(global_x + x, global_y + y - 1,
                                                                           decoration_tile_type, False, require_support=True)
                                else:
                                    self.fg_map[(cx, cy)][x][y - 1] = Tile(global_x + x, global_y + y - 1,
                                                                           decoration_tile_type, False, require_support=True)
                            case "grass" | "grass_high" | "grass_water":
                                self.bg_map[(cx, cy)][x][y - 1] = Tile(global_x + x, global_y + y - 1,
                                                                       decoration_tile_type, False, require_support=True)
                                self.fg_map[(cx, cy)][x][y - 1] = Tile(global_x + x, global_y + y - 1,
                                                                       "grass", False, require_support=True)


        self.is_plants_planted[(cx,cy)] = True
        
        
        
    def mark_chunk_dirty(self, cx, cy):
        self.dirty_chunks.add((cx, cy))

    def get_local_coords(self, global_x, global_y):
        """Correct chunk calculation for negative coordinates"""

        cx = math.floor(global_x / self.chunk_size)
        cy = math.floor(global_y / self.chunk_size)
        lx = global_x - cx * self.chunk_size
        ly = global_y - cy * self.chunk_size
        # lx = global_x % self.chunk_size
        # if lx < 0:  # Adjust when global_x is negative
        #     cx -= 1
        #     lx += self.chunk_size

        # ly = global_y % self.chunk_size
        # if ly < 0:  # Adjust when global_y is negative
        #     cy -= 1
        #     ly += self.chunk_size

        return cx, cy, lx, ly

    def get_tile(self, global_x, global_y, layer=0) -> Tile:
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        return self.get_chunk(cx, cy, layer)[lx][ly]

    def get_first_non_none_tile(self, start, end):
        """Find the first non-None tile intersected by a line using Bresenham's Line Algorithm."""
        x0, y0 = int(start.x), int(start.y)
        x1, y1 = int(end.x), int(end.y)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0

        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        if dx > dy:
            err = dx // 2
            while x != x1:
                tile = self.get_tile(x, y)
                if tile is not None:
                    return tile
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy // 2
            while y != y1:
                tile = self.get_tile(x, y)
                if tile is not None:
                    return tile
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        # Check the end point
        tile = self.get_tile(x1, y1)
        if tile is not None:
            return tile

        return None

    def trace_ray(self, start, direction, max_steps=10):
        """
        Trace a ray through a grid and return first tile and side hit.

        direction should be normalized (unit vector).
        :returns (tile, side, (tile_x, tile_y))
        """
        tile, side_hit = None, None

        x, y = start.x, start.y
        dx, dy = direction.x, direction.y

        # Current tile
        tile_x = int(math.floor(x))
        tile_y = int(math.floor(y))

        # Direction steps
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        # Distance to next tile boundary
        t_max_x = ((tile_x + (1 if dx > 0 else 0)) - x) / dx if dx != 0 else float('inf')
        t_max_y = ((tile_y + (1 if dy > 0 else 0)) - y) / dy if dy != 0 else float('inf')

        # How far we must move along the ray to cross a tile
        t_delta_x = abs(1 / dx) if dx != 0 else float('inf')
        t_delta_y = abs(1 / dy) if dy != 0 else float('inf')

        for _ in range(max_steps):
            # Check current tile
            tile = self.get_tile(tile_x, tile_y)
            if tile is not None:
                return tile, side_hit, (tile_x, tile_y)

            if t_max_x < t_max_y:
                t_max_x += t_delta_x
                tile_x += step_x
                side_hit = 'left' if step_x == -1 else 'right'
            else:
                t_max_y += t_delta_y
                tile_y += step_y
                side_hit = 'top' if step_y == -1 else 'bottom'

        return None, None, None

    def get_chunk(self, cx, cy, layer=0):
        chunk_key = (cx, cy)
        if chunk_key not in self.map: self.initialize_chunk(cx, cy)
        if layer == -1: return self.bg_map[chunk_key]
        if layer == 1: return self.fg_map[chunk_key]
        return self.map[chunk_key]

    def update_tile(self, global_x, global_y, update_neighbours=False):
        was_deleted = False
        for l in range(-1, 2):
            tile = self.get_tile(global_x, global_y, l)
            if tile is not None:
                neighbours = self.get_neighbors(global_x, global_y)
                d_neighbours = self.get_diagonal_neighbors(global_x, global_y)
                tile.update_state(
                    neighbours=neighbours,
                    d_neighbours=d_neighbours
                )
                if tile.require_support and not neighbours[2]:
                    print("deleting")
                    self.delete_tile(Vec2(global_x, global_y), l)
                    was_deleted = True


        if update_neighbours:
            self.update_tile(global_x - 1, global_y, was_deleted)
            self.update_tile(global_x + 1, global_y, was_deleted)
            self.update_tile(global_x, global_y - 1, was_deleted)
            self.update_tile(global_x, global_y + 1, was_deleted)
            # diagonal
            self.update_tile(global_x - 1, global_y - 1, was_deleted)
            self.update_tile(global_x + 1, global_y + 1, was_deleted)
            self.update_tile(global_x + 1, global_y - 1, was_deleted)
            self.update_tile(global_x - 1, global_y + 1, was_deleted)

    def delete_tile(self, pos, layer=0):
        global_x, global_y = pos.x, pos.y
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        chunk_key = (cx, cy)
        if chunk_key in self.map:
            chunk = self.get_chunk(cx, cy, layer)
            tile = chunk[lx][ly]
            if tile is not None:

                self.world.environment.add_body(ItemStackEntity((pos.x+0.5)*TILE_SIZE, (pos.y+0.5)*TILE_SIZE,
                                                                  ItemStack(Item(tile.tile_type), 1)))
                for pn in range(int((random.random()*5+5))):
                    self.world.environment.add_body(
                        TileBreakParticle(pos, tile.tile_type, max_age=random.random()*0.3+0.2,
                                 direction=Vec2(random.random(), random.random())*10))


                chunk[lx][ly] = None
                self.update_tile(global_x, global_y, True)

        self.mark_chunk_dirty(cx, cy)

    def set_tile(self, global_x, global_y, tile_type):
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        chunk_key = (cx, cy)
        if chunk_key in self.map:
            tile = self.map[chunk_key][lx][ly]
            if tile is None:
                self.map[chunk_key][lx][ly] = Tile(global_x, global_y, tile_type)
                self.update_tile(global_x, global_y, True)

        self.mark_chunk_dirty(cx, cy)

    def get_neighbors(self, global_x, global_y):
        # Determine neighbor presence: [top, left, bottom, right]
        return (
            bool(self.get_tile(global_x, global_y - 1) is not None),
            bool(self.get_tile(global_x - 1, global_y) is not None),
            bool(self.get_tile(global_x, global_y + 1) is not None),
            bool(self.get_tile(global_x + 1, global_y) is not None),
        )

    def get_diagonal_neighbors(self, global_x, global_y):
        # Determine neighbor presence: [tl, bl, br, tr]
        return (
            bool(self.get_tile(global_x - 1, global_y - 1) is not None),
            bool(self.get_tile(global_x - 1, global_y + 1) is not None),
            bool(self.get_tile(global_x + 1, global_y + 1) is not None),
            bool(self.get_tile(global_x + 1, global_y - 1) is not None),
        )

    # def update_chunk(self, cx, cy):
    #     """Update all tiles in the chunk"""
    #     print(f"Updating chunk: ({cx}, {cy})")
    #     chunk = self.get_chunk(cx, cy)
    #
    #     merged_bodies = []
    #     visited = set()
    #
    #     for lx in range(0,self.chunk_size):
    #         for ly in range(0,self.chunk_size):
    #             global_x, global_y = cx * self.chunk_size + lx, cy * self.chunk_size + ly
    #             # self.update_tile(cx * self.chunk_size + lx, cy * self.chunk_size + ly)
    #             tile = chunk[lx][ly]
    #             if tile is not None:
    #                 tile.update_state(
    #                     neighbours=self.get_neighbors(global_x, global_y),
    #                     d_neighbours=self.get_diagonal_neighbors(global_x, global_y)
    #                 )
    #
    #                 if (lx, ly) in visited: continue
    #
    #                 # Find the width of the rectangle
    #                 width = 0
    #                 while lx + width < self.chunk_size and (lx + width, ly) not in visited and chunk[lx + width][ly] is not None:
    #                     width += 1
    #
    #                 # Find the height of the rectangle
    #                 height = 0
    #                 while ly + height < self.chunk_size and all(chunk[lx + w][ly + height] is not None for w in range(width)):
    #                     height += 1
    #
    #                 # Mark these tiles as visited
    #                 for dy in range(height):
    #                     for dx in range(width):
    #                         visited.add((lx + dx, ly + dy))
    #
    #                 # Store the merged rectangle
    #                 merged_bodies.append(
    #                     RigidBody(tile.position.x, tile.position.y, width * TILE_SIZE, height * TILE_SIZE, None, 0,
    #                               False, True, True)
    #                 )
    #
    #     self.collision_map[(cx, cy)] = merged_bodies

    def update_chunk(self, cx, cy):
        """Update all tiles in the chunk and create merged render meshes"""
        print(f"Updating chunk: ({cx}, {cy})")

        self.place_plants(cx, cy)

        will_not_be_visible = set()

        for layer in range(1, -2, -1):
            chunk = self.get_chunk(cx, cy, layer)
            visited = set()

            meshes = defaultdict(list)

            for lx in range(0, self.chunk_size):
                for ly in range(0, self.chunk_size):
                    if (lx, ly) in visited:
                        continue

                    tile = chunk[lx][ly]
                    if tile is None:
                        continue


                    tile_visibility = (lx, ly) in will_not_be_visible

                    if tile_visibility and layer != 0:
                        continue

                    tile_type = tile.tile_type
                    # global_x, global_y = cx * self.chunk_size + lx, cy * self.chunk_size + ly

                    # --- Find max width ---
                    width = 0
                    while lx + width < self.chunk_size:
                        t = chunk[lx + width][ly]
                        if ((lx + width, ly) in visited
                                or t is None
                                or t.tile_type != tile_type
                                or (tile_visibility == (lx + width, ly) in will_not_be_visible)):
                            break
                        width += 1

                    # --- Find max height ---
                    height = 0
                    while ly + height < self.chunk_size:
                        valid_row = True
                        for dx in range(width):
                            t = chunk[lx + dx][ly + height]
                            if ((lx + dx, ly + height) in visited
                                    or t is None
                                    or t.tile_type != tile_type)\
                                    or (tile_visibility == (lx + width, ly) in will_not_be_visible):
                                valid_row = False
                                break
                        if not valid_row:
                            break
                        height += 1

                    # --- Mark all as visited ---
                    for dy in range(height):
                        for dx in range(width):
                            visited.add((lx + dx, ly + dy))
                            if not tile.tile_type in TileTypeGroups.TRANSPARENT:
                                will_not_be_visible.add((lx, ly))

                    # --- Add to render mesh ---
                    rect_x = tile.position.x
                    rect_y = tile.position.y
                    rect_w = width * TILE_SIZE
                    rect_h = height * TILE_SIZE

                    rb = RigidBody(rect_x, rect_y, rect_w, rect_h, None, 0, False, True, True)

                    if layer == 0:
                        if not (cx, cy) in self.physical_meshes:
                            self.physical_meshes[(cx, cy)] = []
                        self.physical_meshes[(cx, cy)].append(rb)

                    if not tile_visibility:
                        if not tile_type in meshes:
                            meshes[tile_type] = []
                        meshes[tile_type].append(rb)

            self.render_meshes[layer][(cx, cy)] = meshes



# -------------------------------------------------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------------------------------------------------

class Environment():
    def __init__(self, map_manager, day_period=1200):
        self.bodies = []
        self.light_sources = []
        self.map_manager = map_manager
        self.time_running = 0
        self.daytime = 0
        self.day_period = day_period

    def add_body(self, body: Entity):
        self.bodies.append(body)
        body.on_spawn()
        body.environment = self

    def apply_gravity(self):
        for body in self.bodies:
            body.apply_gravity()

    def solve_collisions(self, dt):
        for i in range(len(self.bodies)):
            body = self.bodies[i]

            for j in range(i + 1, len(self.bodies)):
                self.resolve_collision(body, self.bodies[j], dt)


            if isinstance(body, LivingEntity):
                body.is_grounded = False


            start = body.position.copy()
            destination = body.position + body.size
            diff = body.get_next_movement_diff(dt)

            if diff.x > 0:
                start.x -= diff.x
            else:
                destination.x -= diff.x
            if diff.y > 0:
                start.y -= diff.y
            else:
                destination.y -= diff.y

            start_i = Vec2i.from_vec2(start / TILE_SIZE) - 3
            destination_i = Vec2i.from_vec2(destination / TILE_SIZE) + 3

            # destination_i = Vec2i(math.floor(destination.x / TILE_SIZE), math.floor(destination.y / TILE_SIZE)) + Vec2i(3, 3)
            scx, scy, _, _ = self.map_manager.get_local_coords(start_i.x, start_i.y)
            ecx, ecy, _, _ = self.map_manager.get_local_coords(destination_i.x, destination_i.y)
            # print(f"start: {start_i} destination: {destination_i}")
            ecx += 1
            ecy += 1

            # uv = matrices["normal"]
            # glColor3f(1.0, 0.0, 0.0)
            # draw_quad_without_texture(uv,
            #     start * camera.get_scale() + camera.offset,
            #     destination * camera.get_scale() + camera.offset
            # )
            # glColor3f(1.0, 1.0, 1.0)

            # for x in range(start_i.x, destination_i.x):
            #     for y in range(start_i.y, destination_i.y):
            #         tile = self.map_manager.get_tile(x,y)
            #         if tile is not None:
            #             self.resolve_collision(self.bodies[i], tile, dt)


            # Optimized

            for x in range(scx, ecx):
                for y in range(scy, ecy):
                    # if not (x, y) in self.map_manager.physical_meshes:
                    #     self.map_manager.update_chunk(x, y)
                    if (x, y) in self.map_manager.physical_meshes:
                        for collision_body in self.map_manager.physical_meshes[(x, y)]:
                            self.resolve_collision(body, collision_body, dt)

    def update_positions(self, dt):
        for body in self.bodies:
            body.update_position(dt)

    def update(self, dt, cx, cy, sim_range, camera, max_chunks_number=1):
        self.map_manager.update(cx, cy, sim_range, max_chunks_number)
        sub_steps = max(int(dt / 10), 1)
        sub_dt = float(dt / sub_steps)
        for _ in range(sub_steps):

            self.apply_gravity()
            self.update_positions(sub_dt)
            self.solve_collisions(sub_dt)

        for body in self.bodies:
            if isinstance(body, Entity):
                body.update(sub_dt)

        def is_valid(body):
            if isinstance(body, Entity):
                return body.is_alive
            return True

        self.bodies = [body for body in self.bodies if is_valid(body)]

        self.time_running += dt

    # -----------------------------
    # Функція для перевірки колізій
    # -----------------------------

    def check_collision(self, body1, body2, skip_inside_check=True):

        collision = (body1.position.x < body2.position.x + body2.size.x and
                     body1.position.x + body1.size.x > body2.position.x and
                     body1.position.y < body2.position.y + body2.size.y and
                     body1.position.y + body1.size.y > body2.position.y)
        # return collision, False, False

        if not (body1.is_physical and body2.is_physical):
            collision = False

        if (not collision) or skip_inside_check:
            return collision, False, False  # No need to check is_inside

        is_body1_inside = (body1.position.x > body2.position.x and
                           body1.position.x + body1.size.x < body2.position.x + body2.size.x and
                           body1.position.y > body2.position.y and
                           body1.position.y + body1.size.y < body2.position.y + body2.size.y)

        is_body2_inside = (body2.position.x > body1.position.x and
                           body2.position.x + body2.size.x < body1.position.x + body1.size.x and
                           body2.position.y > body1.position.y and
                           body2.position.y + body2.size.y < body1.position.y + body1.size.y)

        return collision, is_body1_inside, is_body2_inside

    # def check_collision(body1, body2):
    #     collision = (body1.position.x < body2.position.x + body2.size.x and
    #                  body1.position.x + body1.size.x > body2.position.x and
    #                  body1.position.y < body2.position.y + body2.size.y and
    #                  body1.position.y + body1.size.y > body2.position.y)
    #     if not body1.is_physical and body2.is_physical: return False
    #     return collision

    # return body1.rect.colliderect(body2.rect)

    # x1, y1, w1, h1 = body1.get_hitbox()
    # x2, y2, w2, h2 = body2.get_hitbox()
    # print(x1, y1, w1, h1)
    # print(x2, y2, w2, h2)
    # return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

    # -----------------------------
    # Функція для обробки колізій
    # -----------------------------
    def resolve_collision(self, body1, body2, dt):
        collision, is_body1_inside, is_body2_inside = self.check_collision(body1, body2, False)
        if collision or is_body1_inside or is_body2_inside:

            if body1.interact(body2, is_body1_inside, is_body2_inside) or \
                    body2.interact(body1, is_body2_inside, is_body1_inside): return

            if body1.is_immovable and body2.is_immovable: return

            # print("Collision detected!")

            # Розрахунок глибини проникнення по осях
            ox1, oy1 = body1.position_old.x, body1.position_old.y
            ox2, oy2 = body2.position_old.x, body2.position_old.y
            x1, y1 = body1.position.x, body1.position.y
            x2, y2 = body2.position.x, body2.position.y
            w1, h1 = body1.size.x, body1.size.y
            w2, h2 = body2.size.x, body2.size.y

            # # Розрахунок швидкості удару
            # hit_speed = ((body1.get_velocity().x - body2.get_velocity().x)**2 + (body1.get_velocity().y - body2.get_velocity().y)**2)**0.5
            # if hit_speed > 10:
            #     if isinstance(body1, LivingEntity): body1.damage(hit_speed/2)
            #     if isinstance(body2, LivingEntity): body2.damage(hit_speed/2)
            # print("Hit speed:", hit_speed)

            # Визначаємо напрямок нормалі зіткнення


            # # based on overlap
            penetration = 0
            overlap_x = min(x1 + w1 - x2, x2 + w2 - x1)
            overlap_y = min(y1 + h1 - y2, y2 + h2 - y1)

            if abs(overlap_x) < abs(overlap_y):
                if x1 < x2:
                    normal = [1, 0]  # Зіткнення зліва (вказується бік ПЕРШОГО тіла)
                else:
                    normal = [-1, 0]  # Зіткнення справа (вказується бік ПЕРШОГО тіла)
                penetration = overlap_x
            else:
                if y1 < y2:
                    normal = [0, 1]  # Зіткнення зверху (вказується бік ПЕРШОГО тіла)
                    # print("xdij bdfi jfd")
                    if isinstance(body2, LivingEntity) or issubclass(type(body2), LivingEntity):
                        body2.is_grounded = True
                        body2.is_jumping = False
                    if isinstance(body1, LivingEntity) or issubclass(type(body2), LivingEntity):
                        body1.is_grounded = True
                        body1.is_jumping = False
                else:
                    normal = [0, -1]  # Зіткнення знизу (вказується бік ПЕРШОГО тіла)
                penetration = overlap_y


            if body1.is_immovable and not body2.is_immovable: # Якщо body1 нерухомий та body2 не застряг
                body2.position.x += normal[0] * penetration
                body2.position_old.x = body2.position.x
                body2.position.y += normal[1] * penetration
                # if normal[0] != 0: body2.position_old.x = body2.position.x
                # if normal[1] != 0: body2.position_old.y = body2.position.y

            elif body2.is_immovable and not body1.is_immovable: # Якщо body2 нерухомий та body1 не застряг
                body1.position.x -= normal[0] * penetration
                body1.position_old.x = body1.position.x
                body1.position.y -= normal[1] * penetration
                # if normal[0] != 0: body1.position_old.x = body1.position.x
                # if normal[1] != 0: body1.position_old.y = body1.position.y
                # body1.acceleration *= vec2(*normal)
            else:
                # Виштовхуємо тіла, щоб прибрати проникнення
                correction = penetration / (1 / body1.mass + 1 / body2.mass)
                body1.position.x -= normal[0] * correction / body1.mass
                body1.position.y -= normal[1] * correction / body1.mass
                body2.position.x += normal[0] * correction / body2.mass
                body2.position.y += normal[1] * correction / body2.mass


            # based on vectors

            penetration = Vec2(0, 0)
            edge_normal = Vec2(0, 0)
            lines = [
                (body1.position_old, body1.position),
                (body1.position_old + Vec2(w1, 0), body1.position + Vec2(w1, 0)),
                (body1.position_old + Vec2(0, h1), body1.position + Vec2(0, h1)),
                (body1.position_old + Vec2(w1, h1), body1.position + Vec2(w1, h1)),
            ]
            for (line_start, line_end) in lines:
                current_penetration, _, normal = line_intersects_rect(
                    line_start,
                    line_end,
                    body2.position.x,
                    body2.position.y,
                    body2.size.x,
                    body2.size.y
                )
                if current_penetration is not None:
                    if current_penetration.length() > penetration.length():
                        penetration = current_penetration
                        edge_normal = normal
            # print(penetration)

            if edge_normal == Vec2(0, -1):
                # print("xdij bdfi jfd")
                if isinstance(body2, LivingEntity) or issubclass(type(body2), LivingEntity):
                    body2.is_grounded = True
                    body2.is_jumping = False
                if isinstance(body1, LivingEntity) or issubclass(type(body2), LivingEntity):
                    body1.is_grounded = True
                    body1.is_jumping = False

            # if isinstance(body2, Player): body2.is_jumping = False
            # if isinstance(body1, Player): body1.is_jumping = False

            if body1.is_immovable and not body2.is_immovable:  # Якщо body1 нерухомий та body2 не застряг
                body2.position += penetration
            elif body2.is_immovable and not body1.is_immovable:  # Якщо body2 нерухомий та body1 не застряг
                body1.position -= penetration
            else:
                pass
                # Виштовхуємо тіла, щоб прибрати проникнення
                correction = penetration / (1 / body1.mass + 1 / body2.mass)
                body1.position -= correction / body1.mass
                body2.position += correction / body2.mass

