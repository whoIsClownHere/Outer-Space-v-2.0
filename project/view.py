import math
import random
import pygame
from boss_entities import (
    DroneMinion,
    GravityMine,
    HomingBolt,
    LightningBeam,
    LightningWarning,
    Particle,
    PhaseOverdriveEffect,
    RailBeam,
    RailWarning,
    StormBullet,
)
from constants import *
from gameplay import (
    boss_is_active,
    clamp_player_to_arena,
    initial_health_for_mode,
    score_from_boss_health,
)
from input_state import InputState
from load_image import BEST_SCORE_PATH, get_game_mouse_pos, load_image, present_screen, screen, screen_to_game_pos
from sprites import Boss, Background, Player, Meteor, Comet, SpaceCrystal, Heart, Boom, Fire, MeteorBoom
from time_state import set_time_state

pygame.init()

MENU_FRAMES = [
    'Menu/space-1.tiff', 'Menu/space-2.tiff', 'Menu/space-3.tiff', 'Menu/space-4.tiff',
    'Menu/space-5.tiff', 'Menu/space-6.tiff', 'Menu/space-7.tiff', 'Menu/space-8.tiff',
    'Menu/space-9.tiff', 'Menu/space-10.tiff', 'Menu/space-11.tiff', 'Menu/space-12.tiff',
    'Menu/space-13.tiff', 'Menu/space-14.tiff', 'Menu/space-15.tiff', 'Menu/space-16.tiff',
    'Menu/space-17.tiff', 'Menu/space-18.tiff', 'Menu/space-19.tiff', 'Menu/space-20.tiff',
    'Menu/space-21.tiff', 'Menu/space-22.tiff', 'Menu/space-23.tiff', 'Menu/space-24.tiff'
]


