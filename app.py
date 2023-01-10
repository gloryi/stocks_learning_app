import pygame
from time_utils import global_timer, Counter, Progression

from feature_chain_mode import ChainedProcessor

from config import STOCKS_DATA, W, H, BPM, CYRILLIC_FONT

from colors import white
import colors
import time
import random
import pyautogui

from ui_elements import UpperLayout
 
pygame.init()
display_surface = pygame.display.set_mode((W, H))
pygame.display.set_caption('STOCKS_TRAINER_067')
trans_surface = pygame.Surface((W, H))
trans_surface.set_alpha(100)
trans_surface.fill((40,0,40))
trans_surface2 = pygame.Surface((W, H))
trans_surface2.set_alpha(50)
trans_surface2.fill((40,0,40))

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
clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)
inter_color = lambda v1, v2, p: clip_color(v1 + (v2-v1)*p)
interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                           inter_color(col1[1], col2[1], percent),
                                           inter_color(col1[2], col2[2], percent))
quadra_col_1 = colors.feature_bg
quadra_col_2 = colors.col_bt_pressed 

skip_next = False

delta_timer = global_timer(pygame)

upper_stats = UpperLayout(pygame, display_surface)

new_line_counter = Counter(upper_stats)
pause_counter = Counter(bpm = 1/3)
screenshot_timer = Counter(bpm = 1)
quadra_timer = Counter(bpm = 20)

game = ChainedProcessor(pygame, display_surface, upper_stats, "hanzi chineese", STOCKS_DATA,
                        (60*1000)/BPM)


progression = Progression(new_line_counter,
                          upper_stats)

beat_time = new_line_counter.drop_time 

font = pygame.font.Font(CYRILLIC_FONT, 80, bold = True)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
pygame.mouse.set_visible(False)
fpsClock = pygame.time.Clock()

mode = "STOCKS"
active_game = game
active_stats = upper_stats
meta = ""
meta_minor = []

base_font = pygame.font.match_font("setofont")
base_font = pygame.font.Font(base_font, 35)
minor_font = pygame.font.match_font("setofont")
minor_font = pygame.font.Font(minor_font, 30)

upper_stats.active_balance = 100
    
def place_text(text, x, y, transparent = False, renderer = None, base_col = (80,80,80)):
    if renderer is None:
        renderer = base_font 
    if not transparent:
        text = renderer.render(text, True, base_col, (150,150,151))
    else:
        text = renderer.render(text, True, base_col)
    textRect = text.get_rect()
    textRect.center = (x, y)
    display_surface.blit(text, textRect)

def screenshot_to_image(pil_image):
    size = pil_image.size
    mode = pil_image.mode
    data = pil_image.tobytes()
    py_image =  pygame.image.fromstring(data, size, mode)
    py_image =  py_image.convert()
    image_scaled = pygame.transform.scale(py_image, (W//2, H//2)) 
    return image_scaled

 
for time_delta in delta_timer:

    if skip_next:
        skip_next = False
        continue

    fpsClock.tick(30)
    display_surface.fill(white)

    if paused:

        display_surface.fill(white)
        for i, active_screenshot in enumerate(pause_screenshots):
            I = (i - i%2)//2
            J = i%2
            display_surface.blit(active_screenshot, ((W//2)*J,(H//2)*I))

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

        trans_surface.fill((40,0,40))
        trans_surface2.fill((40,0,40))
        pygame.draw.circle(trans_surface,
                              interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent()),
                              (W//2, H//2),
                               (H//2-100)*quadra_w_perce1+100)
        pygame.draw.circle(trans_surface,
                              interpolate(quadra_col_1, quadra_col_2, quadra_timer.get_percent()**2),
                              (W//2, H//2),
                               (H//2-50)*quadra_w_perce2+50, width = 3)
            


        display_surface.blit(trans_surface, (0,0))
        display_surface.blit(trans_surface2, (0,0))

        if pause_progression:
            total = sum(int(_[:-1]) for _ in pause_progression) - 100*len(pause_progression)
            num_errors = sum([1 for _ in pause_progression if int(_[:-1]) <= 100])
            mark = "S" if num_errors == 0 else "A" if num_errors == 1 else "B" if num_errors == 2 else "C" if num_errors == 3 else "D" if num_errors == 4 else "E"
            color = colors.dark_green if total >= 0 else colors.col_error
            current_progress = pause_progression + ["_" for _ in range(5-len(pause_progression))]
            place_text(" ".join(current_progress) + "|" + f" {total}$" + f" \\ {max_fallback} / {max_streak} | {mark}",
                        W//2,
                        H//2,
                        transparent = True,
                        renderer = font,
                        base_col = color)
            

        if meta:
            chunks = [meta[i:i+70] for i in range(0, len(meta), 70)]
            for i, chunk in enumerate(chunks):
                place_text(chunk,
                            W//2,
                            H//2+70 + 30*(i+1),
                            transparent = True,
                            renderer = None,
                            base_col = (colors.col_bt_pressed))
        if meta_minor:
            for i, line in enumerate(meta_minor):
                place_text(line,
                            W//2,
                            H//2-500 + 30*(i+1),
                            transparent = True,
                            renderer = minor_font,
                            base_col = (colors.col_bt_pressed))

    if paused:
        pygame.display.update()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            paused = False


            if len(pause_progression) >=5:
                pause_progression = []
                active_count = 0
                max_fallback = 0
                fallback = 0
                error_count = 0
                streak = 0
                max_streak = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
 
                quit()
        continue


    if pause_counter.is_tick(time_delta):
        pause_progression.append(f"{active_balance}$")
        active_balance = 100
        upper_stats.active_balance = active_balance
        paused = True


    if new_line_counter.is_tick(time_delta):
        pyautogui.moveTo(W//3*2, H//2)
        next_tick_time, meta, meta_minor = active_game.add_line()
        new_line_counter.modify_bpm(next_tick_time)

    if screenshot_timer.is_tick(time_delta):
        if not paused:

            if len(pause_screenshots) < 9:
                pause_screenshots.append(screenshot_to_image(pyautogui.screenshot(region=(0, 0, W, H))))
            else:
                del pause_screenshots[0]
                pause_screenshots.append(screenshot_to_image(pyautogui.screenshot(region=(0, 0, W, H))))


            skip_next = True


    active_stats.redraw()
    feedback = active_game.tick(beat_time, time_delta)

    if feedback > 0:
        active_count += 3
        active_balance += 0.25*active_balance*3
        active_balance = int(active_balance)
        upper_stats.active_balance = active_balance

        fallback = 0

        streak += 1
        max_streak = max(streak, max_streak)

    elif feedback <0:
        active_count -= 1
        active_balance -= 0.25*active_balance
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

    beat_time = progression.synchronize_tick()


    pygame.display.update()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_v]:
        paused = True
 
    for event in pygame.event.get():
 
        if event.type == pygame.QUIT:
            pygame.quit()
 
            quit()
pygame.quit() 
