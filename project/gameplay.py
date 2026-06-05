from constants import BOSS_HEARTS, PLAYER_HEARTS, SCREEN_HEIGHT


HARD_PLAYER_HEARTS = 3
HARD_BOSS_HEART_BONUS = 300


def initial_health_for_mode(game_type):
    """Return the player and boss health values for the selected mode."""
    if game_type == 'hard':
        return HARD_PLAYER_HEARTS, BOSS_HEARTS + HARD_BOSS_HEART_BONUS
    return PLAYER_HEARTS, BOSS_HEARTS


def boss_is_active(boss_hearts, game_type):
    """Infinity mode keeps the boss dangerous even after normal health is gone."""
    return boss_hearts > 0 or game_type == 'infinity'


def score_from_boss_health(boss_hearts, game_type):
    """Preserve the original score math, including hard mode's 150% ceiling."""
    if game_type == 'hard':
        score = (BOSS_HEARTS + HARD_BOSS_HEART_BONUS - boss_hearts) / BOSS_HEARTS * 100
    else:
        score = (BOSS_HEARTS - boss_hearts) / BOSS_HEARTS * 100
    return round(score, 2)


def clamp_player_to_arena(player, boss):
    """Keep the player inside the visible play area and away from the boss."""
    if hasattr(player, 'clamp_to_arena'):
        player.clamp_to_arena(boss.rect.left)
        return

    if player.rect.bottom > SCREEN_HEIGHT - 100:
        player.rect.bottom = SCREEN_HEIGHT - 100
    if player.rect.right > boss.rect.left:
        player.rect.right = boss.rect.left
    if player.rect.top < 0:
        player.rect.top = 0
    if player.rect.left < 0:
        player.rect.left = 0
