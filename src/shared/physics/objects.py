import math
import random

import pygame
from enum import Enum

from src.server.terrain import *
from src.shared.utilites import *
from src.shared.globals import *




# -----------------------------
# Клас фізичного тіла
# -----------------------------


class RigidBody(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, texture, mass, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__()
        self.position = Vec2(x, y)
        self.position_old = Vec2(x, y)
        self.size = Vec2(width, height)
        self.acceleration = Vec2(0, 0)
        self.mass = mass
        self.gravity_enabled = gravity_enabled
        self.is_immovable = is_immovable
        self.is_physical = is_physical
        self.texture = texture
        self.rect = pygame.Rect(x, y, width, height)

    def apply_gravity(self, gravity=GRAVITY*TILE_SIZE):
        if self.gravity_enabled: 
            self.accelerate(Vec2(0, gravity))

    def accelerate(self, acc):
        self.acceleration += acc
        
    def get_velocity(self):
        return self.position - self.position_old

    def update_position(self, dt):
        if not self.is_immovable:
            velocity = self.get_velocity()
            self.position_old = self.position.copy()
            diff = velocity + (self.acceleration * dt * dt)
            # diff.x = diff.x % 10*TILE_SIZE 
            # diff.y = diff.y % 10*TILE_SIZE 
            if diff.x > 5*TILE_SIZE: diff.x = 5*TILE_SIZE
            if diff.y > 5*TILE_SIZE: diff.y = 5*TILE_SIZE
            if diff.x < -5*TILE_SIZE: diff.x = -5*TILE_SIZE
            if diff.y < -5*TILE_SIZE: diff.y = -5*TILE_SIZE
            
            self.position += diff
            self.acceleration = Vec2(0, 0)
            # self.update_rect()

    # def update_rect(self):
    #     self.rect.x = self.position.x
    #     self.rect.y = self.position.y
    #     self.rect.height = self.size.y
    #     self.rect.width = self.size.x
    
    # def get_current_velocity(self):
    #     return self.position - self.position_old

    # def get_display_rect(self, camera):
    #     pos = self.position * camera.get_scale() + camera.offset
    #     size = pos + self.size * camera.get_scale()
    #     return pygame.Rect(pos.x, pos.y, pos.x + self.width * camera.get_scale(), pos.y + self.height * camera.get_scale())
    
    # def get_display_bounds(self, camera):
    #     pos = self.position * camera.get_scale() + camera.offset
    #     return pos, pos + self.size * camera.get_scale()
    #
    # def get_display_center(self, camera):
    #     pos = self.position * camera.get_scale() + camera.offset
    #     return pos + self.size * camera.get_scale() * 0.5
    
    def get_uv(self):
        return matrices["normal"]

    def interact(self, other) -> bool:
        """
        :param other: other body this body interacting with
        :return: should skip physics for this interaction
        """
        return False

class Entity(RigidBody):
    def __init__(self, x, y, width, height, texture, mass, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, gravity_enabled, is_immovable, is_physical)
        self.age = 0
        self.max_age = max_age
        self.is_alive = True
        self.is_talking = False
        self.talk_bubble_text = ""
        self.text_bubble_remaining_time = 0.0
        self.environment = None

    def update(self, dt):
        self.tick(dt)
        if self.max_age > 0:
            self.age += dt
            self.tick(dt)
            if self.age >= self.max_age:
                self.is_alive = False
                # if self.environment is not None: self.environment.remove(self)

    def tick(self, dt):
        if self.text_bubble_remaining_time > 0: self.text_bubble_remaining_time -= dt
        pass

    def get_text_bubble(self):
        return self.talk_bubble_text if (self.text_bubble_remaining_time > 0) else None

    def set_text_bubble(self, text, time=1):
        self.talk_bubble_text = text
        self.text_bubble_remaining_time = time
        pass

    def kill(self):
        self.is_alive = False
        self.on_kill()

    def on_kill(self):
        pass

class Particle(Entity):
    def __init__(self, x, y, width, height, texture, direction=Vec2(), max_age=1, gravity_enabled=True, is_immovable=False, is_physical=False):
        super().__init__(x, y, width, height, texture, 0, max_age, gravity_enabled, is_immovable, is_physical)
        self.accelerate(direction)

    def get_transparency(self):
        t = self.age / self.max_age
        return t*t

    def interact(self, other):
        return True # should skip collision

class TileBreakParticle(Particle):
    def __init__(self, block_pos, tile_type, size=Vec2(0.25,0.25), direction=Vec2(), max_age=1, gravity_enabled=True, is_immovable=False, is_physical=False):
        super().__init__((block_pos.x + random.random()) * TILE_SIZE, (block_pos.y + random.random()) * TILE_SIZE,
                         TILE_SIZE * size.x, TILE_SIZE * size.y, None, direction, max_age, gravity_enabled, is_immovable, is_physical)
        self.tile_type = tile_type
        self.uv_offset = create_transformation_matrix(
            position=Vec2(random.randint(0, 3), random.randint(0, 3)) * size * TILE_SIZE,
            size=Vec2(1,1))

    def get_uv(self):
        return self.uv_offset

class LivingEntity(Entity):
    def __init__(self, x, y, width, height, texture, mass, health, entity_type="npc", max_age=0, gravity_enabled=True, is_immovable=False, is_physical=False, animation_frames=1):
        super().__init__(x, y, width/animation_frames, height, texture, mass, max_age, gravity_enabled, is_immovable, is_physical)
        self.health = health
        self.max_health = health
        self.animation_frame = 0.0
        self.animation_frames = animation_frames
        self.texture_size = Vec2(width, height)
        self.texture_state = texture
        self.entity_type = entity_type
        self.state = LivingEntityState.IDLE
        self.animation_speed = 12

        self.is_jumping = False
        self.is_grounded = False
        self.is_traveling_left = False
        self.is_traveling_right = False
        self.jump_force = -1000*TILE_SIZE
        self.jump_height = 1.2
        self.movement_speed = 5*TILE_SIZE


        self.direction = Direction.RIGHT
        self.environment = None
        self.inventory = Inventory(size=9)

    def jump(self, dt):
        if not self.is_jumping and self.is_grounded:
            self.is_jumping = True
            # self.accelerate(vec2(0, -GRAVITY *2))

            vel = math.sqrt(2 * self.jump_height * GRAVITY)*TILE_SIZE
            self.position_old.y = self.position.y
            self.position.y -= vel * dt

    # def move(self, d):
    #     self.accelerate(d)

    def move_left(self, dt):
        # print(dt)
        # if self.get_velocity().x > -self.movement_speed:
        #     self.move(Vec2(-self.movement_speed / (dt * dt), 0))
        self.is_traveling_left = True
        self.direction = Direction.LEFT


    def move_right(self, dt):
        # print(dt)
        # if self.get_velocity().x < self.movement_speed:
        #     self.move(Vec2(self.movement_speed / (dt * dt), 0))
        self.is_traveling_right = True
        self.direction = Direction.RIGHT


    # def update(self, dt):
    #     super().update(dt)
    #
    # def tick(self, dt):
    #     super().tick(dt)

    def get_uv(self):
        if self.direction == Direction.LEFT:
            return create_transformation_matrix(size=Vec2(1,1), flip_x=True)
        return matrices["normal"]
        #     return [
        #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 0,
        #         self.animation_frame * self.size.x / self.texture_sheet_width, 1,
        #     ]
        # else:
        #     return [
        #         self.animation_frame * self.size.x / self.texture_sheet_width, 0,
        #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 1,
        #     ]

    # def update_state(self):
    #     self.state = PlayerState.IDLE_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.IDLE_LEFT
    #     if(self.is_crouching):
    #         self.state = PlayerState.CROUCHING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.CROUCHING_LEFT
    #     if(self.is_jumping):
    #         self.state = PlayerState.JUMPING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.JUMPING_LEFT

    def get_health(self):
        return self.health

    def update_position(self, dt):
        if not self.is_immovable:
            velocity = self.get_velocity()
            self.position_old = self.position.copy()
            diff = velocity + (self.acceleration * dt * dt)
            # diff.x = diff.x % 10*TILE_SIZE
            # diff.y = diff.y % 10*TILE_SIZE
            if diff.x > 5 * TILE_SIZE: diff.x = 5 * TILE_SIZE
            if diff.y > 5 * TILE_SIZE: diff.y = 5 * TILE_SIZE
            if diff.x < -5 * TILE_SIZE: diff.x = -5 * TILE_SIZE
            if diff.y < -5 * TILE_SIZE: diff.y = -5 * TILE_SIZE

            self.position.y += diff.y

            if self.is_grounded:
                if self.is_traveling_left:
                    self.position.x -= self.movement_speed * dt
                if self.is_traveling_right:
                    self.position.x += self.movement_speed * dt
            if not self.is_grounded:
                movement_diff = self.movement_speed * dt * 0.5
                if self.is_traveling_left:
                    self.position.x -= movement_diff
                    self.position_old.x -= movement_diff
                    # diff.x = max(movement_diff, diff.x)
                if self.is_traveling_right:
                    self.position.x += movement_diff
                    self.position_old.x += movement_diff
                    # diff.x = min(movement_diff, diff.x)
                self.position.x += diff.x

            # self.is_traveling_left = False
            # self.is_traveling_right = False

            self.acceleration = Vec2(0, 0)

    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.is_alive = False

    def heal(self, amount):
        if self.health < self.max_health:
            self.health = min(self.health + amount, self.max_health)

    def tick(self, dt):
        super().tick(dt)
        self.animation_frame += self.animation_speed*dt
        if self.animation_frame >= self.animation_frames:
            self.animation_frame = 0
        self.update_state(dt)

    # def get_uv(self):
    #     return [
    #         self.animation_frame * self.size.x / self.texture_sheet_width, 0,
    #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 1,
    #     ]

    def update_state(self, dt):
        # state = self.state
        if not self.is_grounded:
            state = LivingEntityState.JUMPING
        elif self.is_traveling_right or self.is_traveling_left:
            state = LivingEntityState.WALKING
        else:
            state = LivingEntityState.IDLE
        if state != self.state:
            self.state = state
            self.animation_frame = 0

    def interact(self, other) -> bool:
        return isinstance(other, Entity) or issubclass(type(other), Entity)

class Inventory:
    def __init__(self, size):
        self.size = size
        self.items = [None for _ in range(size)]
        self.slot = 0

    def get_current(self):
        return self.items[self.slot]

    def set_slot_pointer(self, slot_number):
        self.slot = slot_number % self.size

    def move_slot_pointer(self, amount):
        self.set_slot_pointer(self.slot + amount)

    def set_item(self, item_stack, slot_number):
        if self.items[slot_number] is None:
            self.items[slot_number] = item_stack
            return True
        return False

    def pick_item(self, item_stack):
        for p in range(self.size):
            if self.items[p] is not None and self.items[p].item.tile_type == item_stack.item.tile_type:
                self.items[p].count += item_stack.count
                return True
        for p in range(self.size):
            if self.items[p] is None:
                self.items[p] = item_stack
                return True
        return False

    def use(self, used_slot=-1):
        s = self.slot if used_slot < 0 or used_slot > len(self.items) else used_slot
        self.items[s].count -= 1
        if self.items[s].count < 1:
            self.items[s] = None

class Item:
    def __init__(self, tile_type):
        self.tile_type = tile_type

class ItemStack:
    def __init__(self, item: Item, count: int):
        self.count = count
        self.item = item

class ItemStackEntity(Entity):
    def __init__(self, x, y, stack: ItemStack, width=TILE_SIZE/2, height=TILE_SIZE/2, texture=None, mass=1, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, max_age, gravity_enabled, is_immovable, is_physical)
        self.stack = stack

    def interact(self, other):
        if isinstance(other, ItemStackEntity):
            if other.stack.item.tile_type == self.stack.item.tile_type:
                self.stack.count += other.stack.count
                other.kill()
        return isinstance(other, Entity) or issubclass(type(other), Entity)


class Player(LivingEntity):
    def __init__(self, x, y, width, height, texture, mass, health=16, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, health, "player", max_age, gravity_enabled, is_immovable, is_physical)


    def interact(self, other):
        if isinstance(other, ItemStackEntity):
            if self.inventory.pick_item(other.stack):
                other.kill()
        return super().interact(other)

class PlayerNPC(LivingEntity):
    def __init__(self, x, y, width, height, texture, mass, health=32, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, health, "npc", max_age, gravity_enabled, is_immovable, is_physical)



class Tile(RigidBody):

    def __init__(self, x, y, tile_type, is_physical=True, require_support=False):
        super().__init__(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE, None, 0, False, True, is_physical)
        self.tile_pos = Vec2(x, y)
        self.tile_type = tile_type
        self.state = [1,1]
        self.require_support = require_support

    def get_uv(self, tileset_width=6, tileset_height=4):
        # uv = [
        #     [self.state[0]/tileset_width,       1-self.state[1]/tileset_height],
        #     [(self.state[0] + 1)/tileset_width, 1-self.state[1]/tileset_height],
        #     [(self.state[0] + 1)/tileset_width, 1-(self.state[1]+1)/tileset_height],
        #     [self.state[0]/tileset_width,       1-(self.state[1]+1)/tileset_height],
        #     # [0/6, 1-1/4],
        #     # [1/6, 1-1/4],
        #     # [1/6, 0],
        #     # [0/6, 0]
        # ]
        # print(self.state, uv)
        return matrices["normal"]


    def update_state(self, neighbours:tuple, d_neighbours:tuple):
        """
        top, left, bottom, right
        """

        # mapping = {
        #     (0, 0, 0, 0): (3, 3),
        #     (0, 0, 1, 1): (0, 0),
        #     (0, 1, 1, 1): (1, 0),
        #     (0, 1, 1, 0): (2, 0),
        #     (1, 0, 1, 1): (0, 1),
        #     (1, 1, 1, 0): (2, 1),
        #     (1, 0, 0, 1): (0, 2),
        #     (1, 1, 0, 1): (1, 2),
        #     (1, 1, 0, 0): (2, 2),
        #     (0, 0, 1, 0): (3, 0),
        #     (1, 0, 1, 0): (3, 1),
        #     (1, 0, 0, 0): (3, 2),
        #     (0, 0, 0, 1): (0, 3),
        #     (0, 1, 0, 1): (1, 3),
        #     (0, 1, 0, 0): (2, 3),
        # }
        # self.state = mapping.get(neighbours)
        # if (self.state is None):
        #     self.state = [1, 1]
        #     pass

        match neighbours:

            case [0,0,0,0]: self.state = [3,3]

            case [0,0,1,1]: self.state = [0,0]
            case [0,1,1,1]: self.state = [1,0]
            case [0,1,1,0]: self.state = [2,0]

            case [1,0,1,1]: self.state = [0,1]
            case [1,1,1,0]: self.state = [2,1]

            case [1,0,0,1]: self.state = [0,2]
            case [1,1,0,1]: self.state = [1,2]
            case [1,1,0,0]: self.state = [2,2]

            case [0,0,1,0]: self.state = [3,0]
            case [1,0,1,0]: self.state = [3,1]
            case [1,0,0,0]: self.state = [3,2]

            case [0,0,0,1]: self.state = [0,3]
            case [0,1,0,1]: self.state = [1,3]
            case [0,1,0,0]: self.state = [2,3]

            case [1,1,1,1]:
                if not d_neighbours[3]:
                    if not d_neighbours[0]:
                        self.state = [4, 1]
                    else: self.state = [4, 0]
                elif not d_neighbours[0]:
                    self.state = [5, 0]
                else: self.state = [1, 1]

            case _: self.state = [1,1]
        pass


def coord_round(value):
    return math.floor(value) if value >= 0 else math.floor(value) - 1

class LivingEntityState(Enum):
    FALLBACK = 0
    IDLE = 1
    WALKING = 2
    RUNNING = 3
    JUMPING = 4
    CROUCHING = 5


class Direction(Enum):
    RIGHT = 0
    LEFT = 1

# Background layer class
class BackgroundLayer:
    def __init__(self, texture, speed, layer, movement_speed=0, is_immovable=False, waving=False):
        self.movement_speed = movement_speed
        self.texture, self.width, self.height = texture
        self.speed = speed
        self.layer = layer
        self.last_camera_offset = 0
        self.offset = 0
        self.is_immovable = is_immovable
        self.waving = waving


    def scroll(self, offset, screenWidth, dt):
        diff = self.last_camera_offset - offset
        self.offset += diff * self.speed / screenWidth + self.movement_speed * dt
        self.last_camera_offset = offset

# # Ground class
# class GroundTile(GameObject):
#     def __init__(self, x, y, texture, layer):
#         width, height = 64, 64
#         super().__init__(x, y, width, height, texture, layer, False)

# Create game objects

# country, capital = random.choice(list(d.items()))
# capital = random.choice(list(d.values()))

class FollowPoint(Enum):
    CENTER = Vec2(0.5, 0.6)
    LEFT = Vec2(0.6, 0.6)
    RIGHT = Vec2(0.4, 0.6)


# class Camera:
#     def __init__(self):
#         self.offset = Vec2()
#         self.scale = 1
#         self.zoom = 1
#         self.previous_follow_point = FollowPoint.CENTER
#         self.follow_point = FollowPoint.CENTER
#         self.follow_offset = Vec2()
#         self.last_follow_point_change = 0
#         self.renderBounds = pygame.Rect(0, 0, 0, 0)
#         self.render_distance = 10
#
#     def update_bounds(self, screenWidth, screenHeight):
#         self.renderBounds = pygame.Rect(0, 0, screenWidth, screenHeight)
#         self.render_distance = max(screenWidth, screenHeight) // TILE_SIZE + 1
#
#     def set_follow_point(self, fp):
#         self.previous_follow_point = self.follow_point
#         self.follow_point = fp
#         self.last_follow_point_change = 0
#
#     def follow(self, body, mouse_pos, dt):
#         if body is None: return
#         velocity = body.get_velocity()
#         self.last_follow_point_change += dt
#         is_le = isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity)
#         # next_follow_point = FollowPoint.CENTER
#         # if self.last_follow_point_change > 0.8:
#         #     if velocity.x > 0.1 or (is_le and body.is_traveling_right):
#         #         next_follow_point = FollowPoint.RIGHT
#         #     elif velocity.x < -0.1 or (is_le and body.is_traveling_left):
#         #         next_follow_point = FollowPoint.LEFT
#         #
#         # if next_follow_point != self.follow_point:
#         #     self.set_follow_point(next_follow_point)
#
#         fp_transition = 0.3
#         transition_coef = 1-fp_transition / (fp_transition - self.last_follow_point_change)
#         desired_follow_point = self.follow_point.value - (self.previous_follow_point.value - self.follow_point.value)*transition_coef
#         follow_offset_diff = self.follow_offset - desired_follow_point
#         # self.follow_offset -= follow_offset_diff * dt
#
#
#         object_center = (body.position + body.size*0.5) * self.get_scale()
#         screen_size = Vec2(self.renderBounds.width, self.renderBounds.height)
#         screen_center = screen_size * (self.follow_point.value + self.follow_offset)
#         follow_center = self.offset + object_center
#
#         diff = screen_center - follow_center
#
#         self.offset += diff
#         self.offset = Vec2(round(self.offset.x), round(self.offset.y))
#
#     def get_scale(self):
#         return self.scale * self.zoom



import pygame
import random
import math

class Camera:
    def __init__(self):
        self.offset = Vec2()
        self.scale = 1
        self.zoom = 1
        self.previous_follow_point = FollowPoint.CENTER
        self.follow_point = FollowPoint.CENTER
        self.follow_offset = Vec2()
        self.last_follow_point_change = 0
        self.renderBounds = pygame.Rect(0, 0, 0, 0)
        self.render_distance = 10

        # Shake state
        self.shake_time = 0.0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.shake_offset = Vec2()
        self._shake_seed = random.uniform(0, 1000)

    def update_bounds(self, screenWidth, screenHeight):
        self.renderBounds = pygame.Rect(0, 0, screenWidth, screenHeight)
        self.render_distance = max(screenWidth, screenHeight) // TILE_SIZE + 1

    def set_follow_point(self, fp):
        self.previous_follow_point = self.follow_point
        self.follow_point = fp
        self.last_follow_point_change = 0

    def shake(self, duration, strength):
        self.shake_duration = duration
        self.shake_time = duration
        self.shake_strength = strength
        self._shake_seed = random.uniform(0, 1000)

    def _smooth_noise(self, t, offset):
        # Простий псевдо-плавний шум (можна замінити на Perlin)
        return math.sin(t * 10 + offset + self._shake_seed)

    def update_shake(self, dt):
        if self.shake_time > 0:
            self.shake_time -= dt
            t = (self.shake_duration - self.shake_time)
            fade = self.shake_time / self.shake_duration

            # Плавні осциляції, що затухають
            angle = self._smooth_noise(t, 0) * math.pi * 2
            x = math.cos(angle + self._smooth_noise(t, 100)) * fade * self.shake_strength
            y = math.sin(angle + self._smooth_noise(t, 200)) * fade * self.shake_strength

            self.shake_offset = Vec2(x, y)
        else:
            self.shake_offset = Vec2()

    def follow(self, body, mouse_pos, dt):
        self.update_shake(dt)

        if body is None:
            return

        velocity = body.get_velocity()
        self.last_follow_point_change += dt

        is_le = isinstance(body, LivingEntity) or issubclass(type(body), LivingEntity)

        fp_transition = 0.3
        transition_coef = 1 - fp_transition / (fp_transition - self.last_follow_point_change)
        desired_follow_point = self.follow_point.value - (self.previous_follow_point.value - self.follow_point.value) * transition_coef
        follow_offset_diff = self.follow_offset - desired_follow_point

        object_center = (body.position + body.size * 0.5) * self.get_scale()
        screen_size = Vec2(self.renderBounds.width, self.renderBounds.height)
        screen_center = screen_size * (self.follow_point.value + self.follow_offset)
        follow_center = self.offset + object_center

        diff = screen_center - follow_center
        self.offset += diff
        self.offset = Vec2(round(self.offset.x), round(self.offset.y))

    def get_scale(self):
        return self.scale * self.zoom

    def get_offset(self):
        # Кінцевий зсув камери з тряскою
        return self.offset + self.shake_offset
