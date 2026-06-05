import pygame
from constants import *
from load_image import load_image
from time_state import get_time_ms, get_time_scale
import math
import random


class MovingSprite(pygame.sprite.Sprite):
    """Base class for projectiles and meteors that leave the screen."""

    def update(self):
        super(MovingSprite, self).update()

        if self.rect.centerx < -100 or self.rect.centerx > SCREEN_WIDTH + 100:
            self.kill()

    def update_animation(self):
        pass

    def collision_check(self, rect):
        # Combat objects remove themselves when their mask touches a target.
        if pygame.sprite.collide_mask(self, rect):
            self.kill()
            return True
        return False


class Shoot(MovingSprite):
    """Player projectile. Small shots are lasers, big shots are animated."""

    image = load_image("laser.png")
    frames = ['Fireball/fireball-1.png', 'Fireball/fireball-2.png', 'Fireball/fireball-3.png',
              'Fireball/fireball-4.png', 'Fireball/fireball-5.png', 'Fireball/fireball-6.png']

    def __init__(self, x, y, shoot_type='small', charge_power=0, angle_degrees=0):
        super(Shoot, self).__init__()
        self.shoot_type = shoot_type
        self.charge_power = max(0, min(charge_power, 1))
        self.angle_degrees = angle_degrees
        self.damage = 1
        self.velocity = pygame.Vector2(v_attack, 0)

        if self.shoot_type == 'small':
            self.image = pygame.transform.scale(Shoot.image, (50, 11))
            if self.angle_degrees:
                self.image = pygame.transform.rotate(self.image, -self.angle_degrees)
            radians = math.radians(self.angle_degrees)
            self.velocity = pygame.Vector2(math.cos(radians), math.sin(radians)) * v_attack
        else:
            self.cur_frame = 0
            self.damage = 2
            if self.shoot_type == 'charge':
                self.damage = 3 + int(5 * self.charge_power)
            self._set_fireball_image()
            if self.shoot_type == 'charge':
                self.velocity = pygame.Vector2(v_charge_attack, 0)
            else:
                self.velocity = pygame.Vector2(v_second_attack, 0)

        self.rect = self.image.get_rect()
        if self.shoot_type == 'small':
            self.rect.left = x
            self.rect.centery = y
        elif self.shoot_type == 'charge':
            self.rect.left = x
            self.rect.centery = y
        else:
            self.rect.left = x
            self.rect.top = y

        self.mask = pygame.mask.from_surface(self.image)

    def _set_fireball_image(self):
        width = 75
        height = 139
        if self.shoot_type == 'charge':
            width = int(width + 45 * self.charge_power)
            height = int(height + 60 * self.charge_power)

        center = self.rect.center if hasattr(self, 'rect') else None
        self.image = load_image(self.frames[self.cur_frame])
        self.image = pygame.transform.scale(self.image, (width, height))
        self.image = pygame.transform.rotate(self.image, 90)
        if center is not None:
            self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        super(Shoot, self).update()
        time_scale = get_time_scale()
        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale

    def update_animation(self):
        if self.shoot_type != 'small':
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self._set_fireball_image()


class Rocket(MovingSprite):
    """Heavy player missile that creates a short splash-damage burst."""

    def __init__(self, x, y):
        super(Rocket, self).__init__()
        self.damage = 4
        self.splash_damage = PLAYER_ROCKET_SPLASH_DAMAGE
        self.splash_radius = PLAYER_ROCKET_SPLASH_RADIUS
        self.velocity = pygame.Vector2(v_rocket_attack, 0)
        self.cur_frame = 0
        self.image = self._build_image()
        self.rect = self.image.get_rect(left=x, centery=y)
        self.mask = pygame.mask.from_surface(self.image)

    def _build_image(self):
        surface = pygame.Surface((82, 32), pygame.SRCALPHA)
        flame = (255, 151, 65) if self.cur_frame % 2 == 0 else (255, 224, 112)
        pygame.draw.polygon(surface, flame, ((0, 16), (16, 7), (16, 25)))
        pygame.draw.polygon(surface, (76, 223, 232), ((12, 16), (27, 10), (27, 22)))
        pygame.draw.rect(surface, (223, 230, 223), (24, 8, 42, 16), border_radius=6)
        pygame.draw.rect(surface, (84, 105, 129), (28, 12, 28, 8), border_radius=4)
        pygame.draw.polygon(surface, (255, 91, 84), ((62, 8), (80, 16), (62, 24)))
        pygame.draw.polygon(surface, (255, 232, 145), ((39, 2), (50, 8), (35, 8)))
        pygame.draw.polygon(surface, (255, 232, 145), ((39, 30), (50, 24), (35, 24)))
        return surface

    def update(self):
        super(Rocket, self).update()
        self.rect.x += self.velocity.x / FPS * get_time_scale()

    def update_animation(self):
        center = self.rect.center
        self.cur_frame = (self.cur_frame + 1) % 2
        self.image = self._build_image()
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)