class GameView:
    """Owns screen flow and delegates gameplay details to focused helpers."""

    def __init__(self):
        self.player = None
        self.heart = None
        self.hearts = PLAYER_HEARTS

        self.boss = None
        self.boss_hearts = BOSS_HEARTS

        self.first_background = None
        self.second_background = None
        self.third_background = None
        self.meteor = None
        self.boom = None
        self.fire = None
        self.meteor_boom = None

        self.boss_attacks = pygame.sprite.Group()
        self.player_attacks = pygame.sprite.Group()
        self.all_backgrounds = pygame.sprite.Group()
        self.all_meteors = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.all_hearts = pygame.sprite.Group()
        self.all_boom = pygame.sprite.Group()
        self.all_boss_damage = pygame.sprite.Group()
        self.lightning_warnings = pygame.sprite.Group()
        self.rail_warnings = pygame.sprite.Group()
        self.drone_minions = pygame.sprite.Group()
        self.all_particles = pygame.sprite.Group()
        self.phase_overdrive = pygame.sprite.Group()

        self.input_state = InputState()
        self.boss_max_hearts = BOSS_HEARTS
        self.boss_phase = 1
        self.phase_pause_until = 0
        self.phase_banner_until = 0
        self.phase_banner_text = ''
        self.shake_until = 0
        self.shake_strength = 0
        self.next_aimed_shot_at = 0
        self.next_spiral_at = 0
        self.pending_spiral_at = None
        self.pending_spiral_variant = 'arc'
        self.next_lightning_at = 0
        self.next_minion_at = 0
        self.next_meteor_at = 0
        self.next_rail_at = 0
        self.next_mine_at = 0
        self.next_homing_at = 0
        self.next_nova_at = 0
        self.last_attack_variants = {}
        self.next_phase_impact_at = 0
        self.last_real_time_ms = 0
        self.slow_motion_energy_ms = SLOW_MOTION_MAX_MS
        self.slow_motion_active = False
        self.boss_defeated_at = None
        self.next_defeat_boom_at = 0

    def _boss_display_name(self):
        return 'Original Boss'

    def _make_menu_background(self):
        background = pygame.sprite.Sprite()
        self._set_menu_background_frame(background, 0)
        return background

    def _set_menu_background_frame(self, background, frame_index):
        background.image = load_image(MENU_FRAMES[frame_index])
        background.image = pygame.transform.scale(background.image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        background.rect = background.image.get_rect()

    def _draw_panel(self, rect, fill=(8, 13, 27, 205), border=(99, 205, 230), radius=12):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
        if border is not None:
            pygame.draw.rect(panel, border, panel.get_rect(), 2, border_radius=radius)
        screen.blit(panel, rect.topleft)

    def _draw_text(self, text, font, position, color=(245, 244, 221), anchor='topleft'):
        rendered = font.render(text, True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, position)
        screen.blit(rendered, rect)
        return rect

    def _draw_button_frame(self, rect, hovered=False, selected=False):
        frame = rect.inflate(26, 16)
        fill = (14, 22, 40, 150)
        border = (255, 231, 137) if hovered or selected else (80, 164, 200)
        width = 3 if hovered or selected else 1
        panel = pygame.Surface(frame.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, border, panel.get_rect(), width, border_radius=10)
        screen.blit(panel, frame.topleft)

    def _draw_corner_brackets(self, rect, color=(120, 235, 232), length=28, width=2):
        points = (
            ((rect.left, rect.top + length), (rect.left, rect.top), (rect.left + length, rect.top)),
            ((rect.right - length, rect.top), (rect.right, rect.top), (rect.right, rect.top + length)),
            ((rect.left, rect.bottom - length), (rect.left, rect.bottom), (rect.left + length, rect.bottom)),
            ((rect.right - length, rect.bottom), (rect.right, rect.bottom), (rect.right, rect.bottom - length)),
        )
        for start, corner, end in points:
            pygame.draw.line(screen, color, start, corner, width)
            pygame.draw.line(screen, color, corner, end, width)

    def _draw_menu_atmosphere(self, frame_index):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 70), (0, 0, 505, SCREEN_HEIGHT))
        pygame.draw.rect(overlay, (0, 0, 0, 46), (0, 0, SCREEN_WIDTH, 80))
        pygame.draw.rect(overlay, (0, 0, 0, 58), (0, SCREEN_HEIGHT - 105, SCREEN_WIDTH, 105))
        for y in range(0, SCREEN_HEIGHT, 8):
            pygame.draw.line(overlay, (210, 255, 246, 11), (0, y), (SCREEN_WIDTH, y))
        for x in range(52, SCREEN_WIDTH, 92):
            pygame.draw.line(overlay, (82, 218, 220, 18), (x, 0), (x - 180, SCREEN_HEIGHT), 1)
        screen.blit(overlay, (0, 0))

        pulse = 0.5 + 0.5 * math.sin(frame_index * 0.38)
        accent = (65, 226, 216)
        pygame.draw.line(screen, accent, (40, 38), (188 + int(24 * pulse), 38), 2)
        pygame.draw.line(screen, accent, (40, 38), (40, 112), 2)
        pygame.draw.line(screen, accent, (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 38),
                         (SCREEN_WIDTH - 220 - int(24 * pulse), SCREEN_HEIGHT - 38), 2)
        pygame.draw.line(screen, accent, (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 38),
                         (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 112), 2)

    def _draw_hud_panel(self, rect, fill=(3, 9, 18, 112), border=(73, 210, 221, 165), radius=6):
        self._draw_panel(rect, fill=fill, border=border, radius=radius)
        self._draw_corner_brackets(rect, (122, 237, 230), length=22, width=2)

    def _draw_radar(self, center, radius, frame_index):
        sweep = frame_index * 0.24
        for index, ring in enumerate((radius, int(radius * 0.68), int(radius * 0.36))):
            color = (42 + index * 22, 160 + index * 25, 168 + index * 26)
            pygame.draw.circle(screen, color, center, ring, 1)
        pygame.draw.line(screen, (65, 226, 216), (center[0] - radius, center[1]), (center[0] + radius, center[1]), 1)
        pygame.draw.line(screen, (65, 226, 216), (center[0], center[1] - radius), (center[0], center[1] + radius), 1)
        end = (
            center[0] + int(math.cos(sweep) * radius),
            center[1] + int(math.sin(sweep) * radius),
        )
        pygame.draw.line(screen, (255, 232, 145), center, end, 2)
        pygame.draw.circle(screen, (255, 232, 145), center, 4)

    def _load_pixel_sprite(self, name, size, flip=False, trim_corner=False,
                           corner_tolerance=8, dominant_backgrounds=0):
        image = load_image(name).copy()
        if trim_corner:
            image = self._remove_corner_background(image, corner_tolerance, dominant_backgrounds)
        if flip:
            image = pygame.transform.flip(image, True, False)
        return pygame.transform.scale(image, size).convert_alpha()

    def _remove_corner_background(self, image, tolerance, dominant_backgrounds=0):
        image = image.convert_alpha()
        key = image.get_at((0, 0))
        width, height = image.get_size()
        background_colors = [(key.r, key.g, key.b)]

        if dominant_backgrounds:
            sampled_colors = {}
            for y in range(0, height, 2):
                for x in range(0, width, 2):
                    pixel = image.get_at((x, y))
                    color = (pixel.r, pixel.g, pixel.b)
                    sampled_colors[color] = sampled_colors.get(color, 0) + 1
            dominant_colors = sorted(sampled_colors.items(), key=lambda item: item[1], reverse=True)
            for color, _ in dominant_colors[:dominant_backgrounds]:
                if color not in background_colors:
                    background_colors.append(color)

        min_x = width
        min_y = height
        max_x = -1
        max_y = -1

        for y in range(height):
            for x in range(width):
                pixel = image.get_at((x, y))
                is_background = False
                for red, green, blue in background_colors:
                    if (
                        abs(pixel.r - red) <= tolerance
                        and abs(pixel.g - green) <= tolerance
                        and abs(pixel.b - blue) <= tolerance
                    ):
                        is_background = True
                        break
                if is_background:
                    image.set_at((x, y), (0, 0, 0, 0))
                elif pixel.a > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if max_x >= min_x and max_y >= min_y:
            bounds = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
            return image.subsurface(bounds).copy()
        return image

    def _draw_ship_showcase(self, ship, frame_index, title_font, small_font):
        center = (1005, 350 + int(math.sin(frame_index * 0.32) * 8))
        self._draw_radar(center, 164, frame_index)

        glow = pygame.Surface((380, 220), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (56, 240, 208, 34), glow.get_rect())
        screen.blit(glow, (center[0] - 220, center[1] - 92))

        ship_rect = ship.get_rect(center=center)
        screen.blit(ship, ship_rect)
        engine_x = ship_rect.left + 22
        engine_y = ship_rect.centery
        pygame.draw.polygon(screen, (255, 205, 91), (
            (engine_x, engine_y),
            (engine_x - 74, engine_y - 20),
            (engine_x - 48, engine_y),
            (engine_x - 74, engine_y + 20),
        ))
        pygame.draw.polygon(screen, (78, 231, 221), (
            (engine_x - 5, engine_y),
            (engine_x - 46, engine_y - 11),
            (engine_x - 33, engine_y),
            (engine_x - 46, engine_y + 11),
        ))

        label_rect = pygame.Rect(870, 474, 320, 76)
        self._draw_hud_panel(label_rect, fill=(3, 9, 18, 86), border=(80, 205, 218, 125), radius=5)
        self._draw_text('PX-17 READY', title_font, (label_rect.left + 24, label_rect.top + 18), (255, 232, 145))
        self._draw_text('laser system charged', small_font,
                        (label_rect.left + 24, label_rect.top + 50), (166, 222, 226))

    def _draw_menu_button(self, rect, title, subtitle, title_font, subtitle_font,
                          hovered=False, danger=False, code=None):
        border = (255, 232, 145) if hovered else (73, 210, 221)
        accent = border
        if danger:
            border = (255, 154, 136) if hovered else (174, 91, 99)
            accent = border

        if hovered:
            glow = pygame.Surface(rect.inflate(18, 18).size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*accent, 42), glow.get_rect(), border_radius=8)
            screen.blit(glow, rect.inflate(18, 18).topleft)

        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill = (5, 13, 24, 138) if hovered else (5, 13, 24, 88)
        pygame.draw.rect(button, fill, button.get_rect(), border_radius=6)
        pygame.draw.line(button, border, (0, 0), (rect.width - 18, 0), 2)
        pygame.draw.line(button, border, (18, rect.height - 1), (rect.width, rect.height - 1), 2)
        pygame.draw.polygon(button, (*accent, 180), ((0, 0), (34, 0), (0, 34)))
        pygame.draw.polygon(button, border, ((rect.width - 24, rect.height // 2 - 9),
                                             (rect.width - 9, rect.height // 2),
                                             (rect.width - 24, rect.height // 2 + 9)))
        screen.blit(button, rect.topleft)

        code_font = pygame.font.Font(None, 20)
        title_color = (255, 232, 145) if hovered else (244, 249, 236)
        if danger and hovered:
            title_color = (255, 218, 211)
        if code is not None:
            self._draw_text(code, code_font, (rect.left + 20, rect.top + 13), (143, 232, 226))
            text_left = rect.left + 58
        else:
            text_left = rect.left + 24
        self._draw_text(title, title_font, (text_left, rect.top + 12), title_color)
        self._draw_text(subtitle, subtitle_font, (text_left, rect.top + 43), (158, 212, 220))

    def _draw_mode_card(self, card, title_font, text_font, small_font, hovered=False):
        rect = card['rect']
        border = (255, 232, 145, 190) if hovered else (72, 206, 220, 145)
        fill = (4, 11, 22, 144) if hovered else (4, 11, 22, 92)
        self._draw_hud_panel(rect, fill=fill, border=border, radius=6)

        accent = (255, 232, 145) if hovered else (73, 210, 221)
        pygame.draw.line(screen, accent, (rect.left + 24, rect.top + 22), (rect.left + 24, rect.bottom - 24), 3)
        self._draw_text(card['tagline'].upper(), small_font, (rect.left + 42, rect.top + 18), (150, 220, 224))
        self._draw_text(card['title'], title_font, (rect.left + 42, rect.top + 43), (245, 248, 236))
        self._draw_text(card['stat'], text_font, (rect.left + 42, rect.top + 82), (255, 232, 145))
        self._draw_text(card['description'][0], small_font, (rect.left + 42, rect.bottom - 52), (218, 235, 238))
        self._draw_text(card['description'][1], small_font, (rect.left + 42, rect.bottom - 27), (143, 202, 210))
        pygame.draw.polygon(screen, accent, ((rect.right - 38, rect.bottom - 34),
                                             (rect.right - 19, rect.bottom - 24),
                                             (rect.right - 38, rect.bottom - 14)))

    def _format_percent(self, value):
        text = ('%.2f' % value).rstrip('0').rstrip('.')
        return text + '%'

    def _draw_best_score_badge(self, rect, font):
        score = '0%'
        try:
            with open(BEST_SCORE_PATH, 'r') as f:
                data = f.read().strip()
                if data:
                    score = self._format_percent(float(data))
        except (OSError, ValueError):
            pass

        self._draw_hud_panel(rect, fill=(3, 9, 18, 92), border=(72, 206, 220, 135), radius=6)
        label_font = pygame.font.Font(None, 21)
        self._draw_text('MISSION RECORD', label_font, (rect.left + 18, rect.top + 10), (145, 214, 220))
        self._draw_text(score, font, (rect.right - 18, rect.top + 24), (255, 232, 145), anchor='topright')

    def _draw_controls_panel(self, rect):
        self._draw_hud_panel(rect, fill=(3, 9, 18, 94), border=(82, 214, 224, 135), radius=6)
        title_font = pygame.font.Font(None, 28)
        value_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 21)

        self._draw_text('PX-17 TELEMETRY', title_font, (rect.left + 22, rect.top + 18), (255, 232, 145))
        telemetry = [
            ('SPACE', 'LASER'),
            ('Z', 'SPREAD'),
            ('X', 'CHARGE'),
            ('C', 'ROCKET'),
        ]
        x = rect.left + 244
        for label, value in telemetry:
            self._draw_text(label, small_font, (x, rect.top + 15), (145, 214, 220))
            self._draw_text(value, value_font, (x, rect.top + 40), (245, 248, 236))
            x += 98

    def menu(self):
        """Main menu screen with animated space background."""
        set_time_state(1, pygame.time.get_ticks())
        clock = pygame.time.Clock()
        running = True

        timer_animation = pygame.USEREVENT
        pygame.time.set_timer(timer_animation, 70)

        cur_frame = 0
        background = self._make_menu_background()

        title = self._load_pixel_sprite('Buttons/Outer space.png', (530, 86), trim_corner=True, corner_tolerance=3)
        title_rect = title.get_rect(topleft=(70, 62))
        nav_panel = pygame.Rect(70, 178, 372, 414)
        controls_panel = pygame.Rect(690, 610, 636, 74)
        button_rects = {
            'play': pygame.Rect(104, 286, 304, 70),
            'levels': pygame.Rect(104, 374, 304, 70),
            'quit': pygame.Rect(104, 462, 304, 70),
        }
        best_score_rect = pygame.Rect(104, 542, 304, 48)
        title_font = pygame.font.Font(None, 36)
        button_font = pygame.font.Font(None, 35)
        button_subtitle_font = pygame.font.Font(None, 22)
        badge_font = pygame.font.Font(None, 34)
        hint_font = pygame.font.Font(None, 24)
        micro_font = pygame.font.Font(None, 21)
        ship_label_font = pygame.font.Font(None, 32)
        ship_preview = self._load_pixel_sprite(
            'Player/ship-1.tiff', (305, 142), flip=True, trim_corner=True,
            corner_tolerance=8, dominant_backgrounds=2
        )
        buttons = (
            ('play', 'START', 'story sortie', False, '01'),
            ('levels', 'MODES', 'difficulty and route', False, '02'),
            ('quit', 'EXIT', 'close terminal', True, '03'),
        )

        while running:
            screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_pos = screen_to_game_pos(event.pos)
                    if click_pos is None:
                        continue

                    if button_rects['quit'].collidepoint(click_pos):
                        running = False

                    if button_rects['play'].collidepoint(click_pos):
                        self.setup()
                        player_result = self.game_life()
                        if player_result:
                            self.game_over(type_over='win')
                        elif not player_result:
                            self.game_over()

                    if button_rects['levels'].collidepoint(click_pos):
                        self.levels_menu()

                if event.type == timer_animation:
                    cur_frame = (cur_frame + 1) % len(MENU_FRAMES)
                    self._set_menu_background_frame(background, cur_frame)

            mouse_pos = get_game_mouse_pos()
            screen.blit(background.image, background.rect)
            self._draw_menu_atmosphere(cur_frame)
            screen.blit(title, title_rect)
            pygame.draw.line(screen, (73, 210, 221), (title_rect.left + 8, title_rect.bottom + 12),
                             (title_rect.left + 408, title_rect.bottom + 12), 2)
            self._draw_text('SECTOR GREEN / START TERMINAL', micro_font,
                            (title_rect.left + 10, title_rect.bottom + 21), (147, 219, 224))

            self._draw_hud_panel(nav_panel, fill=(3, 9, 18, 92), border=(72, 206, 220, 132), radius=6)
            self._draw_text('COMMAND CONSOLE', title_font, (nav_panel.left + 34, nav_panel.top + 31),
                            (255, 232, 145))
            self._draw_text('pre-launch protocol active', hint_font,
                            (nav_panel.left + 34, nav_panel.top + 68), (154, 212, 218))

            for key, label, subtitle, danger, code in buttons:
                rect = button_rects[key]
                self._draw_menu_button(rect, label, subtitle, button_font, button_subtitle_font,
                                       rect.collidepoint(mouse_pos), danger, code)

            self._draw_ship_showcase(ship_preview, cur_frame, ship_label_font, micro_font)
            self._draw_controls_panel(controls_panel)
            self._draw_best_score_badge(best_score_rect, badge_font)
            self._draw_text('ABORT CHANNEL ARMED', micro_font, (92, 650), (152, 205, 214))

            clock.tick(FPS)
            present_screen()

    def _draw_boss_label(self, rect, font):
        self._draw_hud_panel(rect, fill=(3, 9, 18, 104), border=(72, 206, 220, 138), radius=6)
        label_font = pygame.font.Font(None, 22)
        self._draw_text('MISSION TARGET', label_font, (rect.left + 22, rect.top + 11), (145, 214, 220))
        self._draw_text(self._boss_display_name(), font, (rect.left + 22, rect.top + 33), (255, 232, 145))

    def levels_menu(self):
        """Mode selection screen for story, infinity, and hard."""
        set_time_state(1, pygame.time.get_ticks())
        clock = pygame.time.Clock()
        running = True

        timer_animation = pygame.USEREVENT
        pygame.time.set_timer(timer_animation, 70)

        cur_frame = 0
        background = self._make_menu_background()

        title = self._load_pixel_sprite('Buttons/Outer space.png', (460, 75), trim_corner=True, corner_tolerance=3)
        title_rect = title.get_rect(topleft=(70, 54))
        boss_font = pygame.font.Font(None, 34)
        heading_font = pygame.font.Font(None, 46)
        card_title_font = pygame.font.Font(None, 38)
        text_font = pygame.font.Font(None, 27)
        small_font = pygame.font.Font(None, 23)
        micro_font = pygame.font.Font(None, 21)
        boss_label_rect = pygame.Rect(860, 96, 350, 76)
        route_panel = pygame.Rect(70, 172, 438, 180)
        back_rect = pygame.Rect(78, 594, 220, 60)
        boss_preview = self._load_pixel_sprite('Boss/ship_big-1.png', (475, 250), trim_corner=True, corner_tolerance=6)

        mode_cards = [
            {
                'rect': pygame.Rect(78, 394, 386, 164),
                'game_type': 'story',
                'title': 'Story',
                'tagline': 'Classic fight',
                'stat': '5 hearts',
                'description': ('Defeat the boss.', 'Best warm-up route.'),
            },
            {
                'rect': pygame.Rect(508, 394, 386, 164),
                'game_type': 'infinity',
                'title': 'Infinity',
                'tagline': 'Score run',
                'stat': 'Endless boss',
                'description': ('Reach the highest percent.', 'Record is saved.'),
            },
            {
                'rect': pygame.Rect(938, 394, 386, 164),
                'game_type': 'hard',
                'title': 'Hard',
                'tagline': 'More pressure',
                'stat': '3 hearts',
                'description': ('Faster, denser attacks.', 'For confident pilots.'),
            },
        ]

        while running:
            screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_pos = screen_to_game_pos(event.pos)
                    if click_pos is None:
                        continue

                    if back_rect.collidepoint(click_pos):
                        running = False

                    for card in mode_cards:
                        if card['rect'].collidepoint(click_pos):
                            self.setup()
                            game_type = card['game_type']
                            if game_type == 'story':
                                player_result = self.game_life()
                            else:
                                player_result = self.game_life(game_type=game_type)

                            if player_result:
                                self.game_over(type_over='win', game_type=game_type)
                            elif not player_result:
                                self.game_over(game_type=game_type)

                if event.type == timer_animation:
                    cur_frame = (cur_frame + 1) % len(MENU_FRAMES)
                    self._set_menu_background_frame(background, cur_frame)

            mouse_pos = get_game_mouse_pos()
            screen.blit(background.image, background.rect)
            self._draw_menu_atmosphere(cur_frame)
            screen.blit(title, title_rect)
            pygame.draw.line(screen, (73, 210, 221), (title_rect.left + 8, title_rect.bottom + 12),
                             (title_rect.left + 348, title_rect.bottom + 12), 2)
            self._draw_text('MISSION ROUTER / ACTIVE SECTOR', micro_font,
                            (title_rect.left + 10, title_rect.bottom + 21), (147, 219, 224))

            self._draw_hud_panel(route_panel, fill=(3, 9, 18, 82), border=(72, 206, 220, 126), radius=6)
            self._draw_text('MODE SELECT', heading_font, (route_panel.left + 30, route_panel.top + 24),
                            (255, 232, 145))
            self._draw_text('sector pressure and heart reserve calculated', small_font,
                            (route_panel.left + 31, route_panel.top + 75), (174, 226, 229))
            pygame.draw.line(screen, (73, 210, 221), (route_panel.left + 31, route_panel.top + 119),
                             (route_panel.right - 34, route_panel.top + 119), 1)
            self._draw_text('route circuit awaiting command', small_font,
                            (route_panel.left + 31, route_panel.top + 137), (145, 202, 209))

            preview_center = (965, 288 + int(math.sin(cur_frame * 0.27) * 7))
            self._draw_radar(preview_center, 145, cur_frame)
            boss_rect = boss_preview.get_rect(center=preview_center)
            screen.blit(boss_preview, boss_rect)
            self._draw_text('SIGNATURE LOCK', micro_font, (preview_center[0] - 108, preview_center[1] + 154),
                            (255, 232, 145))

            for card in mode_cards:
                hovered = card['rect'].collidepoint(mouse_pos)
                self._draw_mode_card(card, card_title_font, text_font, small_font, hovered)

            self._draw_boss_label(boss_label_rect, boss_font)
            self._draw_menu_button(back_rect, 'Back', 'main menu', text_font, small_font,
                                   back_rect.collidepoint(mouse_pos), code='00')

            clock.tick(FPS)
            present_screen()

    def game_over(self, type_over='lose', game_type=None):
        """Game over and win screen, including best-score persistence."""
        set_time_state(1, pygame.time.get_ticks())
        clock = pygame.time.Clock()
        score = score_from_boss_health(self.boss_hearts, game_type)
        running = True

        if type_over == 'win':
            title = load_image('Buttons/YOU WIN.png')
        else:
            title = load_image('Buttons/GAME OVER.png')

        best_score_value = 0
        try:
            with open(BEST_SCORE_PATH, 'r') as f:
                data = f.read().strip()
                if data:
                    best_score_value = float(data)
        except (OSError, ValueError):
            best_score_value = 0

        if score > best_score_value:
            best_score_value = score
            with open(BEST_SCORE_PATH, 'w') as f:
                f.write(str(score))

        quit_button = pygame.sprite.Sprite()
        quit_button.image = load_image('Buttons/back.png')
        quit_button.rect = quit_button.image.get_rect()
        quit_button.rect.centerx = SCREEN_WIDTH / 2
        quit_button.rect.bottom = SCREEN_HEIGHT - 70

        timer_animation = pygame.USEREVENT
        pygame.time.set_timer(timer_animation, 70)
        cur_frame = 0
        background = self._make_menu_background()
        panel = pygame.Rect(392, 250, 616, 245)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 148))
        label_font = pygame.font.Font(None, 32)
        value_font = pygame.font.Font(None, 58)
        hint_font = pygame.font.Font(None, 25)

        while running:
            screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_pos = screen_to_game_pos(event.pos)
                    if click_pos is None:
                        continue

                    if quit_button.rect.collidepoint(click_pos):
                        running = False

                if event.type == timer_animation:
                    cur_frame = (cur_frame + 1) % len(MENU_FRAMES)
                    self._set_menu_background_frame(background, cur_frame)

            mouse_pos = get_game_mouse_pos()
            screen.blit(background.image, background.rect)
            screen.blit(title, title_rect)
            self._draw_panel(panel, fill=(8, 13, 27, 218), border=(255, 231, 137), radius=16)

            self._draw_text('Score', label_font, (panel.left + 58, panel.top + 54), (158, 204, 224))
            self._draw_text(self._format_percent(score), value_font, (panel.right - 58, panel.top + 42),
                            (245, 244, 221), anchor='topright')
            pygame.draw.line(screen, (68, 137, 170), (panel.left + 48, panel.top + 122),
                             (panel.right - 48, panel.top + 122), 2)
            self._draw_text('Best score', label_font, (panel.left + 58, panel.top + 154), (158, 204, 224))
            self._draw_text(self._format_percent(best_score_value), value_font, (panel.right - 58, panel.top + 142),
                            (255, 231, 137), anchor='topright')

            self._draw_button_frame(quit_button.rect, quit_button.rect.collidepoint(mouse_pos))
            screen.blit(quit_button.image, quit_button.rect)
            self._draw_text('Esc - back', hint_font, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 34),
                            (152, 196, 214), anchor='center')

            clock.tick(FPS)
            present_screen()

    def _reset_sprite_groups(self):
        """Start each game run with clean sprite groups."""
        self.boss_attacks = pygame.sprite.Group()
        self.player_attacks = pygame.sprite.Group()
        self.all_backgrounds = pygame.sprite.Group()
        self.all_meteors = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.all_hearts = pygame.sprite.Group()
        self.all_boom = pygame.sprite.Group()
        self.all_boss_damage = pygame.sprite.Group()
        self.lightning_warnings = pygame.sprite.Group()
        self.rail_warnings = pygame.sprite.Group()
        self.drone_minions = pygame.sprite.Group()
        self.all_particles = pygame.sprite.Group()
        self.phase_overdrive = pygame.sprite.Group()

    def setup(self):
        # Gameplay sprites are rebuilt for every run while menu sprites stay local
        # to their screens.
        self._reset_sprite_groups()

        self.first_background = Background()

        self.first_background.rect.left = 0
        self.first_background.rect.top = 0

        self.all_backgrounds.add(self.first_background)

        self.second_background = Background(orientation=True)

        self.second_background.rect.left = self.first_background.rect.right
        self.second_background.rect.top = 0

        self.all_backgrounds.add(self.second_background)

        self.third_background = Background()

        self.third_background.rect.left = self.second_background.rect.right
        self.third_background.rect.top = 0

        self.all_backgrounds.add(self.third_background)

        self.player = Player()

        self.boss = Boss(SCREEN_WIDTH, SCREEN_HEIGHT / 2)

        self.all_sprites.add(self.first_background)
        self.all_sprites.add(self.second_background)
        self.all_sprites.add(self.third_background)
        self.all_sprites.add(self.boss)
        self.all_sprites.add(self.player)

        self.hearts, self.boss_hearts = initial_health_for_mode('story')
        self.input_state = InputState()
        self.boss_max_hearts = BOSS_HEARTS
        self._reset_boss_fight_state()

    def _reset_boss_fight_state(self):
        self.boss_phase = 1
        self.phase_pause_until = 0
        self.phase_banner_until = 0
        self.phase_banner_text = ''
        self.shake_until = 0
        self.shake_strength = 0
        self.next_aimed_shot_at = 0
        self.next_spiral_at = 0
        self.pending_spiral_at = None
        self.pending_spiral_variant = 'arc'
        self.next_lightning_at = 0
        self.next_minion_at = 0
        self.next_meteor_at = 0
        self.next_rail_at = 0
        self.next_mine_at = 0
        self.next_homing_at = 0
        self.next_nova_at = 0
        self.last_attack_variants = {}
        self.next_phase_impact_at = 0
        self.last_real_time_ms = 0
        self.slow_motion_energy_ms = SLOW_MOTION_MAX_MS
        self.slow_motion_active = False
        self.boss_defeated_at = None
        self.next_defeat_boom_at = 0

    def _start_boss_fight_timers(self, current_time, game_type):
        self._reset_boss_fight_state()
        if hasattr(self.boss, 'phase'):
            self.boss.phase = 1
        self.next_aimed_shot_at = current_time + 480
        self.next_spiral_at = current_time + 1750
        self.next_lightning_at = current_time + 3000
        self.next_minion_at = current_time + 3300
        self.next_meteor_at = current_time + self._attack_interval(BOSS_METEOR_INTERVAL_MS, game_type)
        self.next_rail_at = current_time + 2300
        self.next_mine_at = current_time + 2650
        self.next_homing_at = current_time + 3600
        self.next_nova_at = current_time + 5200

    def _update_boss_fight(self, current_time, game_type):
        if self._boss_is_defeated(game_type):
            self._update_boss_defeat(current_time)
            return

        if not boss_is_active(self.boss_hearts, game_type):
            return

        self._update_boss_phase(current_time)
        if current_time < self.phase_pause_until:
            self._update_phase_overdrive_impact(current_time)
            return

        self._update_lightning_warnings(current_time)
        self._update_rail_warnings(current_time)
        self._update_gravity_mines(current_time, game_type)
        self._update_aimed_fireballs(current_time, game_type)
        self._update_spiral_attack(current_time, game_type)
        self._update_lightning_attack(current_time, game_type)
        self._update_drone_minions(current_time, game_type)
        self._update_meteor_pressure(current_time, game_type)
        self._update_rail_attack(current_time, game_type)
        self._update_minefield_attack(current_time, game_type)
        self._update_homing_attack(current_time, game_type)
        self._update_nova_attack(current_time, game_type)

    def _boss_phase_for_health(self):
        if self.boss_max_hearts <= 0:
            return 1

        ratio = max(0, self.boss_hearts) / self.boss_max_hearts
        if ratio > BOSS_PHASE_TWO_RATIO:
            return 1
        if ratio > BOSS_PHASE_THREE_RATIO:
            return 2
        return 3

    def _update_boss_phase(self, current_time):
        new_phase = self._boss_phase_for_health()
        if new_phase <= self.boss_phase:
            return

        self.boss_phase = new_phase
        if hasattr(self.boss, 'set_phase'):
            self.boss.set_phase(new_phase, current_time)
        self.phase_pause_until = current_time + BOSS_PHASE_PAUSE_MS
        self.phase_banner_until = current_time + BOSS_PHASE_PAUSE_MS
        self.phase_banner_text = 'Laser transition - phase ' + str(new_phase)
        self._start_screen_shake(SCREEN_SHAKE_PHASE_STRENGTH, SCREEN_SHAKE_PHASE_MS, current_time)
        self._spawn_particles(self.boss.rect.centerx, self.boss.rect.centery, 32, (255, 230, 118), 260)
        self._clear_phase_transition_hazards()
        self._delay_boss_timers_until_after_phase(current_time)
        self._spawn_phase_overdrive(current_time)
        self.next_phase_impact_at = current_time + BOSS_PHASE_LASER_CHARGE_MS

    def _spawn_phase_overdrive(self, current_time):
        for effect in list(self.phase_overdrive):
            effect.kill()
        effect = PhaseOverdriveEffect(self.player, self.boss, current_time)
        self.phase_overdrive.add(effect)
        self.all_sprites.add(effect)

    def _phase_transition_elapsed(self, current_time):
        return BOSS_PHASE_PAUSE_MS - max(0, self.phase_pause_until - current_time)

    def _phase_laser_is_active(self, current_time):
        elapsed = self._phase_transition_elapsed(current_time)
        active_start = BOSS_PHASE_LASER_CHARGE_MS
        active_end = BOSS_PHASE_LASER_CHARGE_MS + BOSS_PHASE_LASER_ACTIVE_MS
        return active_start <= elapsed < active_end

    def _update_phase_overdrive_impact(self, current_time):
        if not self._phase_laser_is_active(current_time):
            return
        if current_time < self.next_phase_impact_at:
            return

        self.next_phase_impact_at = current_time + BOSS_PHASE_LASER_IMPACT_INTERVAL_MS
        if hasattr(self.boss, 'take_hit'):
            self.boss.take_hit(current_time, BOSS_PHASE_LASER_IMPACT_FLASH_MS)
        self._start_screen_shake(4, BOSS_PHASE_LASER_IMPACT_INTERVAL_MS, current_time)
        impact_x, impact_y = self.boss.rect.center
        self._spawn_particles(impact_x, impact_y, 8, (255, 118, 82), 185)
        self._spawn_particles(impact_x, impact_y, 5, (91, 232, 238), 150)

    def _clear_phase_transition_hazards(self):
        for group in (
            self.boss_attacks,
            self.player_attacks,
            self.lightning_warnings,
            self.rail_warnings,
            self.drone_minions,
            self.all_meteors,
        ):
            for sprite in list(group):
                sprite.kill()
        self.pending_spiral_at = None

    def _delay_boss_timers_until_after_phase(self, current_time):
        resume_at = current_time + BOSS_PHASE_PAUSE_MS
        self.next_aimed_shot_at = resume_at + 420
        self.next_spiral_at = resume_at + 950
        self.next_lightning_at = resume_at + 1700
        self.next_minion_at = resume_at + 2100
        self.next_meteor_at = resume_at + 650
        self.next_rail_at = resume_at + 1300
        self.next_mine_at = resume_at + 1550
        self.next_homing_at = resume_at + 1850
        self.next_nova_at = resume_at + 2800

    def _choose_attack_variant(self, key, variants):
        if len(variants) <= 1:
            variant = variants[0]
        else:
            previous = self.last_attack_variants.get(key)
            choices = [candidate for candidate in variants if candidate != previous]
            variant = random.choice(choices or variants)
        self.last_attack_variants[key] = variant
        return variant

    def _add_boss_attack(self, attack):
        self.boss_attacks.add(attack)
        self.all_sprites.add(attack)

    def _velocity_toward(self, origin_x, origin_y, target_x, target_y, speed, angle_offset=0):
        direction = pygame.Vector2(target_x - origin_x, target_y - origin_y)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(-1, 0)
        direction = direction.normalize()
        if angle_offset:
            direction = direction.rotate(angle_offset)
        return direction * speed

    def _spawn_aimed_storm_bullet(self, origin_x, origin_y, target_x, target_y,
                                  speed, radius=14, color=(83, 218, 255), angle_offset=0):
        velocity = self._velocity_toward(origin_x, origin_y, target_x, target_y, speed, angle_offset)
        self._add_boss_attack(StormBullet(origin_x, origin_y, velocity, radius=radius, color=color))

    def _clamp_lightning_x(self, x):
        return max(120, min(SCREEN_WIDTH - 320, int(x)))

    def _clamp_rail_y(self, y):
        return max(58, min(SCREEN_HEIGHT - 132, int(y)))

    def _update_aimed_fireballs(self, current_time, game_type):
        if current_time < self.next_aimed_shot_at:
            return

        variants = ['single', 'double_tap']
        if self.boss_phase >= 2:
            variants.extend(['fan', 'pincer'])
        if self.boss_phase >= 3 or game_type == 'hard':
            variants.extend(['crossfire', 'snipe'])
        variant = self._choose_attack_variant('aimed', variants)

        speed = BOSS_AIMED_BULLET_SPEED + (self.boss_phase - 1) * 55
        if game_type == 'hard':
            speed *= 1.12

        interval_multiplier = self._spawn_aimed_fireball_variant(variant, speed, game_type)
        interval = BOSS_AIMED_INTERVAL_MS - (self.boss_phase - 1) * 90
        interval = self._attack_interval(interval * interval_multiplier, game_type)
        self.next_aimed_shot_at = current_time + interval

    def _spawn_aimed_fireball_variant(self, variant, speed, game_type):
        cannon_positions = self.boss.cannon_positions()
        target_x, target_y = self.player.rect.center

        if variant == 'single':
            x, y = random.choice(cannon_positions)
            self._spawn_aimed_storm_bullet(x, y, target_x, target_y, speed)
            return 0.92

        if variant == 'double_tap':
            positions = cannon_positions if self.boss_phase > 1 else [random.choice(cannon_positions)]
            for index, (x, y) in enumerate(positions):
                self._spawn_aimed_storm_bullet(x, y, target_x, target_y + index * 18, speed)
            return 1

        if variant == 'fan':
            positions = cannon_positions if self.boss_phase >= 3 or game_type == 'hard' else [random.choice(cannon_positions)]
            offsets = [-12, 0, 12] if self.boss_phase < 3 else [-14, -5, 5, 14]
            for x, y in positions:
                for offset in offsets:
                    self._spawn_aimed_storm_bullet(
                        x,
                        y,
                        target_x,
                        target_y,
                        speed * 0.92,
                        radius=12,
                        color=(255, 199, 79),
                        angle_offset=offset,
                    )
            return 1.35

        if variant == 'pincer':
            for index, (x, y) in enumerate(cannon_positions):
                target_offset = -105 if index == 0 else 105
                self._spawn_aimed_storm_bullet(
                    x,
                    y,
                    target_x,
                    target_y + target_offset,
                    speed * 1.04,
                    radius=13,
                    color=(124, 232, 255),
                )
            if self.boss_phase >= 3:
                x, y = random.choice(cannon_positions)
                self._spawn_aimed_storm_bullet(x, y, target_x, target_y, speed * 0.9, radius=10)
            return 1.16

        if variant == 'crossfire':
            for offset in (-9, 9):
                for x, y in cannon_positions:
                    self._spawn_aimed_storm_bullet(
                        x,
                        y + random.randint(-18, 18),
                        target_x,
                        target_y,
                        speed * 0.96,
                        radius=11,
                        color=(255, 134, 118),
                        angle_offset=offset,
                    )
            return 1.42

        x, y = random.choice(cannon_positions)
        self._spawn_aimed_storm_bullet(
            x,
            y,
            target_x,
            target_y,
            speed * 1.3,
            radius=9,
            color=(255, 241, 140),
        )
        return 0.82

    def _update_spiral_attack(self, current_time, game_type):
        if self.boss_phase < 2:
            return

        if self.pending_spiral_at is not None and current_time >= self.pending_spiral_at:
            self._spawn_spiral_wave(game_type, self.pending_spiral_variant)
            self.pending_spiral_at = None

        if self.pending_spiral_at is None and current_time >= self.next_spiral_at:
            self.boss.start_dash(random.choice([-1, 1]), current_time)
            variants = ['arc', 'wide']
            if self.boss_phase >= 3 or game_type == 'hard':
                variants.extend(['split', 'pinwheel'])
            self.pending_spiral_variant = self._choose_attack_variant('spiral', variants)
            self.pending_spiral_at = current_time + BOSS_DASH_MS
            interval = self._attack_interval(BOSS_SPIRAL_INTERVAL_MS - (self.boss_phase - 2) * 350, game_type)
            self.next_spiral_at = current_time + interval

    def _spawn_spiral_wave(self, game_type, variant='arc'):
        origin_x = self.boss.rect.left + 70
        origin_y = self.boss.rect.centery
        speed = BOSS_SPIRAL_BULLET_SPEED + self.boss_phase * 45
        if game_type == 'hard':
            speed *= 1.1

        origins = [(origin_x, origin_y)]
        angles = list(range(116, 245, 11 if self.boss_phase == 3 else 13))
        safe_width = 16
        color = (255, 184, 76)

        if variant == 'wide':
            angles = list(range(98, 263, 14 if self.boss_phase == 3 else 16))
            speed *= 0.94
            safe_width = 20
            color = (255, 222, 112)
        elif variant == 'split':
            origins = self.boss.cannon_positions()
            angles = list(range(126, 236, 18))
            speed *= 0.96
            safe_width = 18
            color = (120, 226, 255)
        elif variant == 'pinwheel':
            angles = list(range(112, 249, 21))
            speed *= 1.05
            safe_width = 17
            color = (255, 128, 128)

        for current_origin_x, current_origin_y in origins:
            gap_angle = math.degrees(math.atan2(
                self.player.rect.centery - current_origin_y,
                self.player.rect.centerx - current_origin_x,
            ))
            for angle in angles:
                if abs((angle - gap_angle + 180) % 360 - 180) < safe_width:
                    continue
                radians = math.radians(angle)
                velocity = pygame.Vector2(math.cos(radians), math.sin(radians)) * speed
                self._add_boss_attack(StormBullet(
                    current_origin_x,
                    current_origin_y,
                    velocity,
                    radius=11,
                    color=color,
                ))
                if variant == 'pinwheel':
                    mirrored = (360 - angle) % 360
                    if abs((mirrored - gap_angle + 180) % 360 - 180) < safe_width:
                        continue
                    radians = math.radians(mirrored)
                    velocity = pygame.Vector2(math.cos(radians), math.sin(radians)) * (speed * 0.9)
                    self._add_boss_attack(StormBullet(
                        current_origin_x,
                        current_origin_y,
                        velocity,
                        radius=9,
                        color=(255, 222, 112),
                    ))

    def _update_lightning_attack(self, current_time, game_type):
        if self.boss_phase < 3 or current_time < self.next_lightning_at:
            return

        self.boss.start_dash(random.choice([-1, 1]), current_time)
        variant = self._choose_attack_variant('lightning', ['single', 'cage', 'chain'])
        for target_x in self._lightning_targets_for_variant(variant, game_type):
            warning = LightningWarning(target_x, current_time)
            self.lightning_warnings.add(warning)
            self.all_sprites.add(warning)
        interval = self._attack_interval(BOSS_LIGHTNING_INTERVAL_MS, game_type)
        self.next_lightning_at = current_time + interval

    def _lightning_targets_for_variant(self, variant, game_type):
        base_x = self._clamp_lightning_x(self.player.rect.centerx + random.randint(-90, 90))

        if variant == 'cage':
            return [
                self._clamp_lightning_x(base_x - 132),
                self._clamp_lightning_x(base_x + 132),
            ]

        if variant == 'chain':
            direction = random.choice([-1, 1])
            offsets = [0, direction * 155]
            if game_type == 'hard':
                offsets.append(-direction * 155)
            targets = []
            for offset in offsets:
                candidate = self._clamp_lightning_x(base_x + offset)
                if all(abs(candidate - target) > 92 for target in targets):
                    targets.append(candidate)
            return targets

        return [base_x]

    def _update_lightning_warnings(self, current_time):
        for warning in list(self.lightning_warnings):
            if not warning.ready(current_time):
                continue

            beam = LightningBeam(warning.rect.centerx, current_time)
            self.boss_attacks.add(beam)
            self.all_sprites.add(beam)
            warning.kill()
            self._start_screen_shake(SCREEN_SHAKE_LIGHTNING_STRENGTH, SCREEN_SHAKE_LIGHTNING_MS, current_time)
            self._spawn_particles(beam.rect.centerx, SCREEN_HEIGHT // 2, 20, (255, 245, 130), 230)

    def _update_rail_attack(self, current_time, game_type):
        if self.boss_phase < 2 or current_time < self.next_rail_at:
            return

        self.boss.start_dash(random.choice([-1, 1]), current_time)
        variants = ['tracked', 'offset']
        if self.boss_phase == 3 or game_type == 'hard':
            variants.extend(['bracket', 'split'])
        variant = self._choose_attack_variant('rail', variants)
        lanes = self._rail_lanes_for_variant(variant, game_type)

        for lane in lanes:
            warning = RailWarning(self._clamp_rail_y(lane), current_time)
            self.rail_warnings.add(warning)
            self.all_sprites.add(warning)

        interval = BOSS_RAIL_INTERVAL_MS - (self.boss_phase - 2) * 430
        self.next_rail_at = current_time + self._attack_interval(interval, game_type)

    def _rail_lanes_for_variant(self, variant, game_type):
        player_y = self.player.rect.centery

        if variant == 'offset':
            return [player_y + random.choice([-118, 118])]

        if variant == 'bracket':
            return [player_y - 118, player_y + 118]

        if variant == 'split':
            lane_count = 2 + int(game_type == 'hard')
            lanes = [random.randint(82, SCREEN_HEIGHT - 164)]
            attempts = 0
            while len(lanes) < lane_count and attempts < 24:
                attempts += 1
                candidate = random.randint(82, SCREEN_HEIGHT - 164)
                if all(abs(candidate - lane) > 112 for lane in lanes):
                    lanes.append(candidate)
            while len(lanes) < lane_count:
                fallback = 96 + len(lanes) * 176
                lanes.append(self._clamp_rail_y(fallback))
            return lanes

        return [player_y + random.randint(-65, 65)]

    def _update_rail_warnings(self, current_time):
        for warning in list(self.rail_warnings):
            if not warning.ready(current_time):
                continue

            beam = RailBeam(warning.rect.centery, current_time)
            self.boss_attacks.add(beam)
            self.all_sprites.add(beam)
            warning.kill()
            self._start_screen_shake(SCREEN_SHAKE_LIGHTNING_STRENGTH - 2, SCREEN_SHAKE_LIGHTNING_MS, current_time)
            self._spawn_particles(SCREEN_WIDTH // 2, beam.rect.centery, 18, (255, 170, 83), 230)

    def _update_minefield_attack(self, current_time, game_type):
        if self.boss_phase < 2 or current_time < self.next_mine_at:
            return

        variants = ['scatter', 'chase']
        if self.boss_phase == 3 or game_type == 'hard':
            variants.extend(['line', 'triangle'])
        variant = self._choose_attack_variant('minefield', variants)
        self._spawn_minefield_variant(variant, current_time, game_type)

        interval = BOSS_MINE_INTERVAL_MS - (self.boss_phase - 2) * 360
        self.next_mine_at = current_time + self._attack_interval(interval, game_type)

    def _spawn_minefield_variant(self, variant, current_time, game_type):
        hard_mode = game_type == 'hard'
        base_x = self.boss.rect.left

        if variant == 'chase':
            offsets = [0]
            if self.boss_phase == 3 or hard_mode:
                offsets = [-86, 86]
            for index, offset in enumerate(offsets):
                self._spawn_gravity_mine(
                    base_x + 52 + index * 24,
                    self.player.rect.centery + offset,
                    current_time + index * 120,
                    hard_mode,
                )
            return

        if variant == 'line':
            lane_step = (SCREEN_HEIGHT - 210) // 3
            start_y = 88 + random.randint(-22, 22)
            for index in range(3):
                self._spawn_gravity_mine(
                    base_x + random.randint(35, 98),
                    start_y + lane_step * index,
                    current_time + index * 95,
                    hard_mode,
                )
            return

        if variant == 'triangle':
            center_y = self.boss.rect.centery
            for index, (x_offset, y_offset) in enumerate(((36, 0), (92, -112), (92, 112))):
                self._spawn_gravity_mine(
                    base_x + x_offset,
                    center_y + y_offset,
                    current_time + index * 90,
                    hard_mode,
                )
            return

        mine_count = 1 + int(self.boss_phase == 3) + int(hard_mode)
        for index in range(mine_count):
            self._spawn_gravity_mine(
                base_x + random.randint(24, 92),
                self.boss.rect.centery + random.randint(-135, 135),
                current_time + index * 70,
                hard_mode,
            )

    def _spawn_gravity_mine(self, x, y, current_time, hard_mode):
        y = max(70, min(SCREEN_HEIGHT - 150, int(y)))
        self._add_boss_attack(GravityMine(x, y, current_time, hard_mode=hard_mode))

    def _update_homing_attack(self, current_time, game_type):
        if self.boss_phase < 2 or current_time < self.next_homing_at:
            return

        variants = ['paired', 'stagger']
        if self.boss_phase == 3 or game_type == 'hard':
            variants.extend(['flank', 'burst'])
        variant = self._choose_attack_variant('homing', variants)
        self._spawn_homing_variant(variant, game_type)

        interval = BOSS_HOMING_INTERVAL_MS - (self.boss_phase - 2) * 330
        self.next_homing_at = current_time + self._attack_interval(interval, game_type)

    def _spawn_homing_variant(self, variant, game_type):
        hard_mode = game_type == 'hard'
        cannon_positions = self.boss.cannon_positions()

        if variant == 'flank':
            lanes = [85, SCREEN_HEIGHT - 178]
            if hard_mode:
                lanes.append(self.player.rect.centery)
            for index, y in enumerate(lanes):
                x = self.boss.rect.left + 55 + index * 12
                self._add_boss_attack(HomingBolt(x, y, self.player, hard_mode=hard_mode))
            return

        if variant == 'burst':
            offsets = [-78, 0, 78]
            for index, offset in enumerate(offsets):
                x, y = cannon_positions[index % len(cannon_positions)]
                y = max(70, min(SCREEN_HEIGHT - 150, self.player.rect.centery + offset))
                self._add_boss_attack(HomingBolt(x, y, self.player, hard_mode=hard_mode))
            return

        if variant == 'stagger':
            for index, (x, y) in enumerate(cannon_positions):
                y += random.choice([-64, 64]) + index * 18
                self._add_boss_attack(HomingBolt(x, y, self.player, hard_mode=hard_mode))
            return

        spawn_count = 1 + int(self.boss_phase == 3) + int(hard_mode)
        for index in range(spawn_count):
            x, y = cannon_positions[index % len(cannon_positions)]
            y += random.randint(-42, 42)
            self._add_boss_attack(HomingBolt(x, y, self.player, hard_mode=hard_mode))

    def _update_nova_attack(self, current_time, game_type):
        if self.boss_phase < 3 or current_time < self.next_nova_at:
            return

        self.boss.start_dash(random.choice([-1, 1]), current_time)
        variant = self._choose_attack_variant('nova', ['ring', 'spiral', 'star'])
        self._spawn_nova_burst(game_type, variant)
        interval = BOSS_NOVA_INTERVAL_MS
        self.next_nova_at = current_time + self._attack_interval(interval, game_type)

    def _spawn_nova_burst(self, game_type, variant='ring'):
        origin_x = self.boss.rect.left + 90
        origin_y = self.boss.rect.centery
        safe_angle = math.degrees(math.atan2(self.player.rect.centery - origin_y, self.player.rect.centerx - origin_x))
        speed = BOSS_NOVA_BULLET_SPEED + (70 if game_type == 'hard' else 0)

        if variant == 'spiral':
            for ring in range(3 + int(game_type == 'hard')):
                count = 14 + ring * 4
                offset = random.randint(0, 25) + ring * 22
                self._spawn_nova_ring(origin_x, origin_y, count, offset, safe_angle,
                                      speed + ring * 48, 15, (255, 146, 96))
        elif variant == 'star':
            spoke_count = 12 + int(game_type == 'hard') * 2
            for layer in range(2):
                for index in range(spoke_count):
                    angle = 360 / spoke_count * index + layer * 360 / spoke_count / 2
                    if abs((angle - safe_angle + 180) % 360 - 180) < 18:
                        continue
                    radians = math.radians(angle)
                    velocity = pygame.Vector2(math.cos(radians), math.sin(radians)) * (speed + layer * 105)
                    self._add_boss_attack(StormBullet(
                        origin_x,
                        origin_y,
                        velocity,
                        radius=9,
                        color=(255, 230, 116),
                    ))
        else:
            ring_count = 2 + int(game_type == 'hard')
            for ring in range(ring_count):
                count = 18 + ring * 5
                offset = ring * 360 / count / 2
                self._spawn_nova_ring(origin_x, origin_y, count, offset, safe_angle,
                                      speed + ring * 60, 13, (255, 112, 132))

        self._spawn_particles(origin_x, origin_y, 26, (255, 112, 132), 260)

    def _spawn_nova_ring(self, origin_x, origin_y, count, offset, safe_angle, speed, safe_width, color):
        for index in range(count):
            angle = 360 / count * index + offset
            if abs((angle - safe_angle + 180) % 360 - 180) < safe_width:
                continue
            radians = math.radians(angle)
            velocity = pygame.Vector2(math.cos(radians), math.sin(radians)) * speed
            self._add_boss_attack(StormBullet(origin_x, origin_y, velocity, radius=8, color=color))

    def _update_gravity_mines(self, current_time, game_type):
        for mine in list(self.boss_attacks):
            if not isinstance(mine, GravityMine) or not mine.ready_to_burst(current_time):
                continue

            for bullet in mine.burst_bullets(self.boss_phase, hard_mode=game_type == 'hard'):
                self.boss_attacks.add(bullet)
                self.all_sprites.add(bullet)
            self._spawn_particles(mine.rect.centerx, mine.rect.centery, 18, (174, 104, 255), 190)
            mine.kill()

    def _update_drone_minions(self, current_time, game_type):
        if self.boss_phase < 3 or current_time < self.next_minion_at:
            return

        spawn_count = 2 if game_type == 'hard' and len(self.drone_minions) < 3 else 1
        for _ in range(spawn_count):
            y = self.boss.rect.centery + random.randint(-95, 95)
            y = max(70, min(SCREEN_HEIGHT - 150, y))
            minion = DroneMinion(
                self.boss.rect.left + random.randint(30, 100),
                y,
                self.player.rect.centerx,
                self.player.rect.centery,
                hard_mode=game_type == 'hard',
            )
            self.drone_minions.add(minion)
            self.all_sprites.add(minion)

        self.next_minion_at = current_time + self._attack_interval(BOSS_MINION_INTERVAL_MS, game_type)

    def _update_meteor_pressure(self, current_time, game_type):
        if current_time < self.next_meteor_at:
            return

        self.meteor = self._make_space_hazard(game_type)
        self.all_meteors.add(self.meteor)
        self.all_sprites.add(self.meteor)

        interval = BOSS_METEOR_INTERVAL_MS - (self.boss_phase - 1) * 170
        self.next_meteor_at = current_time + self._attack_interval(interval, game_type)

    def _make_space_hazard(self, game_type):
        roll = random.random()
        comet_chance = 0.23 + 0.05 * (self.boss_phase - 1)
        crystal_chance = 0.18 + 0.04 * int(game_type == 'hard')

        if roll < comet_chance:
            return Comet()
        if roll < comet_chance + crystal_chance:
            return SpaceCrystal()
        return Meteor()

    def _attack_interval(self, interval, game_type):
        if game_type == 'hard':
            interval *= BOSS_HARD_INTERVAL_MULTIPLIER
        return max(220, int(interval))

    def _boss_is_defeated(self, game_type):
        return self.boss_hearts <= 0 and game_type != 'infinity'

    def _update_boss_defeat(self, current_time):
        if self.boss_defeated_at is None:
            self.boss_defeated_at = current_time
            self.phase_pause_until = current_time + BOSS_DEFEAT_DELAY_MS
            self._start_screen_shake(SCREEN_SHAKE_PHASE_STRENGTH, SCREEN_SHAKE_PHASE_MS, current_time)

        if current_time >= self.next_defeat_boom_at:
            self._spawn_random_boss_boom()
            self._spawn_particles(
                random.randrange(self.boss.rect.left, self.boss.rect.right),
                random.randrange(self.boss.rect.top, self.boss.rect.bottom),
                9,
                (255, 148, 83),
                210,
            )
            self.next_defeat_boom_at = current_time + 160

    def _boss_defeat_finished(self, current_time, game_type):
        return (
            self.boss_defeated_at is not None
            and game_type != 'infinity'
            and current_time - self.boss_defeated_at >= BOSS_DEFEAT_DELAY_MS
        )

    def _start_screen_shake(self, strength, duration, current_time):
        self.shake_strength = max(self.shake_strength, strength)
        self.shake_until = max(self.shake_until, current_time + duration)

    def _screen_shake_offset(self, current_time):
        if current_time >= self.shake_until:
            self.shake_strength = 0
            return 0, 0

        progress = (self.shake_until - current_time) / max(1, SCREEN_SHAKE_PHASE_MS)
        strength = max(1, int(self.shake_strength * min(1, progress + 0.25)))
        return random.randint(-strength, strength), random.randint(-strength, strength)

    def _spawn_particles(self, x, y, count, color, speed):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(speed * 0.35, speed)
            particle = Particle(x, y, velocity, color, radius=random.randint(2, 5))
            self.all_particles.add(particle)
            self.all_sprites.add(particle)

    def _draw_game_world(self, offset, current_time):
        heart_sprites = set(self.all_hearts.sprites())
        for sprite in self.all_sprites:
            if sprite in heart_sprites:
                continue
            screen.blit(sprite.image, sprite.rect.move(offset))

        self.player.draw_charge_effect(screen, current_time, offset)
        if self.input_state.debug_hitboxes:
            self.player.draw_debug_hitbox(screen, offset)

        for heart in self.all_hearts:
            screen.blit(heart.image, heart.rect)

    def _draw_boss_ui(self, current_time):
        if self.boss_max_hearts <= 0:
            return

        bar_width = 560
        bar_height = 18
        x = SCREEN_WIDTH // 2 - bar_width // 2
        y = 22
        ratio = max(0, min(1, self.boss_hearts / self.boss_max_hearts))
        pygame.draw.rect(screen, (24, 28, 42), (x - 3, y - 3, bar_width + 6, bar_height + 6))
        pygame.draw.rect(screen, (82, 93, 122), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, (234, 83, 83), (x, y, int(bar_width * ratio), bar_height))
        pygame.draw.rect(screen, (245, 230, 146), (x, y, bar_width, bar_height), 2)

        font = pygame.font.Font(None, 28)
        label = self._boss_display_name()
        if self.boss_phase > 1:
            label += '  Phase ' + str(self.boss_phase)
        text = font.render(label, True, (245, 244, 221))
        screen.blit(text, (x, y + 24))

        if self.phase_banner_text and current_time < self.phase_banner_until:
            banner_font = pygame.font.Font(None, 56)
            banner = banner_font.render(self.phase_banner_text, True, (255, 241, 140))
            banner_rect = banner.get_rect(center=(SCREEN_WIDTH // 2, 105))
            screen.blit(banner, banner_rect)

    def _update_slow_motion(self, input_state, real_delta_ms):
        wants_slow_motion = input_state.slow_mode
        self.slow_motion_active = wants_slow_motion and self.slow_motion_energy_ms > 0

        if self.slow_motion_active:
            self.slow_motion_energy_ms = max(0, self.slow_motion_energy_ms - real_delta_ms)
            if self.slow_motion_energy_ms <= 0:
                self.slow_motion_active = False
            return

        if not wants_slow_motion:
            recharge = real_delta_ms * SLOW_MOTION_RECHARGE_MULTIPLIER
            self.slow_motion_energy_ms = min(SLOW_MOTION_MAX_MS, self.slow_motion_energy_ms + recharge)

    def _slow_motion_progress(self):
        return max(0, min(1, self.slow_motion_energy_ms / SLOW_MOTION_MAX_MS))

    def _draw_player_weapon_ui(self, current_time):
        rect = pygame.Rect(SCREEN_WIDTH - 386, SCREEN_HEIGHT - 92, 340, 74)
        self._draw_hud_panel(rect, fill=(3, 9, 18, 92), border=(72, 206, 220, 125), radius=6)
        font = pygame.font.Font(None, 20)

        slow_progress = self._slow_motion_progress()
        slow_color = (96, 226, 238) if self.slow_motion_active else (255, 232, 145)
        if slow_progress <= 0:
            slow_color = (255, 105, 91)
        self._draw_text('Shift', font, (rect.left + 18, rect.top + 9), slow_color)
        slow_bar = pygame.Rect(rect.left + 70, rect.top + 13, 238, 8)
        pygame.draw.rect(screen, (18, 28, 45), slow_bar)
        pygame.draw.rect(screen, slow_color, (slow_bar.left, slow_bar.top, int(slow_bar.width * slow_progress),
                                              slow_bar.height))
        pygame.draw.rect(screen, (80, 164, 200), slow_bar, 1)

        slots = [
            ('Space', '', 1),
            ('Z', 'spread', self.player.cooldown_progress(
                current_time, self.player.next_spread_shot_at, PLAYER_SPREAD_SHOT_COOLDOWN_MS
            )),
            ('X', 'charge', self.player.charge_progress(current_time) if self.player.charge_started_at is not None
             else self.player.cooldown_progress(current_time, self.player.next_charge_available_at,
                                                PLAYER_CHARGE_COOLDOWN_MS)),
            ('C', 'rocket', self.player.cooldown_progress(
                current_time, self.player.next_rocket_available_at, PLAYER_ROCKET_COOLDOWN_MS
            )),
        ]

        slot_width = 72
        for index, (key, label, progress) in enumerate(slots):
            x = rect.left + 18 + index * 78
            pygame.draw.rect(screen, (18, 28, 45), (x, rect.top + 38, slot_width, 9))
            pygame.draw.rect(screen, (255, 232, 145), (x, rect.top + 38, int(slot_width * progress), 9))
            pygame.draw.rect(screen, (80, 164, 200), (x, rect.top + 38, slot_width, 9), 1)
            text_color = (244, 249, 236) if progress >= 1 else (145, 202, 209)
            if self.slow_motion_active:
                text_color = (104, 143, 151)
            text = key if not label else key + ' ' + label
            self._draw_text(text, font, (x, rect.top + 52), text_color)

    def game_life(self, game_type='story'):
        """Run one gameplay session until the player loses or the boss dies."""
        self.hearts, self.boss_hearts = initial_health_for_mode(game_type)
        self.boss_max_hearts = self.boss_hearts
        current_time = pygame.time.get_ticks()
        self.last_real_time_ms = current_time
        self.slow_motion_energy_ms = SLOW_MOTION_MAX_MS
        self.slow_motion_active = False
        set_time_state(1, current_time)
        self._start_boss_fight_timers(current_time, game_type)

        for i in range(self.hearts):
            self.heart = Heart(i)
            self.all_sprites.add(self.heart)
            self.all_hearts.add(self.heart)

        clock = pygame.time.Clock()
        running = True

        timer_background = pygame.USEREVENT + 4
        pygame.time.set_timer(timer_background, 300)

        timer_animation = pygame.USEREVENT + 5
        pygame.time.set_timer(timer_animation, 70)

        timer_heart_animation = pygame.USEREVENT + 6
        pygame.time.set_timer(timer_heart_animation, 200)

        while running:
            screen.fill((0, 0, 0))
            events = pygame.event.get()
            self.input_state.refresh(events)
            current_time = pygame.time.get_ticks()
            real_delta_ms = max(0, min(current_time - self.last_real_time_ms, int(1000 / FPS * 2)))
            self.last_real_time_ms = current_time
            self._update_slow_motion(self.input_state, real_delta_ms)
            time_scale = BULLET_TIME_SCALE if self.slow_motion_active else 1
            set_time_state(time_scale, current_time)

            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False

                if event.type == timer_background:
                    if self.first_background.rect.right <= 0:
                        self.first_background.rect.left = self.third_background.rect.right

                    if self.second_background.rect.right <= 0:
                        self.second_background.rect.left = self.first_background.rect.right

                    if self.third_background.rect.right <= 0:
                        self.third_background.rect.left = self.second_background.rect.right

                    self.all_backgrounds.update()

                if event.type == timer_animation:
                    self.boss.update_animation()
                    self.player.update_animation()

                    for i in self.all_boom:
                        i.update_animation()

                    for i in self.all_boss_damage:
                        i.update_animation()

                    for i in self.player_attacks:
                        i.update_animation()

                if event.type == timer_heart_animation:
                    for i in self.all_hearts:
                        i.update_animation()

            # Gameplay state is updated before rendering the current frame.
            dt = min(clock.get_time() / 1000, 2 / FPS) or 1 / FPS
            self.player.update_controls(self.input_state, dt, current_time, self.boss.rect.left,
                                        self.slow_motion_active)
            can_player_shoot = not self.slow_motion_active and current_time >= self.phase_pause_until
            for shoot in self.player.update_shooting(self.input_state, current_time, can_shoot=can_player_shoot):
                self.player_attacks.add(shoot)
                self.all_sprites.add(shoot)

            self._update_boss_fight(current_time, game_type)
            self._handle_collisions(game_type, current_time)

            shake_offset = self._screen_shake_offset(current_time)
            self._draw_game_world(shake_offset, current_time)

            self.all_sprites.update()

            clamp_player_to_arena(self.player, self.boss)

            clock.tick(FPS)
            self._draw_boss_ui(current_time)
            self._draw_player_weapon_ui(current_time)
            present_screen()

            if self.hearts == 0 and (self.boss_hearts > 0 or game_type == 'infinity'):
                return False

            if self._boss_defeat_finished(current_time, game_type):
                return True

    def _handle_collisions(self, game_type, current_time):
        """Resolve combat collisions separately from rendering."""
        self._handle_boss_projectile_hits(game_type, current_time)
        self._handle_player_projectile_hits(game_type, current_time)
        self._handle_meteor_player_hits(game_type, current_time)
        self._handle_minion_player_hits(current_time)

    def _handle_boss_projectile_hits(self, game_type, current_time):
        if not boss_is_active(self.boss_hearts, game_type):
            return

        for boss_attack in list(self.boss_attacks):
            if (
                self.hearts > 0
                and self.player.can_take_damage(current_time)
                and self.player.collides_with(boss_attack)
            ):
                if not getattr(boss_attack, 'pierces', False):
                    boss_attack.kill()
                self._remove_player_heart(current_time)

    def _handle_player_projectile_hits(self, game_type, current_time):
        for player_attack in list(self.player_attacks):
            for boss_attack in list(self.boss_attacks):
                if not getattr(boss_attack, 'destructible', True):
                    continue
                if boss_attack.alive() and boss_attack.collision_check(player_attack):
                    self._explode_player_attack(player_attack, game_type, current_time)
                    break

            if not player_attack.alive():
                continue

            for minion in list(self.drone_minions):
                if pygame.sprite.collide_mask(player_attack, minion):
                    damage = getattr(player_attack, 'damage', 1)
                    player_attack.kill()
                    if minion.take_damage(damage):
                        self._spawn_minion_explosion(minion)
                    else:
                        self._spawn_particles(minion.rect.centerx, minion.rect.centery, 5, (200, 230, 245), 115)
                    self._explode_player_attack(player_attack, game_type, current_time)
                    break

            if player_attack.alive() and player_attack.collision_check(self.boss):
                self._damage_boss(player_attack, game_type, current_time)
                self._explode_player_attack(player_attack, game_type, current_time, damage_boss=False)
                continue

            for meteor in list(self.all_meteors):
                if player_attack.alive() and player_attack.collision_check(meteor):
                    self._spawn_meteor_boom(meteor)
                    meteor.kill()
                    self._explode_player_attack(player_attack, game_type, current_time)
                    break

    def _explode_player_attack(self, player_attack, game_type, current_time, damage_boss=True):
        splash_radius = getattr(player_attack, 'splash_radius', 0)
        if splash_radius <= 0:
            return

        center = pygame.Vector2(player_attack.rect.center)
        splash_damage = getattr(player_attack, 'splash_damage', 1)
        if player_attack.alive():
            player_attack.kill()

        self._spawn_particles(player_attack.rect.centerx, player_attack.rect.centery, 24, (255, 232, 145), 260)
        self._start_screen_shake(SCREEN_SHAKE_BOSS_HIT_STRENGTH + 1, SCREEN_SHAKE_HIT_MS, current_time)

        for boss_attack in list(self.boss_attacks):
            if not getattr(boss_attack, 'destructible', True) or not boss_attack.alive():
                continue
            if center.distance_to(boss_attack.rect.center) <= splash_radius:
                boss_attack.kill()

        for minion in list(self.drone_minions):
            if center.distance_to(minion.rect.center) <= splash_radius:
                if minion.take_damage(splash_damage):
                    self._spawn_minion_explosion(minion)
                else:
                    self._spawn_particles(minion.rect.centerx, minion.rect.centery, 5, (200, 230, 245), 115)

        for meteor in list(self.all_meteors):
            if center.distance_to(meteor.rect.center) <= splash_radius:
                self._spawn_meteor_boom(meteor)
                meteor.kill()

        if damage_boss and boss_is_active(self.boss_hearts, game_type):
            if center.distance_to(self.boss.rect.center) <= self.boss.rect.width / 2 + splash_radius:
                previous_damage = player_attack.damage
                player_attack.damage = splash_damage
                self._damage_boss(player_attack, game_type, current_time)
                player_attack.damage = previous_damage

    def _handle_meteor_player_hits(self, game_type, current_time):
        if not boss_is_active(self.boss_hearts, game_type):
            return

        for meteor in list(self.all_meteors):
            if (
                self.hearts > 0
                and self.player.can_take_damage(current_time)
                and self.player.collides_with(meteor)
            ):
                meteor.kill()
                self._spawn_particles(self.player.rect.centerx, self.player.rect.centery, 14, (255, 130, 83), 190)
                self._remove_player_heart(current_time)

    def _handle_minion_player_hits(self, current_time):
        for minion in list(self.drone_minions):
            if self.hearts > 0 and self.player.can_take_damage(current_time) and self.player.collides_with(minion):
                self._spawn_minion_explosion(minion)
                minion.kill()
                self._remove_player_heart(current_time)

    def _remove_player_heart(self, current_time):
        if self.hearts <= 0:
            return

        self.hearts -= 1
        hearts = self.all_hearts.sprites()
        if hearts:
            self.heart = hearts[-1]
            self.heart.kill()
        self.player.start_invincibility(current_time)
        self._start_screen_shake(SCREEN_SHAKE_PLAYER_HIT_STRENGTH, SCREEN_SHAKE_HIT_MS, current_time)
        self._spawn_particles(self.player.rect.centerx, self.player.rect.centery, 16, (255, 102, 80), 220)

    def _damage_boss(self, player_attack, game_type, current_time):
        previous_hearts = self.boss_hearts
        self.boss_hearts -= getattr(player_attack, 'damage', 1)
        if hasattr(self.boss, 'take_hit'):
            self.boss.take_hit(current_time)
        self._start_screen_shake(SCREEN_SHAKE_BOSS_HIT_STRENGTH, SCREEN_SHAKE_HIT_MS, current_time)
        self._spawn_particles(player_attack.rect.centerx, player_attack.rect.centery, 8, (255, 221, 118), 150)

        crossed_damage_step = previous_hearts // 100 != self.boss_hearts // 100
        if crossed_damage_step and game_type != 'infinity':
            self._spawn_boss_damage(player_attack)
        self._update_boss_phase(current_time)

    def _spawn_minion_explosion(self, minion):
        self._spawn_particles(minion.rect.centerx, minion.rect.centery, 18, (218, 238, 247), 210)
        self.meteor_boom = MeteorBoom(*minion.rect.center)
        self.all_boom.add(self.meteor_boom)
        self.all_sprites.add(self.meteor_boom)

    def _spawn_boss_damage(self, player_attack):
        self.boom = Boom(*player_attack.rect.center)
        self.all_boom.add(self.boom)
        self.all_sprites.add(self.boom)

        damage_index = len(self.all_boss_damage) + 1
        if damage_index <= 5:
            self.fire = Fire(self.boss, damage_index)
            self.all_boss_damage.add(self.fire)
            self.all_sprites.add(self.fire)

    def _spawn_meteor_boom(self, meteor):
        self.meteor_boom = MeteorBoom(*meteor.rect.center)
        self.all_boom.add(self.meteor_boom)
        self.all_sprites.add(self.meteor_boom)

    def _spawn_random_boss_boom(self):
        x = random.randrange(self.boss.rect.left, self.boss.rect.right)
        y = random.randrange(self.boss.rect.top, self.boss.rect.bottom)

        boom = Boom(x, y)
        self.all_sprites.add(boom)
        self.all_boom.add(boom)
