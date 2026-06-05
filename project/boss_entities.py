import math
import random

import pygame

from constants import *
from time_state import get_time_ms, get_time_scale


def _circle_surface(radius, color, outline=None):
    surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    center = radius + 2, radius + 2
    pygame.draw.circle(surface, color, center, radius)
    if outline is not None:
        pygame.draw.circle(surface, outline, center, radius, 2)
    return surface


class PhaseOverdriveEffect(pygame.sprite.Sprite):
    """Purely visual player burst used during boss phase transitions."""

    def __init__(self, player, boss, current_time):
        super(PhaseOverdriveEffect, self).__init__()
        self.player = player
        self.boss = boss
        self.birth_time = current_time
        self.expires_at = current_time + BOSS_PHASE_PAUSE_MS
        self.destructible = False
        self.pierces = True
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self._draw(current_time)

    def update(self):
        current_time = get_time_ms()
        if current_time >= self.expires_at:
            self.kill()
            return
        self._draw(current_time)

    def _draw(self, current_time):
        self.image.fill((0, 0, 0, 0))
        elapsed = current_time - self.birth_time
        progress = max(0, min(1, elapsed / BOSS_PHASE_PAUSE_MS))
        pulse = 0.5 + 0.5 * math.sin(current_time / 45)
        player_center = (self.player.rect.right + 28, self.player.rect.centery)
        boss_center = self.boss.rect.center
        charge_end = BOSS_PHASE_LASER_CHARGE_MS
        active_end = BOSS_PHASE_LASER_CHARGE_MS + BOSS_PHASE_LASER_ACTIVE_MS
        impact_strength = 0

        if elapsed < charge_end:
            stage = 'LASER CHARGING'
            stage_progress = max(0, min(1, elapsed / charge_end))
            beam_alpha = int(35 + 85 * stage_progress * pulse)
            beam_width = 2 + int(8 * stage_progress)
            ring_alpha = 155
        elif elapsed < active_end:
            stage = 'LASER ONLINE'
            stage_progress = max(0, min(1, (elapsed - charge_end) / BOSS_PHASE_LASER_ACTIVE_MS))
            beam_alpha = 210 + int(32 * pulse)
            beam_width = 22 + int(7 * pulse)
            ring_alpha = 120
            impact_strength = 0.82 + 0.18 * pulse
        else:
            stage = 'LASER SHUTDOWN'
            stage_progress = max(0, min(1, (elapsed - active_end) / BOSS_PHASE_LASER_SHUTDOWN_MS))
            beam_alpha = max(0, int(190 * (1 - stage_progress)))
            beam_width = max(2, int(18 * (1 - stage_progress)))
            ring_alpha = max(0, int(120 * (1 - stage_progress)))
            impact_strength = max(0, 0.5 * (1 - stage_progress))

        for index in range(3):
            radius = int(34 + progress * 330 + index * 38)
            alpha = max(0, int((ring_alpha - index * 28) * (1 - progress * 0.45)))
            pygame.draw.circle(self.image, (84, 226, 238, alpha), player_center, radius, 3)

        core_radius = 26 + int(12 * pulse)
        pygame.draw.circle(self.image, (255, 232, 145, 165), player_center, core_radius, 3)
        pygame.draw.circle(self.image, (255, 255, 255, 170), player_center, 7 + int(4 * pulse))

        if beam_alpha > 0:
            start = player_center
            end = boss_center
            pygame.draw.line(self.image, (91, 232, 238, beam_alpha), start, end, beam_width)
            pygame.draw.line(self.image, (255, 232, 145, min(255, beam_alpha + 25)), start, end,
                             max(2, beam_width // 3))
            pygame.draw.line(self.image, (255, 255, 255, min(255, beam_alpha + 30)), start, end,
                             max(1, beam_width // 6))

        if impact_strength > 0:
            self._draw_boss_impact(boss_center, current_time, impact_strength, beam_width)

        for index in range(8):
            angle = progress * math.tau * 1.4 + index * math.tau / 8
            distance = 62 + int(progress * 120)
            point = (
                player_center[0] + int(math.cos(angle) * distance),
                player_center[1] + int(math.sin(angle) * distance),
            )
            pygame.draw.circle(self.image, (255, 116, 95, 150), point, 4)

        target_radius = 44 + int(8 * pulse)
        pygame.draw.circle(self.image, (255, 112, 95, 145), boss_center, target_radius, 2)
        pygame.draw.line(self.image, (255, 232, 145, 135), (boss_center[0] - target_radius, boss_center[1]),
                         (boss_center[0] + target_radius, boss_center[1]), 2)
        pygame.draw.line(self.image, (255, 232, 145, 135), (boss_center[0], boss_center[1] - target_radius),
                         (boss_center[0], boss_center[1] + target_radius), 2)

        font = pygame.font.Font(None, 36)
        text = font.render(stage, True, (255, 232, 145))
        self.image.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 168)))

    def _draw_boss_impact(self, boss_center, current_time, strength, beam_width):
        pulse = 0.5 + 0.5 * math.sin(current_time / 34)
        impact_alpha = int(170 * strength)
        glow_radius = int(44 + 24 * strength + 12 * pulse)
        core_radius = int(max(8, beam_width * 0.7))

        pygame.draw.circle(self.image, (255, 96, 76, 72), boss_center, glow_radius + 18)
        pygame.draw.circle(self.image, (255, 214, 104, impact_alpha), boss_center, glow_radius, 3)
        pygame.draw.circle(self.image, (255, 255, 255, min(240, impact_alpha + 45)), boss_center, core_radius)
        pygame.draw.circle(self.image, (91, 232, 238, impact_alpha), boss_center, core_radius + 14, 3)

        for index in range(3):
            radius = int(glow_radius + index * 26 + pulse * 18)
            alpha = max(0, int((110 - index * 24) * strength))
            pygame.draw.circle(self.image, (255, 126, 88, alpha), boss_center, radius, 2)

        for index in range(18):
            angle = current_time / 42 + index * math.tau / 18
            inner = 18 + int(10 * math.sin(current_time / 55 + index))
            outer = 54 + int(34 * strength) + int(12 * math.cos(current_time / 63 + index * 1.7))
            start = (
                boss_center[0] + int(math.cos(angle) * inner),
                boss_center[1] + int(math.sin(angle) * inner),
            )
            end = (
                boss_center[0] + int(math.cos(angle) * outer),
                boss_center[1] + int(math.sin(angle) * outer),
            )
            color = (255, 232, 145, int(80 + 125 * strength)) if index % 3 else (91, 232, 238, 150)
            pygame.draw.line(self.image, color, start, end, 2)

        crack_color = (255, 104, 84, int(120 * strength))
        for angle in (-42, -16, 22, 48):
            radians = math.radians(angle + math.sin(current_time / 95) * 7)
            end = (
                boss_center[0] + int(math.cos(radians) * (70 + 12 * pulse)),
                boss_center[1] + int(math.sin(radians) * (36 + 8 * pulse)),
            )
            pygame.draw.line(self.image, crack_color, boss_center, end, 3)


class StormBullet(pygame.sprite.Sprite):
    """Plasma projectile used for aimed shots and spiral waves."""

    def __init__(self, x, y, velocity, radius=14, color=(83, 218, 255)):
        super(StormBullet, self).__init__()
        self.velocity = pygame.Vector2(velocity)
        self.destructible = True
        self.pierces = False
        self.image = _circle_surface(radius, color, (255, 229, 128))
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def collision_check(self, sprite):
        if pygame.sprite.collide_mask(self, sprite):
            self.kill()
            return True
        return False

    @classmethod
    def aimed(cls, x, y, target_x, target_y, speed, radius=14):
        direction = pygame.Vector2(target_x - x, target_y - y)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(-1, 0)
        direction = direction.normalize()
        return cls(x, y, direction * speed, radius)

    def update(self):
        time_scale = get_time_scale()
        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale
        if (
            self.rect.right < -120
            or self.rect.left > SCREEN_WIDTH + 120
            or self.rect.bottom < -120
            or self.rect.top > SCREEN_HEIGHT + 120
        ):
            self.kill()


class LightningWarning(pygame.sprite.Sprite):
    """Visible, non-damaging targeting column before an ion strike."""

    def __init__(self, x, current_time):
        super(LightningWarning, self).__init__()
        self.strike_at = current_time + BOSS_LIGHTNING_WARNING_MS
        self.x = x
        self.destructible = False
        self.pierces = True
        self.image = pygame.Surface((26, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=x, top=0)
        self._draw(current_time)

    def ready(self, current_time):
        return current_time >= self.strike_at

    def update(self):
        self._draw(get_time_ms())

    def _draw(self, current_time):
        self.image.fill((0, 0, 0, 0))
        pulse = 120 + int(90 * abs(math.sin(current_time / 80)))
        pygame.draw.rect(self.image, (87, 222, 255, pulse), (10, 0, 6, SCREEN_HEIGHT))
        pygame.draw.rect(self.image, (255, 255, 255, 120), (12, 0, 2, SCREEN_HEIGHT))
        pygame.draw.rect(self.image, (160, 104, 255, 70), (4, 0, 18, SCREEN_HEIGHT), 1)


class LightningBeam(pygame.sprite.Sprite):
    """Damaging ion beam spawned after the targeting column."""

    def __init__(self, x, current_time):
        super(LightningBeam, self).__init__()
        self.expires_at = current_time + BOSS_LIGHTNING_DURATION_MS
        self.destructible = False
        self.pierces = True
        self.image = pygame.Surface((74, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=x, top=0)
        self._draw()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if get_time_ms() >= self.expires_at:
            self.kill()

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, (72, 214, 255, 140), (14, 0, 46, SCREEN_HEIGHT))
        x = 37
        points = []
        for y in range(-20, SCREEN_HEIGHT + 40, 34):
            x += random.choice([-18, -10, 12, 20])
            x = max(18, min(56, x))
            points.append((x, y))
        pygame.draw.lines(self.image, (246, 252, 255), False, points, 8)
        pygame.draw.lines(self.image, (167, 105, 255), False, points, 4)
        pygame.draw.lines(self.image, (87, 230, 255), False, points, 2)


class RailWarning(pygame.sprite.Sprite):
    """Horizontal warning line before the boss fires a rail beam."""

    def __init__(self, y, current_time):
        super(RailWarning, self).__init__()
        self.strike_at = current_time + BOSS_RAIL_WARNING_MS
        self.destructible = False
        self.pierces = True
        self.image = pygame.Surface((SCREEN_WIDTH, 38), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centery=y, left=0)
        self._draw(current_time)

    def ready(self, current_time):
        return current_time >= self.strike_at

    def update(self):
        self._draw(get_time_ms())

    def _draw(self, current_time):
        self.image.fill((0, 0, 0, 0))
        pulse = 115 + int(95 * abs(math.sin(current_time / 75)))
        pygame.draw.rect(self.image, (255, 199, 79, pulse), (0, 16, SCREEN_WIDTH, 6))
        pygame.draw.rect(self.image, (255, 255, 255, 110), (0, 18, SCREEN_WIDTH, 2))
        for x in range(0, SCREEN_WIDTH, 72):
            pygame.draw.line(self.image, (94, 226, 234, 76), (x, 7), (x + 28, 31), 1)


class RailBeam(pygame.sprite.Sprite):
    """Fast horizontal laser lane used to force vertical dodges."""

    def __init__(self, y, current_time):
        super(RailBeam, self).__init__()
        self.expires_at = current_time + BOSS_RAIL_DURATION_MS
        self.destructible = False
        self.pierces = True
        self.image = pygame.Surface((SCREEN_WIDTH, 58), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centery=y, left=0)
        self._draw()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if get_time_ms() >= self.expires_at:
            self.kill()

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, (255, 103, 87, 120), (0, 12, SCREEN_WIDTH, 34))
        pygame.draw.rect(self.image, (255, 238, 150, 190), (0, 22, SCREEN_WIDTH, 14))
        pygame.draw.rect(self.image, (255, 255, 255, 230), (0, 27, SCREEN_WIDTH, 4))
        for y in (10, 47):
            pygame.draw.line(self.image, (89, 230, 235, 110), (0, y), (SCREEN_WIDTH, y), 2)


class GravityMine(pygame.sprite.Sprite):
    """Destructible plasma mine that bursts into bullets if ignored."""

    def __init__(self, x, y, current_time, hard_mode=False):
        super(GravityMine, self).__init__()
        self.bursts_at = current_time + BOSS_MINE_ARM_MS
        self.spawned_at = current_time
        self.destructible = True
        self.pierces = False
        drift = BOSS_MINE_DRIFT_SPEED * (1.2 if hard_mode else 1)
        self.velocity = pygame.Vector2(-drift, random.choice([-24, -12, 12, 24]))
        self.position = pygame.Vector2(x, y)
        self.image = pygame.Surface((68, 68), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._draw(current_time)
        self.mask = pygame.mask.from_surface(self.image)

    def ready_to_burst(self, current_time):
        return current_time >= self.bursts_at

    def collision_check(self, sprite):
        if pygame.sprite.collide_mask(self, sprite):
            self.kill()
            return True
        return False

    def update(self):
        current_time = get_time_ms()
        time_scale = get_time_scale()
        self.position += self.velocity / FPS * time_scale
        self.rect.center = round(self.position.x), round(self.position.y)

        if self.rect.top < 12 or self.rect.bottom > SCREEN_HEIGHT - 112:
            self.velocity.y *= -1
            self.position.y = self.rect.centery

        if self.rect.right < -80:
            self.kill()
            return

        center = self.rect.center
        self._draw(current_time)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def burst_bullets(self, phase, hard_mode=False):
        count = 9 + phase * 2 + (2 if hard_mode else 0)
        speed = BOSS_MINE_BULLET_SPEED + phase * 24
        bullets = []

        for index in range(count):
            angle = math.radians(360 / count * index)
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            bullets.append(StormBullet(
                self.rect.centerx,
                self.rect.centery,
                velocity,
                radius=9,
                color=(174, 104, 255),
            ))

        return bullets

    def _draw(self, current_time):
        self.image.fill((0, 0, 0, 0))
        pulse = 0.5 + 0.5 * math.sin((current_time - self.spawned_at) / 95)
        core = 12 + int(5 * pulse)
        pygame.draw.circle(self.image, (123, 73, 180, 92), (34, 34), 31)
        pygame.draw.circle(self.image, (57, 231, 238, 126), (34, 34), 25, 2)
        pygame.draw.circle(self.image, (255, 221, 116), (34, 34), core)
        pygame.draw.circle(self.image, (255, 255, 255), (34, 34), 5)
        for angle in (0, 120, 240):
            radians = math.radians(angle + current_time / 12)
            point = (34 + int(math.cos(radians) * 28), 34 + int(math.sin(radians) * 28))
            pygame.draw.circle(self.image, (255, 110, 100), point, 4)


class HomingBolt(pygame.sprite.Sprite):
    """Destructible boss shot that gently turns toward the player."""

    def __init__(self, x, y, target, hard_mode=False):
        super(HomingBolt, self).__init__()
        self.target = target
        self.destructible = True
        self.pierces = False
        speed = BOSS_HOMING_BOLT_SPEED * (1.12 if hard_mode else 1)
        self.velocity = pygame.Vector2(-speed, random.uniform(-90, 90))
        self.turn_rate = BOSS_HOMING_TURN_RATE * (1.25 if hard_mode else 1)
        self.spawned_at = get_time_ms()
        self.image = pygame.Surface((58, 34), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._draw(self.spawned_at)
        self.mask = pygame.mask.from_surface(self.image)

    def collision_check(self, sprite):
        if pygame.sprite.collide_mask(self, sprite):
            self.kill()
            return True
        return False

    def update(self):
        current_time = get_time_ms()
        time_scale = get_time_scale()
        target_vector = pygame.Vector2(self.target.rect.center) - pygame.Vector2(self.rect.center)
        if target_vector.length_squared() > 0:
            desired = target_vector.normalize() * max(1, self.velocity.length())
            self.velocity = self.velocity.lerp(desired, self.turn_rate * time_scale)

        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale

        if (
            self.rect.right < -100
            or self.rect.left > SCREEN_WIDTH + 100
            or self.rect.bottom < -100
            or self.rect.top > SCREEN_HEIGHT + 100
        ):
            self.kill()
            return

        center = self.rect.center
        self._draw(current_time)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def _draw(self, current_time):
        self.image.fill((0, 0, 0, 0))
        pulse = 0.5 + 0.5 * math.sin((current_time - self.spawned_at) / 70)
        pygame.draw.ellipse(self.image, (111, 230, 255, 105), (4, 4, 50, 26))
        pygame.draw.ellipse(self.image, (255, 230, 120, 170), (12, 9, 34, 16))
        pygame.draw.circle(self.image, (255, 255, 255), (22 + int(6 * pulse), 17), 6)
        pygame.draw.polygon(self.image, (168, 104, 255, 155), ((4, 17), (17, 7), (14, 17), (17, 27)))


class DroneMinion(pygame.sprite.Sprite):
    """Small escort drone launched by the dreadnought."""

    def __init__(self, x, y, target_x, target_y, hard_mode=False):
        super(DroneMinion, self).__init__()
        self.health = BOSS_MINION_HEALTH + int(hard_mode)
        speed = BOSS_MINION_SPEED * (1.18 if hard_mode else 1)
        direction = pygame.Vector2(target_x - x, target_y - y)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(-1, 0)
        self.velocity = direction.normalize() * speed
        self.spawned_at = get_time_ms()
        self.image = self._build_image()
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def _build_image(self):
        surface = pygame.Surface((82, 54), pygame.SRCALPHA)
        hull = (96, 122, 151)
        dark = (19, 25, 39)
        glow = (83, 222, 255)
        wing = (55, 68, 96)

        pygame.draw.polygon(surface, wing, [(20, 12), (58, 4), (46, 22)])
        pygame.draw.polygon(surface, wing, [(20, 42), (58, 50), (46, 32)])
        pygame.draw.polygon(surface, dark, [(5, 27), (28, 12), (68, 20), (76, 27), (68, 34), (28, 42)])
        pygame.draw.polygon(surface, hull, [(15, 27), (32, 18), (62, 22), (68, 27), (62, 32), (32, 36)])
        pygame.draw.circle(surface, glow, (28, 27), 7)
        pygame.draw.circle(surface, (242, 250, 255), (28, 27), 3)
        pygame.draw.circle(surface, (255, 106, 108), (70, 27), 5)
        pygame.draw.line(surface, (178, 211, 229), (38, 21), (58, 24), 2)
        pygame.draw.line(surface, (178, 211, 229), (38, 33), (58, 30), 2)
        return surface

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False

    def update(self):
        time_scale = get_time_scale()
        wave = math.sin((get_time_ms() - self.spawned_at) / 180) * 0.7
        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale + wave * time_scale
        if (
            self.rect.right < -80
            or self.rect.left > SCREEN_WIDTH + 120
            or self.rect.bottom < -80
            or self.rect.top > SCREEN_HEIGHT + 80
        ):
            self.kill()


class Particle(pygame.sprite.Sprite):
    """Short-lived hit and explosion particle."""

    def __init__(self, x, y, velocity, color, radius=4, lifetime=PARTICLE_LIFETIME_MS):
        super(Particle, self).__init__()
        self.velocity = pygame.Vector2(velocity)
        self.birth_time = get_time_ms()
        self.lifetime = lifetime
        self.radius = radius
        self.color = color
        self.image = _circle_surface(radius, color)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        age = get_time_ms() - self.birth_time
        if age >= self.lifetime:
            self.kill()
            return

        time_scale = get_time_scale()
        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale
        alpha = max(0, 255 - int(255 * age / self.lifetime))
        self.image = _circle_surface(self.radius, (*self.color[:3], alpha))
