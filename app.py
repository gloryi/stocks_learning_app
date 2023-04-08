import config
import sys
import os
import datetime

SCREEN_X_0 = 3400
SCREEN_Y_0 = 0
slow_rnner_flag = False
if len(sys.argv) > 1:
    slow_rnner_flag = int(sys.argv[1])
    config.__dict__["W"] = 1920
    config.__dict__["H"] = 1080
    config.__dict__["VISUAL_PART"] = 140
    SCREEN_Y_0 = 1440

from rendering_backend import backend_switch

backend = backend_switch().get_backend_ref()

from time_utils import global_timer, Counter, Progression

from feature_chain_mode import ChainedProcessor

from config import (
    STOCKS_DATA,
    W,
    H,
    BPM,
    CYRILLIC_FONT,
    HAPTIC_FEEDBACK,
)
from config import REPORTS_FILE
from config import TEST
import subprocess

from colors import white
import colors
from text_morfer import textMorfer

import time
import random
import pyautogui

from ui_elements import UpperLayout


backend.api().init()
display_surface = backend.api().display.set_mode((W, H))
backend.api().display.set_caption("STOCKS_TRAINER_067")
trans_surface = backend.api().Surface((W, H))
trans_surface.set_alpha(100)
trans_surface.fill((40, 0, 40))
trans_surface2 = backend.api().Surface((W, H))
trans_surface2.set_alpha(50)
trans_surface2.fill((40, 0, 40))

time_to_cross_screen = 16000
time_to_appear = 4000
beat_time = 0

pause_progression = []
pause_screenshots = []

active_count = 0
error_count = 0
max_fallback = 0
fallback = 0
streak = 0
max_streak = 0
active_balance = 100

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

skip_next = False

delta_timer = global_timer()

upper_stats = UpperLayout(display_surface)

new_line_counter = Counter(upper_stats)
if TEST:
    pause_counter = Counter(bpm=1/2)
else:
    pause_counter = Counter(bpm=1 / 3)

screenshot_timer = Counter(bpm=1)
quadra_timer = Counter(bpm=10)
morfer_timer = Counter(bpm=15)
timer_1m = Counter(bpm=1)
haptic_timer = Counter(bpm=60)
timer_dropped = False

tokens_1m = []
tokens_key = backend.api().K_k

game = ChainedProcessor(
    display_surface, upper_stats, "hanzi chineese", STOCKS_DATA, (60 * 1000) / BPM
)

progression = Progression(new_line_counter, upper_stats)

beat_time = new_line_counter.drop_time

font = backend.api().font.Font(CYRILLIC_FONT, 60)
backend.api().event.set_allowed(
    [backend.api().QUIT, backend.api().KEYDOWN, backend.api().KEYUP]
)
backend.api().mouse.set_visible(False)
fpsClock = backend.api().time.Clock()

morfer = textMorfer()

mode = "STOCKS"
active_game = game
active_stats = upper_stats
meta = ""
meta_minor = []

# base_font = backend.api().font.match_font("setofont")
# base_font = backend.api().font.Font(base_font, 35)
# minor_font = backend.api().font.match_font("setofont")
# minor_font = backend.api().font.Font(minor_font, 30)
CYRILLIC_FONT = os.path.join(os.getcwd(), "fonts", "NotoSans-SemiBold.ttf")
base_font = backend.api().font.Font(CYRILLIC_FONT, 35)
minor_font = backend.api().font.Font(CYRILLIC_FONT, 25)

upper_stats.active_balance = 100


def place_text(
    text,
    x,
    y,
    transparent=False,
    renderer=None,
    base_col=(80, 80, 80),
    forbid_morf=False,
):
    if renderer is None:
        renderer = base_font
    if not forbid_morf:
        text = morfer.morf_text(text)
    if not transparent:
        text = renderer.render(text, True, base_col, (150, 150, 151))
    else:
        text = renderer.render(text, True, base_col)
    textRect = text.get_rect()
    textRect.center = (x, y)
    display_surface.blit(text, textRect)


