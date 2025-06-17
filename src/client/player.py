from src.shared.combat.bullet import Bullet
from src.shared.globals import TILE_SIZE
from src.shared.physics.objects import LivingEntity
from src.shared.utilites import Vec2


class Player(LivingEntity):
    def __init__(self, x, y, width, height, texture, mass, health=16, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, health, "player", max_age, gravity_enabled, is_immovable, is_physical)

    def use_item_in_hand(self, world, camera, textures, mouse_buttons, pos, tile_pointing, side_hit):
        m_l, m_m, m_r = mouse_buttons

        item_in_hand = self.inventory.get_current()

        if m_l:
            if item_in_hand is not None and item_in_hand.item.tile_type == "staff":
                acc = (pos - self.position).normalized() * (TILE_SIZE ** 3) * 10
                t = textures["projectiles"]['bullet']
                world.environment.add_body(
                    Bullet(self.position.x, self.position.y,
                           t[1], t[2], acc, 5, [self], t[0], 10, 2))
                self.add_pending_sound("fx", "bullet_fire")
                return True
            else:
                if tile_pointing is not None:
                    world.map_manager.delete_tile(tile_pointing.tile_pos)
                    self.add_pending_sound("fx", "break")
        elif m_r:

            stack = self.inventory.get_current()
            if not (tile_pointing is None or
                    stack is None or
                    stack.item is None or
                    stack.item.tile_type is None):
                append_pos = tile_pointing.tile_pos
                match side_hit:
                    case "top": append_pos += Vec2(0,1)
                    case "left": append_pos += Vec2(1, 0)
                    case "bottom": append_pos += Vec2(0, -1)
                    case "right": append_pos += Vec2(-1, 0)
                if world.map_manager.get_tile(append_pos.x, append_pos.y) is None:
                    world.map_manager.set_tile(append_pos.x, append_pos.y, stack.item.tile_type)
                    self.add_pending_sound("fx", "put")
                    self.inventory.use()

        return False


    def interact(self, other, is_body1_inside=False, is_body2_inside=False):
        return super().interact(other)