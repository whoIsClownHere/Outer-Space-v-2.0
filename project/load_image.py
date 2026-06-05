import os
import pygame
from constants import *

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'Data')
BEST_SCORE_PATH = os.path.join(PROJECT_DIR, 'best_score.txt')


def create_game_window():
    try:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except pygame.error:
        return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


window = create_game_window()
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
pygame.display.set_caption(SCREEN_TITLE)


def _scaled_viewport():
    window_width, window_height = window.get_size()
    scale = min(window_width / SCREEN_WIDTH, window_height / SCREEN_HEIGHT)
    scaled_width = max(1, int(SCREEN_WIDTH * scale))
    scaled_height = max(1, int(SCREEN_HEIGHT * scale))
    x = (window_width - scaled_width) // 2
    y = (window_height - scaled_height) // 2
    return pygame.Rect(x, y, scaled_width, scaled_height), scale


def present_screen():
    viewport, _ = _scaled_viewport()
    window.fill((0, 0, 0))
    scaled_screen = pygame.transform.scale(screen, viewport.size)
    window.blit(scaled_screen, viewport.topleft)
    pygame.display.flip()


def screen_to_game_pos(position):
    viewport, scale = _scaled_viewport()
    if not viewport.collidepoint(position):
        return None

    x = int((position[0] - viewport.left) / scale)
    y = int((position[1] - viewport.top) / scale)
    return x, y


def get_game_mouse_pos():
    position = screen_to_game_pos(pygame.mouse.get_pos())
    if position is None:
        return -1, -1
    return position


def asset_path(name):
    return os.path.join(DATA_DIR, name)


def load_image(name, color_key=None):
    fullname = asset_path(name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image
