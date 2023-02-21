from utils import raw_extracter
from learning_model import ChainedFeature, FeaturesChain, ChainedModel, ChainUnit, ChainUnitType
from collections import OrderedDict
from math import sqrt
from itertools import compress, groupby, product
import random
import re
import os
import subprocess
from config import W, H, CYRILLIC_FONT
from config import CHINESE_FONT, VISUAL_PART
from config import STAKE_PART, META_DIR, META_MINOR_DIR, IMAGES_MINOR_DIR, META_ACTION
from config import HAPTIC_FEEDBACK_CMD
from config import HAPTIC_ERROR_CMD, HAPTIC_CORRECT_CMD
from config import HIGHER_TIMEFRAME_SCALE
from config import META_ACTION_STACK
from config import TEST
from config import KEYBOARD_MODE
#from config import TEST, TEST_WIN_CHANCE
from colors import col_bg_darker, col_wicked_darker
from colors import col_active_darker, col_bg_lighter
from colors import col_wicked_lighter, col_active_lighter
from colors import col_correct, col_error
import colors

from rendering_backend import backend_switch
backend = backend_switch().get_backend_ref()


LAST_EVENT = "POSITIVE"
LAST_META = None
NEW_EVENT = False
SPLIT_VIEW = True
######################################
### DATA PRODUCER
######################################

