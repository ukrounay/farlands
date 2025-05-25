from src.shared.globals import TILE_SIZE
from src.shared.npc.brains import NPCBrain
from src.shared.physics.objects import LivingEntity, Player
from src.shared.utilites import pos_world_to_map


class PlayerNPC(LivingEntity):
    def __init__(self, world, x, y, width, height, texture, mass, health=32, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, health, "npc", max_age, gravity_enabled, is_immovable, is_physical)
        self.world = world
        self.brain = NPCBrain(self, world)

    def update(self, dt):
        super().update(dt)
        self.brain.update(dt)
        nearest_player = min(
            (body for body in self.world.environment.bodies if isinstance(body, Player)),
            key=lambda p: p.position.distance_to(self.position),
            default=None
        )
        self.brain.target = nearest_player