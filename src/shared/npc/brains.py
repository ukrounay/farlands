import random
from enum import *

from src.shared.utilites import *

MAX_JUMP_HEIGHT = 1
MAX_FALL_HEIGHT = 4


class Action:
    def __init__(self):
        pass

class WalkAction(Action):
    def __init__(self, jumps: list, dest: int, direction: Direction):
        super().__init__()
        reverse = direction == Direction.LEFT
        self.jumps = sorted(jumps, reverse=reverse)
        self.dest = dest
        self.direction = direction
        self.done = False


    # def do(self, walker, dt):
    #     if walker.position.x < TILE_SIZE*(self.dest + 0.5):
    #         walker.move(self.direction)
    #         print("move")
    #     else:
    #         walker.stop()
    #         # self.done = True
    #
    #     for i in range(len(self.jumps)):
    #         if TILE_SIZE*(self.jumps[i] - 0.5) < walker.position.x:
    #             walker.jump(dt)
    #             if walker.position.x < self.jumps[i]:
    #                 self.jumps.pop(i)
    #             break


    def do(self, walker, min_range, dt):
        dir_sign = self.direction.value  # -1 for LEFT, 1 for RIGHT

        target_x = TILE_SIZE * (self.dest + 0.5)
        walker_x = walker.position.x

        if abs(walker_x - target_x) > min_range:
            walker.move(self.direction)
            # print("move")
        else:
            walker.stop()
            self.done = True

        for i, jump_point in enumerate(self.jumps):
            jump_x = TILE_SIZE * jump_point
            if (jump_x - walker_x) * dir_sign > 0.5*TILE_SIZE:
                walker.jump(dt)
                break
            elif (jump_x - walker_x) * dir_sign < 0:
                self.jumps.pop(i)


        # for i in range(len(self.jumps)):
        #     jump_x = TILE_SIZE*(self.jumps[i] - 0.5 * dir_sign)
        #     if walker.position.x < TILE_SIZE * self.jumps[i]:
        #         self.jumps.pop(i)
        #         i -= 1
        #     if jump_x < walker.position.x:
        #         walker.jump(dt)
        #         break


class NPCBrain:
    def __init__(self, entity, world):
        self.min_range = 1
        self.target = None
        self.target_pos = None
        self.entity = entity
        self.action = None
        self.age = 0
        self.to_next_pathfind = 0
        self.path_update_time = 0.5
        self.world = world

    def can_walk_on(self, x, y) -> bool:
        return self.world.environment.map_manager.get_tile(x, y) is not None

    def is_supported(self, x, y) -> bool:
        return self.can_walk_on(x, y + 1)

    def update(self, dt):
        self.age += dt
        self.to_next_pathfind += dt
        if self.to_next_pathfind >= self.path_update_time:
            self.to_next_pathfind = 0
            self.find_path()
        if self.action is not None and self.action.done != True:
            self.action.do(self.entity, self.min_range, dt)

    def find_path(self):
        # print("finding path")
        if self.target is not None and self.entity is not None:
            self.target_pos = pos_world_to_map(self.target.position) + Vec2(round((random.random()-0.5)*self.min_range))
            start = pos_world_to_map(self.entity.position + Vec2(0, self.entity.size.y-1))
            d = self.target_pos.x - start.x
            if abs(d) < self.min_range:
                self.action = None
                return 
            direction = d / abs(d)
            n = int(direction * min(abs(d), 5))
            dest = start.x
            jumps = []
            last_height = int(start.y) - MAX_JUMP_HEIGHT
            for x in range(int(start.x), int(start.x) + n, int(direction)):
                can_go = False
                for y in range(int(start.y) - MAX_JUMP_HEIGHT, int(start.y) + MAX_FALL_HEIGHT):
                    if self.is_supported(x, y):
                        can_go = True
                        dest += int(direction)
                        if y < last_height:
                            jumps.append(x + (0 if direction > 0 else 1))
                        last_height = y
                        break
                if not can_go: break
            self.action = WalkAction(jumps, dest, Direction(direction))
            return
        self.action = None