class ChainedsProducer():
    def __init__(S, label, csv_path,
                 meta_path = None, minor_meta = None, meta_actions = None,
                 meta_actions_stack = None, ui_ref = None, minor_images = None):

        S.csv_path = csv_path
        S.label = label
        S.meta_path = meta_path
        S.minor_meta = minor_meta
        S.minor_images = S.list_images(minor_images)
        S.meta_stack = meta_actions_stack

        S.meta_lines = S.extract_meta_dir(S.meta_path) if S.meta_path else []
        S.minor_lines = S.extract_meta_dir(S.minor_meta) if S.minor_meta else []
        S.action_lines = S.extract_meta(meta_actions) if meta_actions else None

        S.chains = S.prepare_data()
        S.active_chain = S.chains.get_active_chain()
        S.ui_ref = ui_ref

    def extract_meta(S, meta_path):
        meta = []
        header = None
        with open(meta_path, "r") as metafile:
            for line in metafile:
                line = line[:-1]
                if line in S.meta_stack:
                    header = line
                    continue
                if header:
                    S.meta_stack[header].append(line)

                meta.append(line.upper())
        return meta

    def extract_meta_dir(S, meta_path):
        meta_lines = []
        for _r, _d, _f in os.walk(meta_path):
            for f in _f:
                meta_lines += S.extract_meta(os.path.join(_r, f))
        return meta_lines

    def list_images(S, target_directory):
        selected_files = []
        for _r, _d, _f in os.walk(target_directory):
            for f in _f:
                selected_files.append(os.path.join(_r, f))
        return selected_files

    def produce_minor_image(S):
        if S.minor_images:
            return random.choice(S.minor_images)

    def prepare_data(S):
        data_extractor = raw_extracter(S.csv_path)
        chains = []
        features = []
        for i, (source, start_line) in enumerate(data_extractor):
            features.append(ChainedFeature(source, start_line))
            if i%5==0:
                chains.append(FeaturesChain(str(i//5), features))
                features = []
        return ChainedModel(chains)

    def produce_chain(S):
        S.active_chain = S.chains.get_active_chain()
        return S.active_chain

    def produce_next_feature(S):
        next_features_chain = S.chains.get_next_feature()

        return next_features_chain

    def produce_meta(S):
        if S.meta_lines:
            return random.choice(S.meta_lines)
        return ""

    def produce_meta_minor(S):
        if S.minor_lines:
            minor_idx = random.randint(0, len(S.minor_lines)-4)
            lines = S.minor_lines[minor_idx:minor_idx+3]

            if any(S.meta_stack.values()):
                ordered_meta = []
                for key, stk in S.meta_stack.items():

                    if random.randint(0,10)>3 and not TEST:
                        continue

                    if stk:
                        ordered_meta.append(key+" "+random.choice(stk))
                    else:
                        ordered_meta.append(key+" " + "---"*5)
                lines = ordered_meta + lines

            elif S.action_lines:
                lines = [random.choice(S.action_lines)] + lines

            return lines
        return ""


######################################
### ENTITIES HANDLER TEXT_AND_POSE
######################################


class ChainedEntity():
    def __init__(S,
                 chained_feature,
                 features_chain,
                 chains,
                 W,
                 H):

        global LAST_META
        LAST_META = None
        S.W, S.H = W, H

        S.chained_feature = chained_feature
        S.features_chain = features_chain
        S.uid = chained_feature.source + str(chained_feature.start_point)
        S.iuid = int(features_chain.chain_no)**2

        S.burn_mode = S.chained_feature.is_burning
        S.locked = False

        S.chains = chains
        S.main_title = S.chained_feature.get_main_title()

        S.correct = False
        S.error = False

        S.mode = "QUESTION"
        S.blink = False

        S.done = True
        S.time_perce_reserved = 0.0

        min_price, max_price = S.chained_feature.get_question_candles_minmax()
        trading_range = max_price - min_price
        mnp = min_price - trading_range*0.05
        mxp = max_price + trading_range*0.05
        S.question_pxls_to_price = lambda _y : mnp + (1 - (_y / S.H) ) * (mxp - mnp)

        S.entry = None
        S.sl = None
        S.tp = None
        S.idle_coursor = None
        S.idle_x = None
        S.entry_activated = None
        S.stop_activated = None
        S.profit_activated = None

        S.cached_candles = None
        S.cached_lines = None
        S.cached_lines_2 = None

        S.variation = 0
        S.variation_on_rise = True
        S.static_variation = random.randint(1,3)
        #S.static_variation = 2
        #S.floating_offset = random.randint(0,50)
        S.floating_offset = 0 
        S.constant_variations = random.sample([_ for _ in range(11)], 3)
        S.initial_action_done = False
        S.initial_action = random.choice(["ENTRY", "SL"])

        S.palette = random.choice(colors.palettes)

        S.question_index = VISUAL_PART
        S.active_index = 0
        S.active_index_float = 0
        S.overflow = 0
        S.clean_overflow = 0

        if not S.burn_mode:
            S.time_estemated = S.chained_feature.get_timing() / 3
        else:
            S.time_estemated = (S.chained_feature.get_timing() / 4) * 3

        S.random_labels = ["".join(_) for _ in product("abcdefghijklmnopqrstuwxyz", repeat=2)]
        S.random_labels = random.sample(S.random_labels, VISUAL_PART + STAKE_PART)
        
        S.test_idx = random.randint(0, VISUAL_PART)
        S.letter_idx = ""
        S.initial_idx = 0
        S.select_mode = False
        S.select_position = 0.5

    def check_sltp_hit(S):
        global LAST_EVENT
        global NEW_EVENT
        global LAST_META
        LAST_EVENT = "POSITIVE"
        NEW_EVENT = True

        if not S.sl or not S.entry or not S.tp:
            LAST_EVENT = "ERROR"
            return False

        candles = S.chained_feature.get_all_candles()
        triggered = False
        within = lambda price, candle: price <= candle.h and price >= candle.l

        stop_first = False
        profit_first = False

        stop_counted = False
        stop_counted_ex = False
        profit_counted = False
        profit_counted_ex = False

        for i, c in enumerate(candles[VISUAL_PART:]):

            if within(S.entry, c):
                S.entry_activated = True
                triggered = True

            if within(S.sl, c):
                stop_counted_ex = True

            if triggered and not profit_first and within(S.sl, c):
                S.stop_activated = True
                stop_counted = True
                stop_first = True

                LAST_EVENT = "ERROR"


            if within(S.tp, c):
                profit_counted_ex = True

            if triggered and not stop_first and within(S.tp, c):
                S.profit_activated = True
                profit_counted = True
                profit_first = True

                LAST_EVENT = "POSITIVE"


        opposite = False
        stp, entr, prof = False, False, False
        if not S.entry_activated:
            if stop_counted_ex and not profit_counted_ex:
                stp, entr, prof = True , False, False
            elif profit_counted_ex and not stop_counted_ex:
                stp, entr, prof = False, False, True

        elif S.entry_activated:
            if not profit_counted_ex and not stop_counted_ex:
                stp, entr, prof = False, True , False
            elif profit_first:
                stp, entr, prof = False, True , True
                if stop_counted_ex:
                    opposite = True
            elif stop_first:
                stp, entr, prof = True , True , False
                if profit_counted_ex:
                    opposite = True
            else:
                stp, entr, prof = True , True , True

        direction = "LONG"
        if S.sl > S.entry:
            direction = "SHORT"

        if not stp and not entr and not prof:
            LAST_META = "PATHETIC"
        elif stp and not entr and not prof:
                LAST_META = "PAPERCUT" if direction == "SHORT" else  "EXECUTION"
        elif stp and entr and not prof:
                LAST_META = "WOUNDED" if direction == "SHORT" else "INJURED"
                if opposite:
                    LAST_META = "SLIGHTLY " + LAST_META
                else:
                    LAST_META = "HARSHLY " + LAST_META

        elif stp and entr and prof:
                LAST_META = "MASACRE" if direction == "SHORT" else "BLAST"
                if profit_first and stop_counted_ex:
                    LAST_META = "SMALL " + LAST_META
                if stop_first and profit_counted_ex:
                    LAST_META = "TERRIBLE " + LAST_META

        elif not stp and entr and not prof:
                LAST_META = "CLATCH" if direction == "SHORT" else "FLEED"
        elif not stp and entr and prof:
            LAST_META = "STUBBED" if direction == "SHORT" else "NAILED"
            if not opposite:
                LAST_META = "PERFECTLY " + LAST_META
            if opposite:
                LAST_META = "DIRTLY " + LAST_META
        elif not stp and not entr and prof:
            LAST_META = "DROP" if direction == "SHORT" else "MISFIRE"

        if profit_first:
            return True

        LAST_EVENT = "ERROR"

        return False

    def register_answers(S):
        if S.mode == "QUESTION":
            if not S.burn_mode:
                is_solved = S.check_sltp_hit()
                S.chained_feature.register_progress(is_solved = is_solved)

                if not is_solved:
                    S.chained_feature.register_error()
                    S.features_chain.update_errors(register_new=True)

        if S.mode == "QUESTION":
            S.mode = "SHOW"
            S.question_index = VISUAL_PART - S.active_index

        elif S.mode == "SHOW":
            S.mode = "DONE"

        return False

    def match_error(S):
        if S.locked:
            return

        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "ERROR"
        NEW_EVENT = True
        S.locked = True

        S.chained_feature.burn_one(positive = False)


    def match_correct(S):
        if S.locked:
            return

        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "POSITIVE"
        NEW_EVENT = True
        S.locked = True

        S.chained_feature.burn_one(positive = True)


    def tick(S, time_passed, time_limit):
        S.variate()
        time_prece = time_passed/time_limit
        time_prece += 0.1
        if time_prece >= 1:
            time_prece = 1
        active_position = int(time_prece*STAKE_PART)
        S.active_index = active_position
        S.active_index_float = time_prece*STAKE_PART
        S.calculate_overflow()
        if S.mode == "SHOW":
            S.question_index = VISUAL_PART - S.active_index

    def calculate_overflow(S):
        S.overflow = int((S.active_index_float - S.active_index)*4)
        S.clean_overflow = S.active_index_float - S.active_index


    def check_answer(S, keys):

        keys = [True if "d" in keys else False,
                True if "f" in keys else False,
                True if "j" in keys else False,
                True if "k" in keys else False]


        if len([_ for _ in keys if _]) > 1:
            S.match_error()

        for i, _ in enumerate(keys):
            if _ and i == S.chained_feature.burn_key:
                S.match_correct()
                return

        S.match_error()

    def process_canle_keys(S, key_states):

        if any(key_states) and not S.select_mode:
            key_states = [_ for _ in key_states if _]

            if key_states[0] == "select":

                S.select_mode = True

                if not S.cached_candles or not S.test_idx:
                    return

                target_candle = S.cached_candles[S.test_idx]

                S.idle_coursor = target_candle.l + (target_candle.h-target_candle.l) * S.select_position

                return

            if not key_states:
                return

            S.letter_idx += key_states[0]

            #print(S.letter_idx)

            if len(S.letter_idx) > 2:
                S.letter_idx = S.letter_idx[2]

            if len(S.letter_idx) == 2:
                try:
                    S.test_idx = S.random_labels.index(S.letter_idx)
                except:
                    S.test_idx = 0

        if any(key_states) and S.select_mode:
            key_states = [_ for _ in key_states if _]

            if not S.letter_idx:
                S.select_mode = False
                return

            if key_states[0] == "select":
                S.select_mode = False
                S.letter_idx = ""
                S.test_idx = -1
                return

            if not S.cached_candles:
                return

            if key_states[0] == "h":
                S.test_idx -= 1
                S.select_position = 0.5
            if key_states[0] == "l":
                S.test_idx += 1
                S.select_position = 0.5

            if key_states[0] == "j":
                S.select_position = (0+S.select_position)/2
            if key_states[0] == "k":
                S.select_position = (1+S.select_position)/2

            if key_states[0] == "b":
                S.select_position = 0.5
            if key_states[0] == "z":
                S.select_position = (0.5+S.select_position)/2

            target_candle = S.cached_candles[S.test_idx]

            S.idle_coursor = target_candle.l + (target_candle.h-target_candle.l) * S.select_position

            if key_states[0] == "e":
                S.entry = S.idle_coursor 
                if S.entry and S.sl:
                    risk = S.entry - S.sl
                    reward = risk * 3
                    S.tp = S.entry + reward
            elif key_states[0] == "s":
                S.sl = S.idle_coursor
                if S.entry and S.sl:
                    risk = S.entry - S.sl
                    reward = risk * 3
                    S.tp = S.entry + reward


    def register_keys(S, key_states, time_percent, time_based = False):
        #S.select_candle_keyboard(key_states)

        if not time_based and S.burn_mode:
            S.check_answer(key_states)
        elif S.mode == "QUESTION":
            S.process_canle_keys(key_states)


        if time_based:
            S.variate()
            time_p = time_percent

            if not S.done:
                S.time_perce_reserved = time_percent

            if S.done:
                time_p = (time_p - S.time_perce_reserved)/(1.0 - S.time_perce_reserved)

    def register_mouse(S, mouse_poses):
        # IF NOT KEYBOARD MODE
        return

        if S.burn_mode:
            return
        if S.mode == "QUESTION":
            mouse_position = backend.api().mouse.get_pos()

            LMB, RMB = 0, 2

            if not S.initial_action_done:
                if S.initial_action == "ENTRY" and not mouse_poses[LMB]:
                    return
                elif S.initial_action == "SL" and not mouse_poses[RMB]:
                    return
                else:
                    S.initial_action_done = True

            if mouse_poses[LMB]:
                S.entry = S.question_pxls_to_price(mouse_position[1])

            if mouse_poses[RMB]:
                S.sl = S.question_pxls_to_price(mouse_position[1])

            if S.entry and S.sl:
                risk = S.entry - S.sl
                reward = risk * 3
                S.tp = S.entry + reward

    def register_idle_mouse(S):
        # IF NOT KEYBOARD MODE
        return

        if S.burn_mode:
            return
        if S.mode == "QUESTION":
                mouse_position = backend.api().mouse.get_pos()
                S.idle_coursor = S.question_pxls_to_price(mouse_position[1])
                S.idle_x = mouse_position[0] / W
        elif not S.blink:
            S.idle_coursor = S.question_pxls_to_price(int(H/STAKE_PART)*S.active_index_float)
        else:
            S.idle_coursor = S.question_pxls_to_price(int(H/STAKE_PART)*0)

    def get_sltp(S):
        return S.entry, S.sl, S.tp


    def produce_geometries(S):
        graphical_objects = []
        set_color = lambda _ : colors.col_active_lighter
        set_bg_color = lambda _ : colors.col_bt_down
        set_font = lambda _ : ChainUnitType.font_cyrillic
        set_size = lambda _ : 30


        options_x_corners = [W//2 - W//5, W//2 - W//10, W//2 + W//10, W//2 + W//5]
        options_y_corners = [H-50,      H-50,    H-50,  H-50]
        options_w = 150
        options_h = 50

        options = ["loNG", "DusT", "rAIn", "SHOrt"]
        opt_colors = [colors.option_fg, colors.dark_green, colors.red2, colors.red1]
        for i, (x1, y1) in enumerate(zip(options_x_corners, options_y_corners)):
            ctx = options[i]
            ctx_x = x1
            ctx_y = y1
            cx, cy = ctx_x + options_w//2, ctx_y + options_h//2
            ctx_w, ctx_h = options_w, options_h

            graphical_objects.append(WordGraphical(ctx,
                                                   cx,
                                                   cy,
                                                   opt_colors[i],
                                                   None,
                                                   font = set_font(ctx),
                                                   font_size = set_size(ctx)))

        return graphical_objects

    def produce_candles(S):
        if S.mode == "QUESTION" or S.blink:
            if not S.cached_candles:

                S.cached_candles = S.chained_feature.get_question_candles()[S.floating_offset:]
                for i in range(len(S.cached_candles)):
                    S.cached_candles[i].label = S.random_labels[i]

                S.initial_idx = S.cached_candles[0].index

            return S.cached_candles
        else:
            candles = S.chained_feature.get_candles_with_offset(S.active_index, VISUAL_PART)[S.floating_offset:]
            for i in range(len(candles)):
                candles[i].label = S.random_labels[i+S.active_index]

            S.initial_idx = candles[0].index - S.active_index

            return candles

    def produce_lines(S):
        if S.mode == "QUESTION" or S.blink:
            if not S.cached_lines:
                S.cached_lines = S.chained_feature.get_lines_with_offset(0, VISUAL_PART)
            return S.cached_lines
        else:
            return S.chained_feature.get_lines_with_offset(S.active_index, VISUAL_PART)

    def produce_high_tf_pattern(S):
        if not S.cached_lines_2:
            S.cached_lines_2 = S.chained_feature.get_high_tf_context()
        return S.cached_lines_2


    def variate(S):
        if S.variation_on_rise:
            S.variation += 1
        else:
            S.variation -= 1

        if S.variation == 0:
            if S.mode == "QUESTION" or S.blink:
                avaliable_numbers = [_ for _ in range(11) if _ not in S.constant_variations]
                if len(S.constant_variations)%2:
                    S.constant_variations.append(random.choice(avaliable_numbers))
                else:
                    S.constant_variations.pop(0)
            else:
                S.constant_variations = []

        if S.variation > 40:
            S.variation_on_rise = False
        elif S.variation < -40:
            S.variation_on_rise = True

######################################
### LINES HANDLER GRAPHICS
######################################

class WordGraphical():
    def __init__(S, text, x, y, color, bg_color = (150,150,150),
                 font = ChainUnitType.font_utf,
                 font_size = None,
                 rect = [], transparent = False):
        S.rect = rect
        S.text = text
        S.x = x
        S.y = y
        S.color = color
        S.bg_color = bg_color
        S.font = font
        S.font_size = font_size
        S.transparent = transparent

class ChainedDrawer():
    def __init__(S, display_instance, W, H):
        S.display_instance = display_instance
        S.W = W
        S.H = H
        S.cyrillic_30 = backend.api().font.Font(CYRILLIC_FONT, 30, bold = True)
        S.cyrillic_40 = backend.api().font.Font(CYRILLIC_FONT, 40, bold = True)
        S.cyrillic_60 = backend.api().font.Font(CYRILLIC_FONT, 60, bold = True)
        S.cyrillic_120 = backend.api().font.Font(CYRILLIC_FONT, 120, bold = True)

        S.cyrillic_10 = backend.api().font.Font(CYRILLIC_FONT, 10, bold = True)
        S.cyrillic_20 = backend.api().font.Font(CYRILLIC_FONT, 20, bold = True)
        S.cyrillic_15 = backend.api().font.Font(CYRILLIC_FONT, 15, bold = True)

        S.utf_30 = backend.api().font.Font(CHINESE_FONT, 30, bold = True)
        S.utf_40 = backend.api().font.Font(CHINESE_FONT, 40, bold = True)
        S.utf_60 = backend.api().font.Font(CHINESE_FONT, 60, bold = True)
        S.utf_120 = backend.api().font.Font(CHINESE_FONT, 120, bold = True)


    def pick_font(S, font_type = ChainUnitType.font_utf, size = 40):
        if font_type == ChainUnitType.font_utf:
            if not size:
                return S.utf_30
            elif size <= 30:
                return S.utf_30
            elif size <= 40:
                return S.utf_40
            elif size <= 60:
                return S.utf_60
            else:
                return S.utf_120
        else:
            if not size:
                return S.cyrillic_30
            elif size <= 30:
                return S.cyrillic_30
            elif size <= 40:
                return S.cyrillic_40
            elif size <= 60:
                return S.cyrillic_60
            else:
                return S.cyrillic_120

    def draw_line(S, line):

        if not line.burn_mode:
            return

        geometries = line.produce_geometries()
        color = (128,128,128)
        for geometry in geometries:
            message = geometry.text
            font = S.pick_font(geometry.font, geometry.font_size)

            if not geometry.transparent:
                text = font.render(message, True, geometry.color, geometry.bg_color)
            else:
                text = font.render(message, True, geometry.color)

            textRect = text.get_rect()
            textRect.center = (geometry.x, geometry.y)

            if geometry.rect:

                x, y, w, h = geometry.rect
                backend.api().draw.rect(S.display_instance,
                                  (50,50,50),
                                  (x,y,w,h),
                                   width = 2)

            S.display_instance.blit(text, textRect)

    def display_keys(S, keys, line):

        if not line.burn_mode:
            return

        options_x_corners = [W//2 - W//5, W//2 - W//10, W//2 + W//10, W//2 + W//5]
        options_y_corners = [H-50,      H-50,    H-50,  H-50]
        options_w = 150
        options_h = 50

        keys = [True if "d" in keys else False,
                True if "f" in keys else False,
                True if "j" in keys else False,
                True if "k" in keys else False]

        for i, (x1, y1) in enumerate(zip(options_x_corners, options_y_corners)):
            key_state = keys[i]
            xc, yc = x1 + options_w / 2, y1 + options_h / 2

            color = (255,255,255)
            if key_state == "up":
                color = colors.col_bt_down if LAST_EVENT == "POSITIVE" else colors.col_error_2
            elif key_state == "down":
                color = colors.col_bt_pressed if LAST_EVENT == "POSITIVE" else colors.col_active_lighter
            else:
                color = (0,150,100)

            backend.api().draw.rect(S.display_instance,
                                  color,
                                  (x1, y1, options_w, options_h), border_radius=15)

    def minMaxOfZon(S, candleSeq):
        if candleSeq:
            minP = min(candleSeq, key = lambda _ : _.l).l
            maxP = max(candleSeq, key = lambda _ : _.h).h
            return minP, maxP
        else:
            return 0, 1

    def generateOCHLPicture(S, line):

        last_color = None

        def split_x(x):
            if x >= W//2:
                x = x - W//2
            else:
                x = x + W//2 + W//64
            return x

        def drawCircleSimple(x1,y1,r, col = (125,125,125)):
            if SPLIT_VIEW:
                x1 = split_x(x1)
            backend.api().draw.circle(S.display_instance,col, (x1,y1),r)

        def drwLineSimple(X1, Y1, X2, Y2, ignore_spit=False):

            if SPLIT_VIEW and not ignore_spit:
                X1 = split_x(X1)
                X2 = split_x(X2)

            reversed = X1 > W//2 and X2 < W//2 or X1 < W//2 and X1 > W//2
            if SPLIT_VIEW and reversed and not ignore_spit:
                return

            backend.api().draw.line(S.display_instance,(180,180,180),(X1,Y1),(X2,Y2),1)

        def drwZonBrdr(zone, ignore_spit = False):
            X1 = zone[0]
            Y1 = zone[1]
            X2 = zone[2]
            Y2 = zone[3]
            X1, X2 = min(X1, X2), max(X1, X2)
            Y1, Y2 = min(Y1, Y2), max(Y1, Y2)
            if SPLIT_VIEW and not ignore_spit:
                Y1 = split_x(Y1)
                Y2 = split_x(Y2)
            dX = X2 - X1
            dY = Y2 - Y1
            backend.api().draw.rect(S.display_instance,(180,180,180),
                                           (Y1,X1,(dY),(dX)), width = 1)

        def drwSqrZon(zone ,x1,y1,x2,y2, col, strk=0,ignore_spit=False):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)
                X2 = int(X + dx*x2)
                Y2 = int(Y + dy*y2)
                X1, X2 = min(X1, X2), max(X1, X2)
                Y1, Y2 = min(Y1, Y2), max(Y1, Y2)

                if SPLIT_VIEW and not ignore_spit:
                    Y1 = split_x(Y1)
                    Y2 = split_x(Y2)

                reversed = Y1 > W//2 and Y2 < W//2 or Y1 < W//2 and Y1 > W//2
                if SPLIT_VIEW and reversed:
                    return

                clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)
                lighter_col = [clip_color(col[0]*0.6), clip_color(col[1]*0.6), clip_color(col[2]*0.6)]
                backend.api().draw.line(S.display_instance,lighter_col,(Y1,X1),(Y1,X2),2)
                backend.api().draw.line(S.display_instance,lighter_col,(Y1,X2),(Y2,X2),2)
                backend.api().draw.line(S.display_instance,lighter_col,(Y2,X2),(Y2,X1),2)
                backend.api().draw.line(S.display_instance,lighter_col,(Y2,X1),(Y1,X1),2)
                backend.api().draw.rect(S.display_instance,col,
                                               (Y1,X1,(Y2-Y1),(X2-X1)), width = strk)
            except Exception as e:
                print(e)
                pass

        def drawCircleInZon(zone ,x1,y1,r,col, width=0):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)

                if SPLIT_VIEW:
                    return
                    Y1 = split_x(Y1)

                backend.api().draw.circle(S.display_instance,col,
                                               (Y1,X1),r, width = width)
            except Exception as e:
                pass

        def fitPointZone(zone, x1,y1, ignore_spit = False):
            X = zone[0]
            Y = zone[1]
            dx = zone[2] - X
            dy = zone[3] - Y
            X1 = int(X + dx*x1)
            Y1 = int(Y + dy*y1)

            if SPLIT_VIEW and not ignore_spit:
                Y1 = split_x(Y1)
            return X1, Y1


        def drwLineZon(zone ,x1,y1,x2,y2, col, strk = 1, out_line = True, ignore_spit = False):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)
                X2 = int(X + dx*x2)
                Y2 = int(Y + dy*y2)

                if SPLIT_VIEW and not ignore_spit:
                    Y1 = split_x(Y1)
                    Y2 = split_x(Y2)

                reversed = Y1 > W//2 and Y2 < W//2 or Y1 < W//2 and Y1 > W//2
                if SPLIT_VIEW and reversed and not ignore_spit:
                    return

                clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)
                lighter_col = [clip_color(col[0]*0.6), clip_color(col[1]*0.6), clip_color(col[2]*0.6)]

                if out_line:
                    backend.api().draw.line(S.display_instance,lighter_col,(Y1,X1),(Y2,X2),strk+1)
                backend.api().draw.line(S.display_instance,col,(Y1,X1),(Y2,X2),strk)

            except Exception as e:
                pass

        def hex_to_bgr(hx):
            hx = hx.lstrip('#')
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

        def getCandleCol(candle, opposite_blend = False, fred = False, fgreen = False):

            base_line_color = colors.col_wicked_darker
            inter_color = lambda v1, v2, p: v1 + (v2-v1)*p
            interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                                       inter_color(col1[1], col2[1], percent),
                                                       inter_color(col1[2], col2[2], percent))
            rgb_col = colors.white

            unique_color_idx = candle.index%len(colors.palettes)
            #palette = line.palette
            palette = colors.palettes[unique_color_idx]
            green1, green2, red1, red2, mixed = palette

            nonlocal last_color
            if not last_color:
                last_color = palette

            if candle.is_same_color:
                green1, green2, red1, red2, mixed = last_color

            if line.mode != "QUESTION" and not line.blink:
                green1, green2, red1, red2, mixed = colors.palettes[int(line.iuid)%len(colors.palettes)]

            if candle.green or fgreen:
                if not opposite_blend:
                    rgb_col = interpolate(green2, green1, abs(line.variation/40))
                else:
                    rgb_col = interpolate(mixed, green2, abs(line.variation/40))

            elif candle.red or fred:
                rgb_col = colors.dark_red
                if not opposite_blend:
                    rgb_col = interpolate(red1, red2, abs(line.variation/40))
                else:
                    rgb_col = interpolate(mixed, red1, abs(line.variation/40))

            clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)

            if candle.green:
                rgb_col = (clip_color(rgb_col[0]),
                           clip_color(rgb_col[1]),
                           clip_color(rgb_col[2]))
            else:
                rgb_col = (clip_color(rgb_col[0]),
                           clip_color(rgb_col[1]),
                           clip_color(rgb_col[2]))

            last_color = green1, green2, red1, red2, mixed

            return rgb_col

        def fit_to_zon(val, minP, maxP, stretch_range = True):
            trading_range = maxP - minP
            if stretch_range:
                mnp = minP-trading_range*0.05
                mxp = maxP+trading_range*0.05
            else:
                mnp = minP
                mxp = maxP
            candleRelative =  (val-mnp)/(mxp-mnp)
            return candleRelative

        def place_text(text, x, y, transparent = True, renderer = None, base_col = (80,80,80)):
            #text = S.morfer.morf_text(text)
            if renderer is None:
                renderer = S.cyrillic_20

            if not transparent:
                text = renderer.render(text, True, base_col, (150,150,151))
            else:
                text = renderer.render(text, True, base_col)

            textRect = text.get_rect()
            textRect.center = (x, y)
            S.display_instance.blit(text, textRect)

        def drawCandle(zone, candle, minP, maxP, p1, p2,
                       entry = None, stop = None, profit = None, idle = None,
                       last = False, first = False, draw_special = False, predefined_color = False, dpth = None):

            if not dpth:
                print("No depth provided")
                return None, None, None, None

            special = False
            special_color = None
            special_priority = None

            i = candle.index - p1

            #if len(line.constant_variations)%2 == i%2 and not last and line.mode == "QUESTION":
                #if random.randint(0,10)>5:
                    #return None, None, None, None

            width = 0
            if draw_special:
                width = 2

            # w0 = 0.5
            # w1 = 0.25
            # w2 = 0.4
            # w3 = 0.5
            # c0 = i+w0
            #if len(line.constant_variations)%2 == i%2 and not last and line.mode == "QUESTION":
            w0 = 0.5
            w1 = 0.2
            w2 = 0.35
            w3 = 0.5
            c0 = i+w0


            _o,_c,_h,_l = candle.ochl()

            if not predefined_color:
                col = getCandleCol(candle, fred=_o>_c,fgreen=_o<_c)
            else:
                col = predefined_color

            oline = fit_to_zon(_o, minP, maxP)
            cline = fit_to_zon(_c, minP, maxP)
            lwick = fit_to_zon(_l, minP, maxP)
            hwick = fit_to_zon(_h, minP, maxP)

            mid_line = (oline+cline)/2

            special_w = (c0/dpth) * W
            special_h = H - mid_line * H
            special_coord = [special_w, special_h]

            candle_len = hwick - lwick
            candle_mid = (_h+_l)/2
            body_mid = (_o+_c)/2
            candle_center = fit_to_zon(candle_mid, minP, maxP)
            body_mid_zone = fit_to_zon(body_mid, minP, maxP)

            # if entry and entry >_l and entry < _h:
            #     h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if entry > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
            #     if not draw_special:
            #         drwSqrZon(zone, h_position,(c0-0.55)/dpth,
            #                                l_position,(c0+0.55)/dpth,(colors.col_bg_darker))
            #     w1 = 0.35
            #     w2 = 0.4
            #     w3 = 0.5
            #     special = True
            #     special_color = col 
            #     special_priority = 0
            # elif stop and stop > _l and stop < _h:
            #     h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if stop > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
            #     if not draw_special:
            #         drwSqrZon(zone, h_position,(c0-0.55)/dpth,
            #                                l_position,(c0+0.55)/dpth,(colors.col_black))
            #     w1 = 0.35
            #     w2 = 0.4
            #     w3 = 0.5
            #     special = True
            #     special_color = col 
            #     special_priority = 1
            # elif profit and profit > _l and profit < _h:
            #     h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if profit > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
            #     if not draw_special:
            #         drwSqrZon(zone, h_position,(c0-0.55)/dpth,
            #                                l_position,(c0+0.55)/dpth,(colors.col_bt_pressed))
            #     w1 = 0.35
            #     w2 = 0.4
            #     w3 = 0.5
            #     special = True
            #     special_color = col 
            #     special_priority = 2
            # #elif idle and idle > _l and idle < _h:
            #     h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if idle > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
            #     if not draw_special:
            #         drwSqrZon(zone, h_position,(c0-0.55)/dpth,
            #                                l_position,(c0+0.55)/dpth,(colors.col_wicked_darker))
            #     w1 = 0.35
            #     w2 = 0.4
            #     w3 = 0.5
            #     special = False
            #     #special = True
            #     #special_color = col 
            #     #special_priority = 3
            #

            if candle.to_offset and candle.to_price and not line.mode == "QUESTION" and line.burn_mode:
                p_connected = fit_to_zon(candle.to_price, minP, maxP)
                p_initial = fit_to_zon(candle.from_price, minP, maxP)
                i_connected = candle.index + candle.to_offset - p1

                if line.iuid%2:
                    drwLineZon(zone, 1-p_initial,0,1-p_initial,1,(150,255,150),strk=1, ignore_spit = True)
                else:
                    drwLineZon(zone, 1-p_connected,0,1-p_connected,1,(255,150,255),strk=1, ignore_spit = True)

                mid_price = (p_initial + p_connected)/2
                mid_ind = (c0 + i_connected)/2

                burn_col = line.palette[4]

                if candle.burn_flag == "LONG":
                    burn_col = colors.option_fg
                elif candle.burn_flag == "LONG P":
                    burn_col = colors.dark_green
                elif candle.burn_flag == "SHORT P":
                    burn_col = colors.red2
                elif candle.burn_flag == "SHORT":
                    burn_col = colors.red1

                drwLineZon(zone, 1-p_initial,(c0)/dpth,1-mid_price,(c0)/dpth,burn_col,strk=10)
                drwLineZon(zone, 1-mid_price,(c0)/dpth,1-p_connected,(i_connected+w0)/dpth,burn_col,strk=10)

            if last:
                upper, lower = max(oline, cline), min(oline, cline)

                drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=3)
                drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=3)

                if line.static_variation%2!=0:
                    drwSqrZon(zone, 1-cline,(c0-w1)/dpth,
                                           1-oline,(c0+w1)/dpth,col, strk = width)
                else:
                    drwLineZon(zone, 1-oline, (c0)/dpth,
                                     1-cline, (c0)/dpth, col, strk = width+2)
                    drwLineZon(zone, 1-oline, (c0-w3)/dpth,
                                     1-oline, (c0)/dpth, col, strk = width+2)
                    drwLineZon(zone, 1-cline, (c0)/dpth,
                                     1-cline, (c0+w3)/dpth, col, strk = width+2)

            else:
                upper, lower = max(oline, cline), min(oline, cline)

                if candle.thick_upper and (9 in line.constant_variations):

                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=2)
                    drwLineZon(zone, 1-hwick,(c0-0.15)/dpth,1-upper,(c0-0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-hwick,(c0+0.15)/dpth,1-upper,(c0+0.15)/dpth,col,strk=1)

                elif candle.thick_lower and (9 in line.constant_variations):
                    drwLineZon(zone, 1-lwick,(c0-0.15)/dpth,1-lower,(c0-0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-lwick,(c0+0.15)/dpth,1-lower,(c0+0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=2)
                else:
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=2)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=2)

                if not candle.is_same_color and not draw_special:
                    drwLineZon(zone, 1-cline,(i)/dpth,1-oline,(i)/dpth,colors.col_black,strk=1)

                if candle.inner and (1 in line.constant_variations):

                    mid_p = (cline + oline)/2

                    drwLineZon(zone, 1-cline,(c0-w1)/dpth,1-oline,(c0+w1)/dpth,col,strk=1)
                    drwLineZon(zone, 1-cline,(c0+w1)/dpth,1-oline,(c0-w1)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(mid_p),(c0-w2)/dpth,1-mid_p,(c0+w2)/dpth,col,strk=1)

                    drwLineZon(zone, 1-cline,(c0+w1)/dpth,1-cline,(c0-w1)/dpth,col,strk=1)
                    drwLineZon(zone, 1-oline,(c0+w1)/dpth,1-oline,(c0-w1)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(oline),(c0)/dpth,1-oline,(i-w0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-(cline),(c0)/dpth,1-cline,(i-w0+w1)/dpth,col,strk=3)


                elif candle.pierce and (2 in line.constant_variations):
                    upper_p = fit_to_zon(candle.upper_pierce_line, minP, maxP)
                    lower_p = fit_to_zon(candle.lower_pierce_line, minP, maxP)
                    upper_b = max(oline, cline)
                    lower_b = min(oline, cline)
                    mid_p = (upper_p + lower_p)/2

                    drwLineZon(zone, 1-(mid_p),(c0+w1)/dpth,1-upper_p,(c0)/dpth,col,strk=1)
                    drwLineZon(zone, 1-(mid_p),(c0-w1)/dpth,1-upper_p,(c0)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(mid_p),(c0-w2-1.0)/dpth,1-mid_p,(c0+w2)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(mid_p),(c0+w1)/dpth,1-lower_p,(c0)/dpth,col,strk=1)
                    drwLineZon(zone, 1-(mid_p),(c0-w1)/dpth,1-lower_p,(c0)/dpth,col,strk=1)

                    drwLineZon(zone,1-lower_p,(c0-w1)/dpth,1-lower_p,(c0+w1)/dpth,col,strk=1)
                    drwLineZon(zone,1-upper_p,(c0-w1)/dpth,1-upper_p,(c0+w1)/dpth,col,strk=1)

                    if line.static_variation%2!=0:
                        drwSqrZon(zone,1-lower_p,(c0-w1)/dpth,
                                       1-lower_b,(c0+w1)/dpth,col, strk = width)
                        drwSqrZon(zone,1-upper_p,(c0-w1)/dpth,
                                       1-upper_b,(c0+w1)/dpth,col, strk = width)
                    else:
                        drwLineZon(zone, 1-lower_p, (c0)/dpth,
                                         1-lower_b, (c0)/dpth, col, strk = width+2)
                        drwLineZon(zone, 1-upper_p, (c0)/dpth,
                                         1-upper_b, (c0)/dpth, col, strk = width+2)
                                     
                        drwLineZon(zone, 1-oline, (c0-w3)/dpth,
                                         1-oline, (c0)/dpth, col, strk = width+2)
                        drwLineZon(zone, 1-cline, (c0)/dpth,
                                         1-cline, (c0+w3)/dpth, col, strk = width+2)

                elif candle.up_from_within and (0 in line.constant_variations):
                    upper_p = fit_to_zon(candle.up_within_p1, minP, maxP)
                    upper_b = max(oline, cline)
                    lower_b = min(oline, cline)

                    mid_1 = upper_p + (upper_b - upper_p)/4
                    mid_2 = upper_p + (upper_b - upper_p)/4*2
                    mid_3 = upper_p + (upper_b - upper_p)/4*3

                    if line.static_variation%2!=0:
                        drwSqrZon(zone, 1-lower_b,(c0-w1)/dpth,
                                               1-upper_p,(c0+w1)/dpth,col, strk = width)
                    else:
                        drwLineZon(zone, 1-lower_b, (c0)/dpth,
                                         1-upper_p, (c0)/dpth, col, strk = width+2)

                        drwLineZon(zone, 1-lower_b, (c0-w3)/dpth,
                                         1-lower_b, (c0)/dpth, col, strk = width+2)


                    drwLineZon(zone, 1-upper_b,(c0-w1)/dpth,1-upper_b,(c0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-upper_p,(c0-w1)/dpth,1-upper_b,(c0-w1)/dpth,col,strk=2)
                    drwLineZon(zone, 1-upper_p,(c0+w1)/dpth,1-upper_b,(c0+w1)/dpth,col,strk=2)

                    drwLineZon(zone, 1-mid_1,(c0-w2)/dpth,1-mid_1,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_2,(c0-w2)/dpth,1-mid_2,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_3,(c0-w2)/dpth,1-mid_3,(c0+w2)/dpth,col,strk=3)

                elif candle.down_from_within and (0 in line.constant_variations):
                    lower_p = fit_to_zon(candle.down_within_p1, minP, maxP)
                    lower_b = min(oline, cline)
                    upper_b = max(oline, cline)
                    mid_p = (lower_p+lower_b)/2

                    mid_1 = lower_p - (lower_p - lower_b)/4
                    mid_2 = lower_p - (lower_p - lower_b)/4*2
                    mid_3 = lower_p - (lower_p - lower_b)/4*3

                    if line.static_variation%2!=0:
                        drwSqrZon(zone, 1-upper_b,(c0-w1)/dpth,
                                               1-lower_p,(c0+w1)/dpth,col, strk = width)
                    else:
                        drwLineZon(zone, 1-upper_b, (c0)/dpth,
                                         1-lower_p, (c0)/dpth, col, strk = width+2)

                        drwLineZon(zone, 1-upper_b, (c0-w3)/dpth,
                                         1-upper_b, (c0)/dpth, col, strk = width+2)

                    drwLineZon(zone, 1-lower_b,(c0-w1)/dpth,1-lower_b,(c0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-lower_p,(c0+w1)/dpth,1-lower_b,(c0+w1)/dpth,col,strk=2)
                    drwLineZon(zone, 1-lower_p,(c0-w1)/dpth,1-lower_b,(c0-w1)/dpth,col,strk=2)

                    drwLineZon(zone, 1-mid_1,(c0-w2)/dpth,1-mid_1,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_2,(c0-w2)/dpth,1-mid_2,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_3,(c0-w2)/dpth,1-mid_3,(c0+w2)/dpth,col,strk=3)


                else:
                    if line.static_variation%2!=0:
                        drwSqrZon(zone, 1-cline,(c0-w1)/dpth,
                                               1-oline,(c0+w1)/dpth,col, strk = width)
                    else:
                        drwLineZon(zone, 1-cline, (c0)/dpth,
                                         1-oline, (c0)/dpth, col, strk = width+2)

                        drwLineZon(zone, 1-oline, (c0-w3)/dpth,
                                         1-oline, (c0)/dpth, col, strk = width+2)

                        drwLineZon(zone, 1-cline, (c0)/dpth,
                                         1-cline, (c0+w3)/dpth, col, strk = width+2)

                    if 3 in line.constant_variations or line.blink:
                        mid_p = (cline + oline)/2
                        drwLineZon(zone, 1-(mid_p),(c0-w2)/dpth,1-mid_p,(c0+w2)/dpth,col,strk=3)


                if candle.weak_pierce_prev and (4 in line.constant_variations):
                    lower_b = min(oline, cline)
                    upper_b = max(oline, cline)
                    mid_h_point = hwick-(hwick-upper_b)/2
                    mid_l_point = lwick+(lower_b-lwick)/2

                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-mid_h_point,(i)/dpth,col,strk=1)
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-mid_l_point,(i)/dpth,col,strk=1)

                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lwick,(i-w0-w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-hwick,(i-w0-w1)/dpth,col,strk=3)

                if candle.weak_pierce_next and (5 in line.constant_variations):
                    lower_b = min(oline, cline)
                    upper_b = max(oline, cline)
                    mid_h_point = (upper_b+hwick)/2
                    mid_l_point = (lower_b+lwick)/2

                    drwLineZon(zone, 1-mid_h_point,(i+1)/dpth,1-hwick,(c0)/dpth,col,strk=1)
                    drwLineZon(zone, 1-mid_l_point,(i+1)/dpth,1-lwick,(c0)/dpth,col,strk=1)

                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lwick,(i+1.5+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-hwick,(i+1.5+w1)/dpth,col,strk=3)

                if candle.overhigh and (6 in line.constant_variations) and not draw_special:
                    if candle.thick_upper:
                        drwLineZon(zone, 1-hwick-1.5/dpth,(c0)/dpth,1-hwick-2.5/dpth, c0/dpth,col,strk=1)
                    drwLineZon(zone, 1-hwick-0.5/dpth,(c0-0.15)/dpth,1-hwick-1.5/dpth,(c0)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick-0.5/dpth,(c0+0.15)/dpth,1-hwick-1.5/dpth,(c0)/dpth,col,strk=3)


                if candle.overlow and (7 in line.constant_variations) and not draw_special:
                    if candle.thick_lower:
                        drwLineZon(zone, 1-lwick+1.5/dpth,(c0)/dpth,1-lwick+2.5/dpth, c0/dpth,col,strk=1)
                    drwLineZon(zone, 1-lwick+0.5/dpth,(c0-0.15)/dpth,1-lwick+1.5/dpth,c0/dpth,col,strk=3)
                    drwLineZon(zone, 1-lwick+0.5/dpth,(c0+0.15)/dpth,1-lwick+1.5/dpth,c0/dpth,col,strk=3)

                if candle.vRising and (10 in line.constant_variations) and not draw_special:
                    if candle.red:
                        drwLineZon(zone, 1-lwick+3.5/dpth,(c0-w0/3)/dpth,1-lwick+4.5/dpth, (c0+w0/3)/dpth,col,strk=2)
                    else:
                        drwLineZon(zone, 1-hwick-3.5/dpth,(c0-w0/3)/dpth,1-hwick-4.5/dpth, (c0+w0/3)/dpth,col,strk=2)

            #if len(line.constant_variations)%2 == i%2 and not last and line.mode == "QUESTION":
                #return special, special_color, special_priority, special_coord

            offseta = 1 if not draw_special else 0 
            offsetb = 1 if not draw_special else 1
            stroke = 2 #if not draw_special else 4
            if idle and ((idle>=_l and idle<=_h) or (last or first) and (idle > maxP or idle < minP)):
                line_level = fit_to_zon(idle, minP, maxP)
                #special_coord[1] = (1-line_level)*H
                drwLineZon(zone, 1-line_level,(i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                               colors.col_wicked_darker, strk = stroke)

            if entry and ((entry>=_l and entry <=_h) or (last or first) and (entry > maxP or entry < minP)):
                line_level = fit_to_zon(entry, minP, maxP)
                #special_coord[1] = (1-line_level)*H
                if not entry_activated:
                    drwLineZon(zone, 1-line_level,
                                   (i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                                   (150,255,150), strk = stroke)
                else:
                    drwLineZon(zone, 1-line_level,
                                   (i-offseta)/dpth,1-line_level,
                                   (i+offsetb)/dpth,(150,255,150),
                                   strk = stroke*2)
            if stop and ((stop>=_l and stop<=_h) or (last or first) and (stop > maxP or stop < minP)):
                line_level = fit_to_zon(stop, minP, maxP)
                #special_coord[1] = (1-line_level)*H
                if not stop_activated:
                    drwLineZon(zone,
                                   1-line_level,(i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                                   (255,150,150), strk = stroke)
                else:
                    drwLineZon(zone, 1-line_level,(i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                                   (255,150,150), strk = stroke*2)
            if profit and ((profit >=_l and profit<=_h) or (last or first) and (profit > maxP or profit < minP)):
                line_level = fit_to_zon(profit, minP, maxP)
                #special_coord[1] = (1-line_level)*H
                if not profit_activated:
                    drwLineZon(zone, 1-line_level,(i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                                   (255,150,255), strk = stroke)
                else:
                    drwLineZon(zone, 1-line_level,(i-offseta)/dpth,1-line_level,(i+offsetb)/dpth,
                                   (255,150,255), strk = stroke*2)

            if candle.label and candle.index%2 == line.static_variation%2:
                if candle.red:
                    x, y = fitPointZone(zone, 1-lwick+0.03,c0/dpth)
                else:
                    x, y = fitPointZone(zone, 1-hwick-0.03,c0/dpth)

                place_text(candle.label.upper(), y, x, base_col = col )


            if candle.index == line.initial_idx + line.test_idx:
                return True, col, 0, special_coord
            else:
                return None, None, None, None

        def fill_volume_bars(candles, minP, maxP):
            min_vol = min(candles, key = lambda _ : _.v).v
            max_vol = max(candles, key = lambda _ : _.v).v

            p_delta = maxP - minP

            volume_bars = [[0,0] for _ in range(30)]

            for i, candle in enumerate(candles):
                higher_price = max(candle.o, candle.c)
                lower_price = min(candle.o, candle.c)
                high_idx = int(((higher_price - minP)/p_delta)*30)
                low_idx = int(((lower_price - minP)/p_delta)*30)

                num_bars = (high_idx - low_idx)+1
                fill_vol = candle.v/num_bars

                for bar_idx in range(low_idx, high_idx+1):
                    if bar_idx >= len(volume_bars) or bar_idx <=0:
                        continue
                    volume_bars[bar_idx][0] += fill_vol
                    if candle.green:
                        volume_bars[bar_idx][1] += fill_vol
                    else:
                        volume_bars[bar_idx][1] -= fill_vol

            max_vol_cumm = max(volume_bars, key = lambda _ : _[0])[0]
            min_vol_cumm = min(volume_bars, key = lambda _ : _[0])[0]
            vol_range_delta = max_vol_cumm - min_vol_cumm

            max_vol_pos = max([_ for _ in volume_bars if _[1]>=0], key = lambda _ : _[1], default = [0,1])[1]
            min_vol_pos = min([_ for _ in volume_bars if _[1]>=0], key = lambda _ : _[1], default = [0,0])[1]

            max_vol_neg = max([_ for _ in volume_bars if _[1]<0], key = lambda _ : _[1], default = [0,0])[1]
            min_vol_neg = min([_ for _ in volume_bars if _[1]<0], key = lambda _ : _[1], default = [0,-1])[1]

            pos_vol_range = max_vol_pos - min_vol_pos if max_vol_pos!=min_vol_pos else max_vol_pos 
            neg_vol_range = max_vol_neg - min_vol_neg if max_vol_neg != min_vol_neg else max_vol_neg

            normalize_abs = lambda _ : _/pos_vol_range if _ >= 0 else _/neg_vol_range

            volume_bars = [[(_[0] - min_vol_cumm)/vol_range_delta, normalize_abs(_[1])] for _ in volume_bars]

            return volume_bars


        def drawCandles(line, candles, zone,
                        minV, maxV, p1, p2,
                        entry=None, stop=None,
                        profit=None, idle = None, dpth = None):

            if not dpth:
                print("no candles provided")
                return []


            inter_color = lambda v1, v2, p: v1 + (v2-v1)*p
            interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                                       inter_color(col1[1], col2[1], percent),
                                                       inter_color(col1[2], col2[2], percent))

            volume_bars = fill_volume_bars(candles, minV, maxV) 
            price_range = maxV - minV

            part_of_screen = 1/8
            vol_strk = 32

            # if random.randint(0,10) < 2:
            #     part_of_screen = 1/4
            #     vol_strk = 12

            for i, volume_bar in enumerate(volume_bars):
                pr1 = fit_to_zon(((i+0.4)/30)*price_range + minV, minV, maxV)
                pr2 = fit_to_zon(((i+1-0.4)/30)*price_range + minV, minV, maxV)
                prm = (pr1+pr2)/2
                volume_rel = volume_bar[0]
                if volume_bar[1] >= 0:
                    col = colors.dark_green
                else:
                    col = colors.dark_red
                abs_fill = abs(volume_bar[1])
                col = interpolate(colors.white, col, abs_fill)


                drwLineZon(zone, 1-prm,(0),
                            1-prm,(volume_rel*part_of_screen),col, strk = vol_strk, out_line=False, ignore_spit = True)
                drwLineZon(zone, 1-prm,(1),
                            1-prm,(1-volume_rel*part_of_screen),col, strk = vol_strk, out_line=False, ignore_spit = True)


            special_ones = []

            for i, candle in enumerate(candles):
                if i == line.question_index-1 and not line.blink:
                    drwLineZon(zone, 1,(i+0.5)/len(candles),
                               0,(i+0.5)/len(candles),
                               colors.col_bt_down, strk = 6)

                last = i == len(candles)-1
                first = i == 0
                feedback = drawCandle(zone, candle, minV, maxV, p1, p2,
                           entry=entry, stop=stop, profit=profit, idle=idle,
                           last = last, first=first, dpth = DPTH)

                special, special_color, special_priority, special_w = feedback
                #if i >= line.question_index-1:
                    #special = None

                if special:
                    special_ones.append([candle, special_priority, special_color, special_w])

            return sorted(special_ones, key = lambda _ : _[1])

        def find_suitable_squares(candles, minV, maxV):
            initial_index = line.question_index-5
            selected_rects = []
            for front in range(initial_index, line.floating_offset+15, -5):
                i2 = front
                i1 = max(0, front - 5)
                max_high     = max(candles[i1:i2], key = lambda _ : _.h).h
                min_low      = min(candles[i1:i2], key = lambda _ : _.l).l

                max_high_rel = 1.0 - fit_to_zon(max_high, minV, maxV)
                min_low_rel  = 1.0 - fit_to_zon(min_low, minV, maxV)

                max_high_abs = H * max_high_rel
                min_low_abs  = H * min_low_rel

                w1 = (i1/VISUAL_PART)*W
                w2 = (i2/VISUAL_PART)*W
                wd = w2 - w1

                if not max_high_abs - H//8 < 0:
                    mh = max(max_high_abs - H//8 , max_high_abs - H//32)
                    mnh = min(max_high_abs - H//8 , max_high_abs - H//32)
                    selected_rects.append([mnh, w1+wd*0.35, mh, w1+wd*0.65])
                if not min_low_abs + H//8 > H:
                    mh = max(min_low_abs + H//8 , min_low_abs + H//32)
                    mnh = min(min_low_abs + H//8 , min_low_abs + H//32)
                    selected_rects.append([mnh, w1+wd*0.35, mh, w1+wd*0.65])

            return selected_rects

        candles = line.produce_candles()
        lines = line.produce_lines()
        high_tf_line = line.produce_high_tf_pattern()

        DPTH = len(candles) + 1
        PIXELS_PER_CANDLE = 10

        W = S.W
        H = S.H

        firstSquare  = [0,  0, H, W]
        minV, maxV = S.minMaxOfZon(candles)

        additional_squares = find_suitable_squares(candles, minV, maxV)

        entry, stop, profit = line.get_sltp()
        idle = line.idle_coursor
        if idle:
            idle_l = fit_to_zon(idle, minV, maxV)

        entry_activated =  line.entry_activated
        stop_activated = line.stop_activated
        profit_activated = line.profit_activated
        draw_tasks = []
        draw_tasks.append([candles, firstSquare])

        DPTH = len(candles)


        o1 = candles[0].index
        o2 = candles[-1].index

        inter_color = lambda v1, v2, p: v1 + (v2-v1)*p
        interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                                   inter_color(col1[1], col2[1], percent),
                                                   inter_color(col1[2], col2[2], percent))


        #HIGHER TIMEFRAME IN MINIATURE
        position_y_low = lambda _ : _*0.2
        position_y_high = lambda _ : _*0.2 + 0.75
        place_x_shift = lambda _ : (_)/(DPTH*(len(high_tf_line)/VISUAL_PART)/0.2) + 0.4

        place_y_shift = position_y_low

        if SPLIT_VIEW:
            avg_low = (candles[-4].l + candles[-3].l + candles[-2].l + candles[-1].l)/4
        else:
            avg_low = (candles[len(candles)//2].l + candles[len(candles)//2+1].l + candles[len(candles)//2-1].l)/3
        if avg_low < (minV+maxV)/2:
            place_y_shift = position_y_high 
        
        high_tf_overlay = False
        # if random.randint(0,10)<2:
        #     # x0 = (high_tf_line[0][0])/(DPTH*(len(high_tf_line)/VISUAL_PART)/0.2) + 0.4
        #     place_x_shift = lambda _ : _/(DPTH*(len(high_tf_line)/VISUAL_PART))
        #     place_y_shift = lambda _ : _
        #     high_tf_overlay = True

        if True:

            if line.static_variation%2==0 and not line.blink:
                thn_htf_ln = 10 if not high_tf_overlay else 10
                thk_htf_ln = 8 if not high_tf_overlay else 8
            else:
                thn_htf_ln = 5 if not high_tf_overlay else 10 
                thk_htf_ln = 4 if not high_tf_overlay else 8

            minH = min(high_tf_line, key = lambda _ : _[1])[1]
            maxH = max(high_tf_line, key = lambda _ : _[1])[1]

            yH = place_y_shift(fit_to_zon(minV, minH, maxH))
            yL = place_y_shift(fit_to_zon(maxV, minH, maxH))
            yE = None
            yP = None

            if line.entry:
                yE = place_y_shift(fit_to_zon(line.entry, minH, maxH))
            if line.tp:
                yP = place_y_shift(fit_to_zon(line.tp, minH, maxH))

            y1 = place_y_shift(fit_to_zon(high_tf_line[0][1], minH, maxH))
            y2 = place_y_shift(fit_to_zon(high_tf_line[-1][1], minH, maxH))
            x0 = place_x_shift(high_tf_line[0][0])
            x1 = place_x_shift(high_tf_line[0][0]+0.5)
            x2 = place_x_shift(high_tf_line[-1][0]+0.5)
            x3 = place_x_shift(high_tf_line[-1][0]+2)


            max_point = max(high_tf_line, key = lambda _ : _[1])
            ymx = place_y_shift(fit_to_zon(max_point[1], minH, maxH))
            xmx = place_x_shift(max_point[0])

            min_point = min(high_tf_line, key = lambda _ : _[1])
            ymn = place_y_shift(fit_to_zon(min_point[1], minH, maxH))
            xmn = place_x_shift(min_point[0])

            len_htf = len(high_tf_line)
            zone_border = int(len_htf*(1-1/HIGHER_TIMEFRAME_SCALE))

            rgb_col = interpolate(colors.col_bt_pressed,colors.col_wicked_lighter, abs(line.variation/40))
            if not high_tf_overlay:
                drwSqrZon(draw_tasks[0][1], 1-ymn,x0,1-ymx,x3,rgb_col, ignore_spit = True)

            xz = place_x_shift(high_tf_line[zone_border][0])

            col1 = colors.col_black
            col2 = colors.mid_color
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-y1,x0,1-y2,x3,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)
            col1 = colors.col_black
            col2 = colors.mid_color
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-ymn,xmn,1-ymx,xmx,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)

            col1 = colors.col_black
            col2 = colors.col_active_darker
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-ymx,xz,1-ymn,xz,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)

            col1 = colors.dark_red
            col2 = colors.white
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-ymx,xmx,1-y2,x3,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)
            col1 = colors.dark_green
            col2 = colors.white
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-y1,x0,1-ymx,xmx,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)

            col1 = colors.dark_green
            col2 = colors.white
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-ymn,xmn,1-y2,x3,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)
            col1 = colors.dark_red
            col2 = colors.white
            rgb_col = interpolate(col1, col2, abs(line.variation/40))
            drwLineZon(draw_tasks[0][1], 1-y1,x0,1-ymn,xmn,rgb_col, strk = thn_htf_ln, out_line=False, ignore_spit = True)

            for i,(p1, p2) in enumerate(zip(high_tf_line[:-1], high_tf_line[1:])):
                y1 = place_y_shift(fit_to_zon(p1[1], minH, maxH))
                y2 = place_y_shift(fit_to_zon(p2[1], minH, maxH))
                x0 = place_x_shift(p1[0]-2)
                x1 = place_x_shift(p1[0]+0.5)
                x2 = place_x_shift(p2[0]+0.5)
                x3 = place_x_shift(p2[0]+2)

                col1 = colors.white
                col2 = colors.col_black

                lower = min(p1[1], p2[1])
                upper = max(p1[1], p2[1])

                if minV >= lower and minV <= upper and maxV >=lower and maxV <= upper:
                    col2 = colors.mid_color
                elif minV >= lower and minV <= upper:
                    col2 = colors.dark_green
                elif maxV >= lower and maxV <= upper:
                    col2 = colors.dark_red

                if minV < lower and maxV > upper:
                    col2 = colors.feature_bg

                if yH >= y1 and yH <= y2:
                    drwLineZon(draw_tasks[0][1], 1-yH,x0,1-yH,x3,colors.col_black, strk = thn_htf_ln, out_line=False, ignore_spit = True)
                if yL >= y1 and yL <= y2:
                    drwLineZon(draw_tasks[0][1], 1-yL,x0,1-yL,x3,colors.col_black, strk = thn_htf_ln, out_line=False, ignore_spit = True)

                if high_tf_overlay:
                    continue

                if yE and yE >= y1 and yE <= y2:
                    drwLineZon(draw_tasks[0][1], 1-yE,x0,1-yE,x3,(150,255,150), strk = thk_htf_ln, out_line=False, ignore_spit = True)
                if yP and yP >= y1 and yP <= y2:
                    drwLineZon(draw_tasks[0][1], 1-yP,x0,1-yP,x3,(255,150,255), strk = thk_htf_ln, out_line=False, ignore_spit = True)

                if not line.static_variation%2==0 or line.blink:
                    rgb_col = interpolate(col1, col2, abs(line.variation/40))
                    drwLineZon(draw_tasks[0][1], 1-y1,x1,1-y2,x2,rgb_col, strk = thk_htf_ln, out_line=False, ignore_spit = True)


        # POINTER
        drwLineZon(draw_tasks[0][1],1,0.5+(1/64),
                   0,0.5+(1/64),
                   colors.col_bt_pressed, strk = 6, ignore_spit = True)

        # IF MODE == MOUSE
        #if line.mode == "QUESTION" and not line.burn_mode and line.idle_x:
        if line.mode == "QUESTION" and not line.burn_mode:
            # line_color = colors.col_bt_down
            # strk = 3
            # cross = 2/DPTH

            if line.letter_idx and not line.select_mode:
                place_text(line.letter_idx, W//2, H//2, base_col = (50,50,50),renderer = S.cyrillic_60 )
            elif line.select_mode:
                place_text("*", W//2, H//2, base_col = (50,50,50),renderer = S.cyrillic_60 )


            # if not line.initial_action_done:
            #     if line.initial_action == "ENTRY":
            #         line_color = (150,255,150)
            #         strk = 5
            #         cross += 4/DPTH
            #     if line.initial_action == "SL":
            #         strk = 5
            #         cross += 4/DPTH
            #         line_color = (255,150,150)

            # if not entry and not stop and not profit:
            #         drwLineZon(draw_tasks[0][1], 0.5,0.4,0.5,0.6,line_color, strk = strk, ignore_spit = True)

        special_lines = lines if line.mode!="QUESTION" or line.static_variation%3 == 0 else lines[1:]
        lines_stroke = 3 if not line.static_variation%3==0 and not line.blink else 5

        for special_line in special_lines:
            for i, (p1, p2) in enumerate(zip(special_line[:-1], special_line[1:])):
                y1 = fit_to_zon(p1[1], minV, maxV)
                y2 = fit_to_zon(p2[1], minV, maxV)
                x1 = (p1[0]-o1+0.5)/DPTH
                x2 = (p2[0]-o1+0.5)/DPTH
                if p2[1] < p1[1]:
                    rgb_col = interpolate(colors.mid_color, colors.dark_red, abs(line.variation/40))
                elif p2[1] > p1[1]:
                    rgb_col = interpolate(colors.dark_green, colors.mid_color, abs(line.variation/40))
                else:
                    rgb_col = interpolate(colors.white, colors.col_black, abs(line.variation/40))
                drwLineZon(draw_tasks[0][1], 1-y1,x1,1-y2,x2,rgb_col, strk = lines_stroke, out_line=False)
                if len(p1)>2:
                    delta = (max(p1[1], p2[1]) - min(p1[1], p2[1]))*0.3
                    y3 = fit_to_zon(p1[1]+delta, minV, maxV)
                    y4 = fit_to_zon(p2[1]+delta, minV, maxV)
                    drwLineZon(draw_tasks[0][1], 1-y3,x1,1-y4,x2,rgb_col, strk = lines_stroke, out_line=False)

        special_ones = []

        for d_task in draw_tasks:

            candles = d_task[0]
            zone = d_task[1]
            DPTH = len(candles)

            p1 = candles[0].index
            p2 = candles[-1].index

            minV, maxV = S.minMaxOfZon(candles)

            special_ones = drawCandles(line, candles, zone, minV, maxV, p1, p2, entry=entry, stop=stop, profit=profit, idle=idle, dpth = DPTH)

        trim_col = lambda _ : _ if _ <= 255 else 255
        dim_col = lambda _ : int((_*1.25))
        #special_ones = [_ for (i,_) in enumerate(special_ones) if i%line.static_variation==0]

        #if line.static_variation == 1:
            #special_ones = []

        for special_candle in special_ones[::-1]:

            if not additional_squares:
                break

            optimal_coord = special_candle[3]
            x0, y0 = special_candle[3]
            distance = lambda _ :(((_[3]+_[1])/2 - x0)**2 + ((_[2]+_[0])/2 - y0)**2)**0.5

            sp_zone =  min(additional_squares, key = distance)
            line_len = distance(sp_zone)
            #if line_len > W//10:
                #continue
            y1, x1, y2, x2 = sp_zone
            xm, ym = (x1+x2)/2, (y1+y2)/2

            if line.select_mode:
                drwZonBrdr(sp_zone)

            drawCircleSimple(x0, y0, 4, (250,250,250))
            drwLineSimple(xm, ym, x0, y0)
            candle = special_candle[0]
            col = special_candle[2]
            col = [trim_col(dim_col(_)) for _ in col]
            _minV = candle.l
            _maxV = candle.h
            p1 = candle.index
            p2 = candle.index
            drawCandle(sp_zone, candle, _minV, _maxV, p1, p2,
                        entry=entry, stop=stop, profit=profit, idle=idle,
                        predefined_color = col, dpth = 1, draw_special = True)
            additional_squares.remove(sp_zone)







######################################
### SIX MODE CONTROLLER
######################################

class KeyboardChainModel():
    def __init__(S):
        S.up = 'up'
        S.down = 'down'
        S.pressed = 'pressed'
        S.mapping = OrderedDict()
        S.mapping[backend.api().K_q]         = ["q",S.up]
        S.mapping[backend.api().K_w]         = ["w",S.up]
        S.mapping[backend.api().K_e]         = ["e",S.up]
        S.mapping[backend.api().K_r]         = ["r",S.up]
        S.mapping[backend.api().K_t]         = ["t",S.up]
        S.mapping[backend.api().K_y]         = ["y",S.up]
        S.mapping[backend.api().K_u]         = ["u",S.up]
        S.mapping[backend.api().K_i]         = ["i",S.up]
        S.mapping[backend.api().K_o]         = ["o",S.up]
        S.mapping[backend.api().K_p]         = ["p",S.up]
        S.mapping[backend.api().K_a]         = ["a",S.up]
        S.mapping[backend.api().K_s]         = ["s",S.up]
        S.mapping[backend.api().K_d]         = ["d",S.up]
        S.mapping[backend.api().K_f]         = ["f",S.up]
        S.mapping[backend.api().K_g]         = ["g",S.up]
        S.mapping[backend.api().K_h]         = ["h",S.up]
        S.mapping[backend.api().K_j]         = ["j",S.up]
        S.mapping[backend.api().K_k]         = ["k",S.up]
        S.mapping[backend.api().K_l]         = ["l",S.up]
        S.mapping[backend.api().K_z]         = ["z",S.up]
        S.mapping[backend.api().K_x]         = ["x",S.up]
        S.mapping[backend.api().K_c]         = ["c",S.up]
        S.mapping[backend.api().K_v]         = ["v",S.up]
        S.mapping[backend.api().K_b]         = ["b",S.up]
        S.mapping[backend.api().K_n]         = ["n",S.up]
        S.mapping[backend.api().K_m]         = ["m",S.up]
        S.mapping[backend.api().K_SPACE]     = ["select",S.up]

        S.keys = [S.up for _ in range(27)]

    def process_button(S, current_state, new_state):
        if current_state == S.up and new_state == S.down:
            return S.down
        elif current_state == S.down and new_state == S.down:
            return S.down
        elif current_state == S.down and new_state == S.up:
            return S.pressed
        elif current_state == S.pressed and new_state == S.up:
            return S.up
        else:
            return S.up

    def prepare_inputs(S):
        S.keys = list(S.mapping.values())

    def get_inputs(S):
        keys = backend.api().key.get_pressed()

        for control_key in S.mapping:
            if keys[control_key]:
                S.mapping[control_key][1] = S.process_button(S.mapping[control_key][1], S.down)
            else:
                S.mapping[control_key][1] = S.process_button(S.mapping[control_key][1], S.up)

    def get_keys(S):
        S.get_inputs()
        S.prepare_inputs()
        return S.keys


class ChainedProcessor():
    def __init__(S, display_instance, ui_ref, data_label, data_path, beat_time = 1):
        S.W = W
        S.H = H
        S.producer = ChainedsProducer(data_label, data_path, meta_path = META_DIR,
                                      minor_meta = META_MINOR_DIR, meta_actions = META_ACTION, meta_actions_stack = META_ACTION_STACK,
                                      ui_ref = ui_ref, minor_images = IMAGES_MINOR_DIR)
        S.drawer = ChainedDrawer(display_instance, W, H)
        S.control = KeyboardChainModel()
        S.active_line = None
        S.display_instance = display_instance
        S.active_beat_time = beat_time
        S.time_elapsed_cummulative = 0
        S.ui_ref = ui_ref

        S.last_uid = None
        S.uid_changed = False
        S.last_positive = False

        S.active_entity = ChainedEntity(S.producer.produce_next_feature(),
                                           S.producer.produce_chain(),
                                           S.producer.chains,
                                           S.W, S.H)
        S.ui_ref.set_image(S.active_entity.chained_feature.ask_for_image())
        S.ui_ref.meta_text = ""
        S.ui_ref.global_progress = S.producer.chains.get_chains_progression()
        S.ui_ref.tiling = S.active_entity.main_title

    def add_line(S):

        line_swapped = False

        if S.active_entity:
            S.active_entity.register_answers()
            S.ui_ref.set_image(S.active_entity.chained_feature.ask_for_image())
            S.ui_ref.meta_text = ""
            S.ui_ref.global_progress = S.producer.chains.get_chains_progression()
            S.ui_ref.move_image = False

        if S.active_entity.mode == "SHOW":
            S.time_elapsed_cummulative = 0

            if KEYBOARD_MODE:
                S.active_entity.time_estemated *=2

            S.active_beat_time = (60*1000)/S.active_entity.time_estemated

            S.ui_ref.move_image = True
            S.ui_ref.show_mode = True
            if LAST_META:
                S.ui_ref.meta_text = LAST_META
        else:
            S.ui_ref.show_mode = False

        if S.active_entity.mode == "DONE":
            S.ui_ref.global_progress = S.producer.chains.get_chains_progression()

            S.active_entity = ChainedEntity(S.producer.produce_next_feature(),
                                               S.producer.produce_chain(), S.producer.chains,
                                               S.W, S.H)

            blink_activated = False
            if not TEST and S.active_entity.uid == S.last_uid and random.randint(0,10) > 9:
                S.ui_ref.blink = True
                blink_activated = True
                S.active_entity.mode = "SHOW"
                S.active_entity.blink = True
            else:
                S.ui_ref.blink = False

            S.ui_ref.set_image(S.active_entity.chained_feature.ask_for_image(forced = blink_activated))
            S.ui_ref.set_image("", minor = True)
            S.ui_ref.tiling = S.active_entity.main_title
            S.ui_ref.meta_text = ""
            S.ui_ref.move_image = False
            S.time_elapsed_cummulative = 0

            if blink_activated:
                S.active_entity.time_estemated /= 3

            S.active_beat_time = (60*1000)/S.active_entity.time_estemated


        return S.active_entity.time_estemated, S.producer.produce_meta(), S.producer.produce_meta_minor()


    def redraw(S):
        S.drawer.draw_line(S.active_entity)
        S.drawer.generateOCHLPicture(S.active_entity)

    def get_pressed(S, key_states):
        mark_pressed = lambda _ : _[0] if _[1] == "pressed" else ""
        return [mark_pressed(_) for _ in key_states]

    def get_feedback(S):
        global NEW_EVENT

        if LAST_EVENT == "POSITIVE" and NEW_EVENT:
            NEW_EVENT = False
            S.ui_ref.bg_color = colors.dark_green

            if random.randint(0,10) > 5 and HAPTIC_CORRECT_CMD:
                subprocess.Popen(["bash", HAPTIC_CORRECT_CMD])

            if S.last_positive and random.randint(0,10) > 5:
                rnd_image = S.producer.produce_minor_image()
                S.ui_ref.set_image(rnd_image, minor = True)

            S.last_positive = True

            if not S.active_entity or S.active_entity.uid == S.last_uid:
                return 0

            if S.active_entity and S.active_entity.burn_mode:
                return 0

            S.last_uid = S.active_entity.uid
            S.ui_ref.last_positive = True

            return 1

        elif LAST_EVENT == "ERROR" and NEW_EVENT:
            NEW_EVENT = False
            S.ui_ref.bg_color = colors.dark_red
            S.last_positive = False

            if random.randint(0,10) > 5 and HAPTIC_ERROR_CMD:
                subprocess.Popen(["bash", HAPTIC_ERROR_CMD])

            if not S.active_entity or S.active_entity.uid == S.last_uid:
                return 0

            if S.active_entity and S.active_entity.burn_mode:
                return 0

            S.last_uid = S.active_entity.uid
            S.ui_ref.last_positive = False
            return -1
        else:
            return 0

    def process_inputs(S, time_elapsed = 0):
        #if S.active_entity and not S.active_entity.burn_mode:
            #key_states = S.control.get_inputs_raw()
            #key_states = [False, False, False, False]
        #else:

        key_states = S.control.get_keys()

        if S.active_entity:
            S.drawer.display_keys(key_states, S.active_entity)

        pressed_keys = S.get_pressed(key_states)

        if S.active_entity and any(pressed_keys):
            S.active_entity.register_keys(pressed_keys,
                                             S.time_elapsed_cummulative / S.active_beat_time)
        elif S.active_entity:
            S.active_entity.register_keys(pressed_keys,
                                             S.time_elapsed_cummulative / S.active_beat_time,
                                             time_based = True)

        pressed_mouse = backend.api().mouse.get_pressed()
        if S.active_entity and any(pressed_mouse):
            S.active_entity.register_mouse(pressed_mouse)
        elif S.active_entity:
            S.active_entity.register_idle_mouse()


    def tick(S, beat_time, time_elapsed):

        S.time_elapsed_cummulative += time_elapsed

        if S.active_entity:
            S.active_entity.tick(S.time_elapsed_cummulative, S.active_beat_time)

        S.process_inputs(time_elapsed)
        S.redraw()

        feedback = S.get_feedback()
        return feedback
