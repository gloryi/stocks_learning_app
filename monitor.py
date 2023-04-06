import pygame
from time_utils import global_timer, Counter, Progression

from feature_chain_mode import ChainedProcessor

from config import STOCKS_DATA, W, H, BPM, CYRILLIC_FONT, MONITORING_LIST
from utils import raw_extracter

from colors import white
import colors
import time
import random
import pyautogui

from ui_elements import UpperLayout

work_assets = [_[0] for _ in raw_extracter(MONITORING_LIST)]
work_index = 0

pygame.init()
display_surface = pygame.display.set_mode((W, H))
pygame.display.set_caption("STOCKS_TRAINER_067")
trans_surface = pygame.Surface((W, H))
trans_surface.set_alpha(100)
trans_surface.fill((40, 0, 40))
trans_surface2 = pygame.Surface((W, H))
trans_surface2.set_alpha(50)
trans_surface2.fill((40, 0, 40))

beat_time = 0

paused = True
quadra_r = 0
quadra_phase = "INHALE"
clip_color = lambda _: 0 if _ <= 0 else 255 if _ >= 255 else int(_)
inter_color = lambda v1, v2, p: clip_color(v1 + (v2 - v1) * p)
interpolate = lambda col1, col2, percent: (
    inter_color(col1[0], col2[0], percent),
    inter_color(col1[1], col2[1], percent),
    inter_color(col1[2], col2[2], percent),
)
quadra_col_1 = colors.feature_bg
quadra_col_2 = colors.col_bt_pressed

delta_timer = global_timer(pygame)

pause_counter = Counter(bpm=1 / 3)
quadra_timer = Counter(bpm=12)


font = pygame.font.Font(CYRILLIC_FONT, 60, bold=True)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
pygame.mouse.set_visible(False)

backward_key = pygame.K_f
forward_key = pygame.K_j

fpsClock = pygame.time.Clock()

base_font = pygame.font.match_font("setofont")
base_font = pygame.font.Font(base_font, 35)
minor_font = pygame.font.match_font("setofont")
minor_font = pygame.font.Font(minor_font, 30)


def place_text(text, x, y, transparent=False, renderer=None, base_col=(80, 80, 80)):
    if renderer is None:
        renderer = base_font
    if not transparent:
        text = renderer.render(text, True, base_col, (150, 150, 151))
    else:
        text = renderer.render(text, True, base_col)
    textRect = text.get_rect()
    textRect.center = (x, y)
    display_surface.blit(text, textRect)


for time_delta in delta_timer:

    fpsClock.tick(30)
    display_surface.fill(white)

    if paused:

        display_surface.fill(white)

        if quadra_timer.is_tick(time_delta):
            if quadra_phase == "INHALE":
                quadra_phase = "HOLD_IN"
                quadra_col_1 = colors.col_bt_pressed
                quadra_col_2 = colors.red2
            elif quadra_phase == "HOLD_IN":
                quadra_phase = "EXHALE"
                quadra_col_1 = colors.red2
                quadra_col_2 = colors.option_fg
            elif quadra_phase == "EXHALE":
                quadra_phase = "HOLD_OUT"
                quadra_col_1 = colors.option_fg
                quadra_col_2 = colors.feature_bg
            else:
                quadra_phase = "INHALE"
                quadra_col_1 = colors.feature_bg
                quadra_col_2 = colors.col_bt_pressed

        if quadra_phase == "INHALE":
            quadra_w_perce1 = quadra_timer.get_percent()
            quadra_w_perce2 = 1.0
        elif quadra_phase == "HOLD_IN":
            quadra_w_perce1 = 1.0
            quadra_w_perce2 = 1 - quadra_timer.get_percent()
        elif quadra_phase == "EXHALE":
            quadra_w_perce1 = 1 - quadra_timer.get_percent()
            quadra_w_perce2 = 0.0
        else:
            quadra_w_perce1 = 0.0
            quadra_w_perce2 = quadra_timer.get_percent()

        trans_surface.fill((40, 0, 40))
        trans_surface2.fill((40, 0, 40))
        pygame.draw.circle(
            trans_surface,
            interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent()),
            (W // 2, H // 2),
            (H // 2 - 100) * quadra_w_perce1 + 100,
        )
        pygame.draw.circle(
            trans_surface,
            interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent() ** 2),
            (W // 2, H // 2),
            (H // 2 - 50) * quadra_w_perce2 + 50,
            width=3,
        )

        display_surface.blit(trans_surface, (0, 0))
        display_surface.blit(trans_surface2, (0, 0))

        place_text(
            str(work_index),
            W // 2,
            H // 2,
            transparent=True,
            renderer=font,
            base_col=interpolate(
                colors.col_active_lighter, colors.feature_text_col, quadra_w_perce1
            ),
        )

        work_assets_rows = 2
        work_assets_cols = 2

        for i, asset in enumerate(work_assets[work_index : work_index + 4]):
            I = (i - i % work_assets_cols) // work_assets_rows
            J = i % work_assets_cols
            place_text(
                asset,
                W // work_assets_cols * J + W // work_assets_cols * 0.5,
                H // work_assets_rows * I + H // work_assets_rows * 0.5,
                transparent=True,
                renderer=font,
                base_col=interpolate(
                    colors.col_active_lighter, colors.feature_text_col, quadra_w_perce1
                ),
            )

    if paused:
        pygame.display.update()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            paused = False

        if keys[backward_key]:
            work_index -= 4
            if work_index < 0:
                work_index = 0
            if backward_key == pygame.K_f:
                backward_key = pygame.K_d
            else:
                backward_key = pygame.K_f
        if keys[forward_key]:
            work_index += 4
            if work_index + 4 >= len(work_assets):
                work_index = len(work_assets) - 4
            if forward_key == pygame.K_j:
                forward_key = pygame.K_k
            else:
                forward_key = pygame.K_j

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

                quit()
        continue

    if pause_counter.is_tick(time_delta):
        paused = True

    pygame.display.update()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_v]:
        paused = True

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()

            quit()
pygame.quit()
