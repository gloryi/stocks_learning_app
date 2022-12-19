import pygame
from time_utils import global_timer, Counter, Progression

#from six_words_mode import SixtletsProcessor
from feature_chain_mode import ChainedProcessor
#from feature_chain_mode_semantic import ChainedProcessor as ChainedProcessorS

from config import STOCKS_DATA, W, H, BPM, CYRILLIC_FONT
#from config_semantic import TEST_LANG_DATA

from colors import white
import colors
import time
import random

from ui_elements import UpperLayout
#from ui_elements_semantic import UpperLayout as UpperLayoutS
 
pygame.init()
display_surface = pygame.display.set_mode((W, H))

time_to_cross_screen = 16000
time_to_appear = 4000
beat_time = 0 
paused = True
pause_progression = []
active_count = 0
error_count = 0
max_fallback = 0
fallback = 0
streak = 0
max_streak = 0
active_balance = 100
is_pause_displayed = False

delta_timer = global_timer(pygame)

upper_stats = UpperLayout(pygame, display_surface)
#upper_stats_s = UpperLayoutS(pygame, display_surface)

new_line_counter = Counter(upper_stats)
pause_counter = Counter(bpm = 1)

game = ChainedProcessor(pygame, display_surface, upper_stats, "hanzi chineese", STOCKS_DATA,
                        (60*1000)/BPM)
#game_s = ChainedProcessorS(pygame, display_surface, upper_stats_s, "hanzi chineese", TEST_LANG_DATA, (60*1000)/BPM)


progression = Progression(new_line_counter,
                          upper_stats)

beat_time = new_line_counter.drop_time 

font = pygame.font.Font(CYRILLIC_FONT, 200, bold = True)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
pygame.mouse.set_visible(False)
fpsClock = pygame.time.Clock()

mode = "STOCKS"
active_game = game
active_stats = upper_stats
swap = False
meta = ""

base_font = pygame.font.match_font("setofont")
base_font = pygame.font.Font(base_font, 50)
    
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

 
for time_delta in delta_timer:
    fpsClock.tick(30)

    if swap:
        swap = False

    if paused and not is_pause_displayed:
        display_surface.fill(white)
        text = font.render("PAUSED", True, colors.col_bg_darker)
        textRect = text.get_rect()
        textRect.center = (W//2, H//2)
        display_surface.blit(text, textRect)

        if pause_progression:
            total = sum(int(_[:-1]) for _ in pause_progression) - 100*len(pause_progression)
            place_text(" ".join(pause_progression) + "||" + f" {total}$" + f" | {max_fallback}/4 ERR | {max_streak}/10 GAINS",
                        W//2,
                        H//2-70 - 40,
                        transparent = False,
                        renderer = None,
                        base_col = (colors.dark_green if active_count>0 or max_fallback >= 4 else colors.col_error))
            

        if meta:
            chunks = [meta[i:i+70] for i in range(0, len(meta), 70)]
            for i, chunk in enumerate(chunks):
                place_text(chunk,
                            W//2,
                            H//2+70 + 40*(i+1),
                            transparent = False,
                            renderer = None,
                            base_col = (colors.col_bt_pressed))
        is_pause_displayed = True

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

            is_pause_displayed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
 
                quit()
        continue

    display_surface.fill(white)

    if pause_counter.is_tick(time_delta):
        pause_progression.append(f"{active_balance}$")
        active_balance = 100
        paused = True

    if new_line_counter.is_tick(time_delta):
        next_tick_time, swap, meta = active_game.add_line()
        new_line_counter.modify_bpm(next_tick_time)


    active_stats.redraw()
    feedback = active_game.tick(beat_time, time_delta)

    if feedback > 0:
        swap = True
        active_count += 3
        active_balance += 0.25*active_balance*3
        active_balance = int(active_balance)

        fallback = 0

        streak += 1
        max_streak = max(streak, max_streak)

    elif feedback <0:
        active_count -= 1
        active_balance -= 0.25*active_balance
        active_balance = int(active_balance)
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
