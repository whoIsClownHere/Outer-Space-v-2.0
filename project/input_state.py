import pygame


class InputState:
    """Reads the current keyboard snapshot and key-release events."""

    def __init__(self):
        self.keys = None
        self.pressed_key_events = set()
        self.released_keys = set()

    def refresh(self, events=None):
        self.keys = pygame.key.get_pressed()
        self.pressed_key_events = set()
        self.released_keys = set()

        if events is None:
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                self.pressed_key_events.add(event.key)
            if event.type == pygame.KEYUP:
                self.released_keys.add(event.key)

    def is_pressed(self, key):
        return self.keys is not None and self.keys[key]

    def was_released(self, key):
        return key in self.released_keys

    def was_pressed(self, key):
        return key in self.pressed_key_events

    @property
    def move_x(self):
        return int(self.is_pressed(pygame.K_RIGHT)) - int(self.is_pressed(pygame.K_LEFT))

    @property
    def move_y(self):
        return int(self.is_pressed(pygame.K_DOWN)) - int(self.is_pressed(pygame.K_UP))

    @property
    def slow_mode(self):
        return self.is_pressed(pygame.K_LSHIFT) or self.is_pressed(pygame.K_RSHIFT)

    @property
    def debug_hitboxes(self):
        return self.is_pressed(pygame.K_F3)

    @property
    def wants_small_shot(self):
        return self.is_pressed(pygame.K_SPACE)

    @property
    def wants_spread_shot(self):
        return self.is_pressed(pygame.K_z)

    @property
    def wants_rocket_shot(self):
        return self.is_pressed(pygame.K_c)

    @property
    def wants_charge_shot(self):
        return self.is_pressed(pygame.K_x)

    @property
    def pressed_charge_shot(self):
        return self.was_pressed(pygame.K_x)

    @property
    def released_charge_shot(self):
        return self.was_released(pygame.K_x)