def screenshot_to_image(pil_image):
    size = pil_image.size
    mode = pil_image.mode
    data = pil_image.tobytes()
    py_image = backend.api().image.fromstring(data, size, mode)
    py_image = py_image.convert()
    image_scaled = backend.api().transform.scale(py_image, (W // 3, H // 2))
    return image_scaled
    
def inter_simple(v1, v2, p):
    return v1 + (v2 - v1) * p


def dump_report():
    with open(REPORTS_FILE, "a") as reportfile:
        total = sum(int(_[:-1]) for _ in pause_progression) - 100 * len(
            pause_progression
        )
        num_errors = sum([1 for _ in pause_progression if int(_[:-1]) <= 100])
        mark = (
            "S"
            if num_errors == 0
            else "A"
            if num_errors == 1
            else "B"
            if num_errors == 2
            else "C"
            if num_errors == 3
            else "D"
            if num_errors == 4
            else "E"
        )
        current_progress = pause_progression + [
            "_" for _ in range(5 - len(pause_progression))
        ]
        now = datetime.datetime.now()
        timestamp = f"{now.day}.{now.month} {now.hour}:{now.minute}"
        report_line = (
            timestamp
            + " "
            + " ".join(current_progress)
            + "|"
            + f" {total}$"
            + f" | {max_streak-max_fallback} | {mark}"
        )
        if TEST:
            report_line = "TEST " + report_line
        reportfile.write(report_line + "\n")


for time_delta in delta_timer:

    if skip_next:
        skip_next = False
        continue

    fpsClock.tick(35)

    if morfer_timer.is_tick(time_delta):
        morfer.update_seed()

    if slow_rnner_flag and not paused:
        keys = backend.api().key.get_pressed()
        if not keys[backend.api().K_BACKSPACE]:
            time_delta = 0

    display_surface.fill(white)

    if paused:

        timer_expired = timer_1m.is_tick(time_delta)

        if timer_expired and not timer_dropped:
            timer_dropped = True

        if timer_dropped:
            if haptic_timer.is_tick(time_delta):
                if HAPTIC_FEEDBACK:
                    HAPTIC_FEEDBACK(higher_freq  = 40000, duration=500)

        display_surface.fill(white)
        for i, active_screenshot in enumerate(pause_screenshots):
            I = (i - i % 3) // 2
            J = i % 3
            display_surface.blit(active_screenshot, ((W // 3) * J, (H // 2) * I))

        if quadra_timer.is_tick(time_delta):
            if quadra_phase == "INHALE":
                quadra_phase = "HOLD_IN"
                quadra_col_1 = colors.col_bt_pressed
                quadra_col_2 = colors.red2
                if pause_screenshots:
                    pause_screenshots.append(pause_screenshots.pop(0))
            elif quadra_phase == "HOLD_IN":
                quadra_phase = "EXHALE"
                quadra_col_1 = colors.red2
                quadra_col_2 = colors.option_fg
            elif quadra_phase == "EXHALE":
                quadra_phase = "HOLD_OUT"
                quadra_col_1 = colors.option_fg
                quadra_col_2 = colors.feature_bg
                if pause_screenshots:
                    pause_screenshots.append(pause_screenshots.pop(0))
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

        if not timer_dropped:
            if haptic_timer.is_tick(time_delta):
                if HAPTIC_FEEDBACK:
                    inter_freq = int(inter_simple(0, 65000, quadra_w_perce1))
                    HAPTIC_FEEDBACK(higher_freq  = inter_freq)

        if not timer_dropped:
            backend.api().draw.rect(
                display_surface,
                interpolate(quadra_col_1, quadra_col_2, timer_1m.get_percent() ** 2),
                (
                    (W // 2 - ((W // 2) * (1 - timer_1m.get_percent()))),
                    H // 2 - 40,
                    ((W) * (1 - timer_1m.get_percent())),
                    80,
                ),
            )

        backend.api().draw.circle(
            trans_surface,
            interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent()),
            (W // 2, H // 2),
            (H // 2 - 100) * quadra_w_perce1 + 100,
        )
        backend.api().draw.circle(
            trans_surface,
            interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent() ** 2),
            (W // 2, H // 2),
            (H // 2 - 50) * quadra_w_perce2 + 50,
            width=3,
        )

        display_surface.blit(trans_surface, (0, 0))
        display_surface.blit(trans_surface2, (0, 0))

        tokens_repr = " ".join(
            str(i + 1) + random.choice("♡♥") for i, _ in enumerate(tokens_1m)
        )
        place_text(
            tokens_repr,
            W // 2,
            H // 32,
            transparent=True,
            renderer=font,
            base_col=interpolate(
                quadra_col_1, quadra_col_2, 1 - quadra_timer.get_percent()
            ),
        )

        if pause_progression:
            total = sum(int(_[:-1]) for _ in pause_progression) - 100 * len(
                pause_progression
            )
            num_errors = sum([1 for _ in pause_progression if int(_[:-1]) <= 100])
            mark = (
                "S"
                if num_errors == 0
                else "A"
                if num_errors == 1
                else "B"
                if num_errors == 2
                else "C"
                if num_errors == 3
                else "D"
                if num_errors == 4
                else "E"
            )
            if total >= 0:
                color = interpolate(
                    colors.dark_green, colors.feature_bg, quadra_w_perce2
                )
            else:
                color = interpolate(colors.dark_red, colors.red2, quadra_w_perce2)
            color = colors.dark_green if total >= 0 else colors.col_error
            current_progress = pause_progression + [
                "_" for _ in range(5 - len(pause_progression))
            ]
            place_text(
                " ".join(current_progress)
                + "|"
                + f" {total}$"
                + f" | {max_streak-max_fallback} | {mark}",
                W // 2,
                H // 2,
                transparent=True,
                renderer=font,
                base_col=color,
                forbid_morf=True,
            )

        if meta:
            chunks = ["read if time left"] + [
                meta[i : i + 70] for i in range(0, len(meta), 70)
            ]
            for i, chunk in enumerate(chunks):
                place_text(
                    chunk,
                    W // 2,
                    H // 2 + 70 + 45 * (i + 1),
                    transparent=True,
                    renderer=None,
                    base_col=interpolate(
                        colors.col_active_lighter,
                        colors.feature_text_col,
                        quadra_w_perce1,
                    ),
                )
        if meta_minor:
            back_v_found = False
            back_t_found = False

            for i, line in enumerate(meta_minor):
                if "*** IBACKV ***" in line:
                    upper_stats.back_v = line
                    back_v_found = True

                if "*** 1XTEXT ***" in line:
                    back_t_found = True

                if not back_t_found and not "#" in line:
                    continue

                place_text(
                    line,
                    W // 2,
                    H // 2 - 500 + 30 * (i + 1),
                    transparent=True,
                    renderer=minor_font,
                    base_col=interpolate(
                        colors.col_active_lighter,
                        colors.feature_text_col,
                        quadra_w_perce1,
                    ),
                )
            if not back_v_found:
                upper_stats.back_v = ""

    if paused:
        backend.api().display.update()
        keys = backend.api().key.get_pressed()

        if keys[backend.api().K_LSHIFT] or keys[backend.api().K_RSHIFT]:
            paused = False

            if len(pause_progression) >= 5:

                pause_progression = []
                active_count = 0
                max_fallback = 0
                fallback = 0
                error_count = 0
                streak = 0
                max_streak = 0

        if keys[tokens_key] and not timer_dropped:
            if tokens_key == backend.api().K_k:
                tokens_key = backend.api().K_d
            else:
                tokens_key = backend.api().K_k
            tokens_1m.append("*")
            if len(tokens_1m) > 10:
                tokens_1m = []

        for event in backend.api().event.get():
            if event.type == backend.api().QUIT:
                backend.api().quit()

                quit()
        continue

    # MINOR QUADRA
    if quadra_timer.is_tick(time_delta):
        if quadra_phase == "INHALE":
            quadra_phase = "HOLD_IN"
        elif quadra_phase == "HOLD_IN":
            quadra_phase = "EXHALE"
        elif quadra_phase == "EXHALE":
            quadra_phase = "HOLD_OUT"
        else:
            quadra_phase = "INHALE"

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

    upper_stats.quadra_w_perce1 = quadra_w_perce1
    upper_stats.quadra_w_perce2 = quadra_w_perce2
    if haptic_timer.is_tick(time_delta):
        if HAPTIC_FEEDBACK:
            inter_freq = int(inter_simple(0, 65000, quadra_w_perce1))
            HAPTIC_FEEDBACK(higher_freq  = inter_freq)

    if pause_counter.is_tick(time_delta):
        pause_progression.append(f"{active_balance}$")

        if len(pause_progression) == 5:
            dump_report()
            backend.api().quit()
            quit()

        active_balance = 100
        upper_stats.active_balance = active_balance
        paused = True
        timer_1m.drop_elapsed()
        tokens_1m = []
        timer_dropped = False

    if new_line_counter.is_tick(time_delta):
        pyautogui.moveTo(
            SCREEN_X_0 // 2 + W // 64,
            SCREEN_Y_0 + random.randint(H // 2 - H // 3, H // 2 + H // 3),
        )
        next_tick_time, meta, meta_minor = active_game.add_line()
        new_line_counter.modify_bpm(next_tick_time)

    if screenshot_timer.is_tick(time_delta):
        if not paused:

            if len(pause_screenshots) < 15:
                pause_screenshots.append(
                    screenshot_to_image(
                        pyautogui.screenshot(
                            region=((SCREEN_X_0 - W) // 2, SCREEN_Y_0, W, H)
                        )
                    )
                )
            else:
                del pause_screenshots[0]
                pause_screenshots.append(
                    screenshot_to_image(
                        pyautogui.screenshot(
                            region=((SCREEN_X_0 - W) // 2, SCREEN_Y_0, W, H)
                        )
                    )
                )

            skip_next = True

    active_stats.redraw()
    feedback = active_game.tick(beat_time, time_delta)

    if feedback > 0:
        active_count += 3
        active_balance += 0.25 * active_balance * 3
        active_balance = int(active_balance)
        upper_stats.active_balance = active_balance

        fallback = 0

        streak += 1
        max_streak = max(streak, max_streak)

    elif feedback < 0:
        active_count -= 1
        active_balance -= 0.25 * active_balance
        active_balance = int(active_balance)
        upper_stats.active_balance = active_balance
        error_count += 1

        fallback += 1
        max_fallback = max(max_fallback, fallback)

        streak = 0

    resume_game = progression.register_event(feedback)

    if not resume_game:
        pause_counter.drop_elapsed()
        paused = True
        timer_1m.drop_elapsed()
        tokens_1m = []
        timer_dropped = False

    beat_time = progression.synchronize_tick()

    backend.api().display.update()

    keys = backend.api().key.get_pressed()
    if keys[backend.api().K_TAB]:
        paused = True
        timer_1m.drop_elapsed()
        tokens_1m = []
        timer_dropped = False

    for event in backend.api().event.get():

        if event.type == backend.api().QUIT:
            backend.api().quit()

            quit()
backend.api().quit()
