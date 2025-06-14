from src.shared.physics.objects import Entity, LivingEntity


class Projectile(Entity):
    """
    Game object with set trajectory and collision damage to living entities
    """
    def __init__(self, x, y, width, height, start_acceleration, damage, whitelist, texture, mass, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, max_age, gravity_enabled, is_immovable, is_physical)
        self.whitelist = whitelist
        self.start_acceleration = start_acceleration
        self.damage = damage

    def on_spawn(self):
        self.accelerate(self.start_acceleration)

    def interact(self, other, is_body1_inside=False, is_body2_inside=False) -> bool:
        if other not in self.whitelist:
            if isinstance(other, LivingEntity) or issubclass(type(other), LivingEntity):
                other.damage(self.damage)
                other.stunt(0.1)
                other.accelerate(self.start_acceleration * (self.mass / other.mass))
            self.kill()
        return True


class Bullet(Projectile):
    """
    Projectile unaffected by gravity
    """
    def __init__(self, x, y, width, height, start_acceleration, damage, whitelist, texture, mass, max_age=0, gravity_enabled=False, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, start_acceleration, damage, whitelist, texture, mass, max_age, gravity_enabled, is_immovable, is_physical)