class BossShoot(MovingSprite):
    """Boss fireball aimed at the player's position when it is created."""

    image = load_image("fireball.png")

    def __init__(self, x, y, x_player, y_player):
        super(BossShoot, self).__init__()

        self.x = x
        self.y = y
        self.x_player = x_player
        self.y_player = y_player

        self.image = BossShoot.image
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y

        self.k, self.b = self.make_moving_function()

        self.mask = pygame.mask.from_surface(self.image)

    def make_moving_function(self):
        if self.x - self.x_player != 0:
            k = (self.y - self.y_player) / (self.x - self.x_player)
            b = self.y - self.x * k
            return k, b
        return 0, self.y

    def update(self):
        super(BossShoot, self).update()
        self.rect.centerx -= v_boss_attack / FPS * get_time_scale()
        self.rect.centery = self.k * self.rect.x + self.b


class Background(pygame.sprite.Sprite):
    """Scrolling background tile used to create the moving-space effect."""

    image = load_image("background/space.png")

    def __init__(self, orientation=False):
        super(Background, self).__init__()

        self.image = Background.image
        if orientation:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.x -= v_background * get_time_scale()


class Boss(pygame.sprite.Sprite):
    """Original animated boss ship with the advanced attack hooks."""

    frames = ['Boss/ship_big-1.png', 'Boss/ship_big-2.png', 'Boss/ship_big-3.png', 'Boss/ship_big-4.png']
    frame_cache = {}

    def __init__(self, x, y):
        super(Boss, self).__init__()
        self.cur_frame = 0
        self.phase = 1
        self.hit_flash_until = 0
        self.dash_until = 0
        self.dash_velocity_y = 0
        self.image = self._build_image(pygame.time.get_ticks())
        self.rect = self.image.get_rect()
        self.rect.right = x
        self.rect.centery = y
        self.mask = pygame.mask.from_surface(self.image)

        self.moving = 1

    def _build_image(self, current_time):
        image = self._base_frame(self.frames[self.cur_frame]).copy()

        if current_time < self.hit_flash_until:
            flash = pygame.mask.from_surface(image).to_surface(
                setcolor=(255, 112, 64, 42),
                unsetcolor=(0, 0, 0, 0),
            )
            image.blit(flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        return image

    @classmethod
    def _base_frame(cls, frame):
        if frame not in cls.frame_cache:
            image = load_image(frame)
            image = pygame.transform.scale(image, (500, 375)).convert_alpha()
            cls.frame_cache[frame] = cls._remove_corner_background(image)
        return cls.frame_cache[frame]

    @staticmethod
    def _remove_corner_background(image, tolerance=8):
        cleaned = image.copy()
        key = cleaned.get_at((0, 0))
        width, height = cleaned.get_size()
        for y in range(height):
            for x in range(width):
                pixel = cleaned.get_at((x, y))
                if (
                    abs(pixel.r - key.r) <= tolerance
                    and abs(pixel.g - key.g) <= tolerance
                    and abs(pixel.b - key.b) <= tolerance
                ):
                    cleaned.set_at((x, y), (0, 0, 0, 0))
        return cleaned

    def set_phase(self, phase, current_time):
        self.phase = phase
        self.hit_flash_until = current_time + BOSS_PHASE_FLASH_MS
        center = self.rect.center
        self.image = self._build_image(current_time)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def take_hit(self, current_time, duration=BOSS_HIT_FLASH_MS):
        self.hit_flash_until = current_time + duration

    def start_dash(self, direction, current_time):
        self.dash_until = current_time + BOSS_DASH_MS
        self.dash_velocity_y = direction * BOSS_DASH_SPEED

    def cannon_positions(self):
        return [
            (self.rect.left + 62, self.rect.centery - 68),
            (self.rect.left + 62, self.rect.centery + 52),
        ]

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        center = self.rect.center
        self.image = self._build_image(get_time_ms())
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        current_time = get_time_ms()
        time_scale = get_time_scale()
        if current_time < self.dash_until:
            self.rect.centery += self.dash_velocity_y / FPS * time_scale
        elif self.moving == 1:
            self.rect.centery += (v_boss + (self.phase - 1) * 22) / FPS * time_scale
            if self.rect.bottom > SCREEN_HEIGHT - 100:
                self.moving *= -1
        else:
            self.rect.centery += -(v_boss + (self.phase - 1) * 22) / FPS * time_scale
            if self.rect.top < 0:
                self.moving *= -1

        if self.rect.bottom > SCREEN_HEIGHT - 100:
            self.rect.bottom = SCREEN_HEIGHT - 100
            self.moving = -1
        if self.rect.top < 0:
            self.rect.top = 0
            self.moving = 1


class Player(pygame.sprite.Sprite):
    """Animated player ship controlled by the keyboard."""

    frames = ['Player/ship-1.tiff', 'Player/ship-2.tiff', 'Player/ship-4.tiff']

    def __init__(self):
        super(Player, self).__init__()
        self.cur_frame = 0
        self.base_frames = [self._load_base_frame(frame) for frame in self.frames]
        self.image = self.base_frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.right = 10
        self.rect.centery = SCREEN_HEIGHT / 2

        self.position = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(0, 0)
        self.tilt_angle = 0
        self.invincible_until = 0
        self.charge_started_at = None
        self.next_normal_shot_at = 0
        self.next_spread_shot_at = 0
        self.next_rocket_available_at = 0
        self.next_charge_available_at = 0
        self.mask = pygame.mask.from_surface(self.image)

    def _load_base_frame(self, frame):
        image = load_image(frame)
        image = pygame.transform.flip(image, True, False)
        return pygame.transform.scale(image, (200, 100))

    def update_controls(self, input_state, dt, current_time, boss_left, slow_motion_active=False):
        """Update velocity, position, tilt, blink, and bounds from input."""
        max_speed_x = PLAYER_MAX_SPEED_X
        max_speed_y = PLAYER_MAX_SPEED_Y
        acceleration_x = PLAYER_ACCEL_X
        acceleration_y = PLAYER_ACCEL_Y
        deceleration_x = PLAYER_DECEL_X
        deceleration_y = PLAYER_DECEL_Y
        if slow_motion_active:
            max_speed_x *= PLAYER_SHIFT_SPEED_MULTIPLIER
            max_speed_y *= PLAYER_SHIFT_SPEED_MULTIPLIER
            acceleration_x *= PLAYER_SHIFT_ACCEL_MULTIPLIER
            acceleration_y *= PLAYER_SHIFT_ACCEL_MULTIPLIER
            deceleration_x *= PLAYER_SHIFT_ACCEL_MULTIPLIER
            deceleration_y *= PLAYER_SHIFT_ACCEL_MULTIPLIER

        self.velocity.x = self._accelerate_axis(
            self.velocity.x, input_state.move_x, acceleration_x, deceleration_x, max_speed_x, dt
        )
        self.velocity.y = self._accelerate_axis(
            self.velocity.y, input_state.move_y, acceleration_y, deceleration_y, max_speed_y, dt
        )

        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.center = round(self.position.x), round(self.position.y)

        self._update_tilt(max_speed_y)
        self._refresh_image(current_time)
        self.clamp_to_arena(boss_left)

    def _accelerate_axis(self, speed, direction, acceleration, deceleration, max_speed, dt):
        if direction:
            speed += direction * acceleration * dt
        elif speed > 0:
            speed = max(0, speed - deceleration * dt)
        elif speed < 0:
            speed = min(0, speed + deceleration * dt)

        return max(-max_speed, min(max_speed, speed))

    def _update_tilt(self, max_speed_y):
        if max_speed_y == 0:
            self.tilt_angle = 0
            return

        target_tilt = -self.velocity.y / max_speed_y * PLAYER_MAX_TILT
        self.tilt_angle += (target_tilt - self.tilt_angle) * 0.25

    def _refresh_image(self, current_time=None):
        center = self.rect.center
        self.image = pygame.transform.rotate(self.base_frames[self.cur_frame], self.tilt_angle)
        if current_time is not None and self.is_invincible(current_time):
            if (current_time // PLAYER_BLINK_MS) % 2 == 0:
                self.image.set_alpha(80)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def clamp_to_arena(self, boss_left=None):
        right_limit = boss_left if boss_left is not None else SCREEN_WIDTH
        bottom_limit = SCREEN_HEIGHT - 100

        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity.x = max(0, self.velocity.x)
        if self.rect.right > right_limit:
            self.rect.right = right_limit
            self.velocity.x = min(0, self.velocity.x)
        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity.y = max(0, self.velocity.y)
        if self.rect.bottom > bottom_limit:
            self.rect.bottom = bottom_limit
            self.velocity.y = min(0, self.velocity.y)

        self.position.update(self.rect.center)

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self._refresh_image(get_time_ms())

    def update_shooting(self, input_state, current_time, can_shoot=True):
        shots = []

        if not can_shoot:
            self.charge_started_at = None
            return shots

        if input_state.wants_small_shot and current_time >= self.next_normal_shot_at:
            shots.append(Shoot(self.rect.right, self.rect.top + 0.7 * self.rect.height))
            self.next_normal_shot_at = current_time + PLAYER_NORMAL_SHOT_COOLDOWN_MS

        if input_state.wants_spread_shot and current_time >= self.next_spread_shot_at:
            shots.extend(self._make_spread_shots())
            self.next_spread_shot_at = current_time + PLAYER_SPREAD_SHOT_COOLDOWN_MS

        if input_state.wants_rocket_shot and current_time >= self.next_rocket_available_at:
            shots.append(Rocket(self.rect.right - 4, self.rect.centery))
            self.next_rocket_available_at = current_time + PLAYER_ROCKET_COOLDOWN_MS

        if (
            (input_state.wants_charge_shot or input_state.pressed_charge_shot)
            and self.charge_started_at is None
            and current_time >= self.next_charge_available_at
        ):
            self.charge_started_at = current_time

        if self.charge_started_at is not None and input_state.released_charge_shot:
            shots.append(self._release_charge(current_time))

        return [shot for shot in shots if shot is not None]

    def _make_spread_shots(self):
        origin_x = self.rect.right - 2
        origin_y = self.rect.centery
        return [
            Shoot(origin_x, origin_y - 20, angle_degrees=-14),
            Shoot(origin_x + 10, origin_y, angle_degrees=0),
            Shoot(origin_x, origin_y + 20, angle_degrees=14),
        ]

    def _release_charge(self, current_time):
        charge_time = max(current_time - self.charge_started_at, PLAYER_CHARGE_MIN_MS)
        charge_time = min(charge_time, PLAYER_CHARGE_MAX_MS)
        charge_range = PLAYER_CHARGE_MAX_MS - PLAYER_CHARGE_MIN_MS
        charge_power = (charge_time - PLAYER_CHARGE_MIN_MS) / charge_range

        self.charge_started_at = None
        self.next_charge_available_at = current_time + PLAYER_CHARGE_COOLDOWN_MS
        return Shoot(self.rect.right, self.rect.centery, shoot_type='charge', charge_power=charge_power)

    def cooldown_progress(self, current_time, next_available_at, cooldown_ms):
        if current_time >= next_available_at:
            return 1
        return max(0, 1 - (next_available_at - current_time) / cooldown_ms)

    def charge_progress(self, current_time):
        if self.charge_started_at is None:
            return 0
        charge_time = min(current_time - self.charge_started_at, PLAYER_CHARGE_MAX_MS)
        return max(0, charge_time / PLAYER_CHARGE_MAX_MS)

    def draw_charge_effect(self, target_screen, current_time, offset=(0, 0)):
        if self.charge_started_at is None:
            return

        progress = self.charge_progress(current_time)
        center = self.rect.centerx + 36 + offset[0], self.rect.centery + offset[1]
        radius = 16 + int(22 * progress)
        color = (120 + int(100 * progress), 210, 255)
        pygame.draw.circle(target_screen, color, center, radius, 2)
        pygame.draw.circle(target_screen, (255, 244, 150), center, 5 + int(8 * progress), 1)

    @property
    def hitbox_rect(self):
        hitbox = pygame.Rect(0, 0, PLAYER_HITBOX_WIDTH, PLAYER_HITBOX_HEIGHT)
        hitbox.center = self.rect.center
        return hitbox

    def collides_with(self, sprite):
        return self.hitbox_rect.colliderect(sprite.rect)

    def draw_debug_hitbox(self, target_screen, offset=(0, 0)):
        pygame.draw.rect(target_screen, (80, 150, 255), self.rect.move(offset), 1)
        pygame.draw.rect(target_screen, (90, 255, 120), self.hitbox_rect.move(offset), 2)

    def is_invincible(self, current_time):
        return current_time < self.invincible_until

    def can_take_damage(self, current_time):
        return not self.is_invincible(current_time)

    def start_invincibility(self, current_time):
        self.invincible_until = current_time + PLAYER_INVINCIBLE_MS
        self._refresh_image(current_time)


class Meteor(MovingSprite):
    image = load_image("meteor.png")

    def __init__(self):
        super(Meteor, self).__init__()

        self.image = Meteor.image
        self.image = pygame.transform.scale(self.image, (75, 58.5))
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH
        self.rect.centery = random.randrange(SCREEN_HEIGHT - 100)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        super(Meteor, self).update()
        self.rect.centerx -= v_meteor / FPS * get_time_scale()


class Comet(MovingSprite):
    """Fast diagonal space hazard with a bright tail."""

    def __init__(self):
        super(Comet, self).__init__()
        self.velocity = pygame.Vector2(-v_comet, random.choice([-180, -120, 120, 180]))
        self.image = self._build_image()
        self.rect = self.image.get_rect()
        self.rect.left = SCREEN_WIDTH + random.randint(10, 140)
        self.rect.centery = random.randrange(60, SCREEN_HEIGHT - 160)
        self.mask = pygame.mask.from_surface(self.image)

    def _build_image(self):
        surface = pygame.Surface((150, 56), pygame.SRCALPHA)
        pygame.draw.polygon(surface, (255, 151, 82, 76), ((0, 28), (88, 5), (64, 28), (88, 51)))
        pygame.draw.polygon(surface, (91, 225, 239, 100), ((26, 28), (100, 13), (78, 28), (100, 43)))
        pygame.draw.circle(surface, (255, 238, 145), (112, 28), 18)
        pygame.draw.circle(surface, (255, 255, 255), (119, 23), 7)
        pygame.draw.circle(surface, (255, 98, 87), (105, 35), 6)
        return surface

    def update(self):
        time_scale = get_time_scale()
        self.rect.x += self.velocity.x / FPS * time_scale
        self.rect.y += self.velocity.y / FPS * time_scale
        if self.rect.right < -100 or self.rect.bottom < -70 or self.rect.top > SCREEN_HEIGHT + 70:
            self.kill()


class SpaceCrystal(MovingSprite):
    """Slow drifting shard that makes the space lane less predictable."""

    def __init__(self):
        super(SpaceCrystal, self).__init__()
        self.spawned_at = get_time_ms()
        self.velocity = pygame.Vector2(-v_space_crystal, random.choice([-55, -30, 30, 55]))
        self.image = self._build_image(self.spawned_at)
        self.rect = self.image.get_rect()
        self.rect.left = SCREEN_WIDTH + random.randint(20, 180)
        self.rect.centery = random.randrange(70, SCREEN_HEIGHT - 170)
        self.position = pygame.Vector2(self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def _build_image(self, current_time):
        pulse = 0.5 + 0.5 * math.sin((current_time - self.spawned_at) / 115)
        surface = pygame.Surface((74, 86), pygame.SRCALPHA)
        glow = 62 + int(55 * pulse)
        pygame.draw.polygon(surface, (61, 226, 238, glow), ((37, 0), (68, 35), (37, 85), (6, 35)))
        pygame.draw.polygon(surface, (132, 100, 255, 190), ((37, 7), (58, 35), (37, 74), (17, 35)))
        pygame.draw.polygon(surface, (233, 249, 255, 150), ((37, 7), (48, 34), (37, 74), (27, 35)))
        pygame.draw.line(surface, (255, 232, 145), (18, 35), (58, 35), 2)
        pygame.draw.line(surface, (255, 255, 255), (37, 8), (37, 74), 2)
        return surface

    def update(self):
        current_time = get_time_ms()
        time_scale = get_time_scale()
        self.position += self.velocity / FPS * time_scale
        self.position.y += math.sin((current_time - self.spawned_at) / 180) * 0.8 * time_scale
        center = round(self.position.x), round(self.position.y)
        self.image = self._build_image(current_time)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

        if self.rect.right < -100 or self.rect.bottom < -80 or self.rect.top > SCREEN_HEIGHT + 80:
            self.kill()


class Heart(pygame.sprite.Sprite):
    frames = ['Heart/heart-1.png', 'Heart/heart-2.png']

    def __init__(self, i):
        super(Heart, self).__init__()
        self.cur_frame = 0
        self.image = load_image(self.frames[self.cur_frame])
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.left = 50 + i * 50 + i * 10
        self.rect.top = SCREEN_HEIGHT - 100

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = load_image(self.frames[self.cur_frame])
        self.image = pygame.transform.scale(self.image, (50, 50))


class Boom(pygame.sprite.Sprite):
    frames = ['boom/boom-1.tiff', 'boom/boom-2.tiff', 'boom/boom-3.tiff', 'boom/boom-4.tiff', 'boom/boom-5.tiff',
              'boom/boom-6.tiff', 'boom/boom-7.tiff', 'boom/boom-8.tiff', 'boom/boom-9.tiff', 'boom/boom-10.tiff',
              'boom/boom-11.tiff', 'boom/boom-12.tiff']

    def __init__(self, x, y):
        super(Boom, self).__init__()
        self.cur_frame = 0
        self.image = load_image(self.frames[self.cur_frame])
        self.rect = self.image.get_rect()
        self.rect.centery = y
        self.rect.centerx = x

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = load_image(self.frames[self.cur_frame])
        if self.cur_frame == 11:
            self.kill()


class Fire(pygame.sprite.Sprite):
    frames = ['fire/fire-1.tiff', 'fire/fire-2.tiff', 'fire/fire-3.tiff', 'fire/fire-4.tiff', 'fire/fire-5.tiff',
              'fire/fire-6.tiff', 'fire/fire-7.tiff', 'fire/fire-8.tiff', 'fire/fire-9.tiff', 'fire/fire-10.tiff',
              'fire/fire-11.tiff', 'fire/fire-12.tiff', 'fire/fire-13.tiff', 'fire/fire-14.tiff', 'fire/fire-15.tiff',
              'fire/fire-16.tiff', 'fire/fire-17.tiff', 'fire/fire-18.tiff', 'fire/fire-19.tiff', 'fire/fire-20.tiff',
              'fire/fire-21.tiff', 'fire/fire-22.tiff', 'fire/fire-23.tiff', 'fire/fire-24.tiff', 'fire/fire-25.tiff',
              'fire/fire-26.tiff', 'fire/fire-27.tiff', 'fire/fire-28.tiff', 'fire/fire-29.tiff', 'fire/fire-30.tiff',
              'fire/fire-31.tiff', 'fire/fire-32.tiff', 'fire/fire-33.tiff', 'fire/fire-34.tiff', 'fire/fire-35.tiff',
              'fire/fire-36.tiff', 'fire/fire-37.tiff', 'fire/fire-38.tiff']

    anchors = [
        (0.55, 0.40),
        (0.68, 0.52),
        (0.46, 0.64),
        (0.62, 0.30),
        (0.76, 0.70),
    ]

    def __init__(self, boss, index):
        super(Fire, self).__init__()
        self.boss = boss
        self.index = max(1, min(index, len(self.anchors))) - 1
        self.cur_frame = 0
        self.image = self._make_image()
        self.rect = self.image.get_rect()
        self._sync_to_boss()

    def _make_image(self):
        image = load_image(self.frames[self.cur_frame])
        return pygame.transform.scale(image, (128, 72))

    def _sync_to_boss(self):
        x_ratio, y_ratio = self.anchors[self.index]
        self.rect.center = (
            self.boss.rect.left + int(self.boss.rect.width * x_ratio),
            self.boss.rect.top + int(self.boss.rect.height * y_ratio),
        )

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        center = self.rect.center
        self.image = self._make_image()
        self.rect = self.image.get_rect(center=center)

    def update(self):
        self._sync_to_boss()


class MeteorBoom(pygame.sprite.Sprite):
    frames = ['meteor_boom/meteor_boom-1.tiff', 'meteor_boom/meteor_boom-2.tiff', 'meteor_boom/meteor_boom-3.tiff',
              'meteor_boom/meteor_boom-4.tiff', 'meteor_boom/meteor_boom-5.tiff', 'meteor_boom/meteor_boom-6.tiff',
              'meteor_boom/meteor_boom-7.tiff', 'meteor_boom/meteor_boom-8.tiff', 'meteor_boom/meteor_boom-9.tiff']

    def __init__(self, x, y):
        super(MeteorBoom, self).__init__()
        self.cur_frame = 0
        self.image = load_image(self.frames[self.cur_frame])
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect.centery = y
        self.rect.centerx = x

    def update_animation(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = load_image(self.frames[self.cur_frame])
        self.image = pygame.transform.scale(self.image, (100, 100))
        if self.cur_frame == 8:
            self.kill()
