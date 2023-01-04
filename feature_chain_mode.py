from utils import raw_extracter 
from learning_model import ChainedFeature, FeaturesChain, ChainedModel, ChainUnit, ChainUnitType
from collections import OrderedDict
from math import sqrt
from itertools import compress, groupby
import random
import re
from config import W, H, CYRILLIC_FONT, CHINESE_FONT, VISUAL_PART, STAKE_PART, META_SCRIPT, META_MINOR
from colors import col_bg_darker, col_wicked_darker
from colors import col_active_darker, col_bg_lighter
from colors import col_wicked_lighter, col_active_lighter
from colors import col_correct, col_error
import colors  
import pygame.gfxdraw

LAST_EVENT = "POSITIVE"
NEW_EVENT = False
######################################
### DATA PRODUCER
######################################

class ChainedsProducer():
    def __init__(self, label, csv_path, meta_path = None, minor_meta = None, ui_ref = None):
        self.csv_path = csv_path
        self.label = label 
        self.meta_path = meta_path
        self.minor_meta = minor_meta
        self.meta_lines = self.extract_meta(self.meta_path) if self.meta_path else []
        self.minor_lines = self.extract_meta(self.minor_meta) if self.minor_meta else []
        self.chains = self.prepare_data()
        self.active_chain = self.chains.get_active_chain()
        self.ui_ref = ui_ref

    def extract_meta(self, meta_path):
        meta = []
        with open(meta_path, "r") as metafile:
            for line in metafile:
                meta.append(line[:-1].upper())
        return meta

    def prepare_data(self):
        data_extractor = raw_extracter(self.csv_path) 
        chains = []
        features = []
        for i, (source, start_line) in enumerate(data_extractor):
            features.append(ChainedFeature(source, start_line))
            if i%5==0:
                chains.append(FeaturesChain(str(i//5), features))
                features = []
        return ChainedModel(chains)

    def produce_chain(self):
        self.active_chain = self.chains.get_active_chain()
        return self.active_chain

    def produce_next_feature(self):
        next_features_chain = self.chains.get_next_feature()
        
        return next_features_chain 

    def produce_meta(self):
        if self.meta_lines:
            return random.choice(self.meta_lines)
        return ""

    def produce_meta_minor(self):
        if self.minor_lines:
            minor_idx = random.randint(0, len(self.minor_lines)-9)
            return self.minor_lines[minor_idx:minor_idx+8] 
        return ""


######################################
### ENTITIES HANDLER TEXT_AND_POSE
######################################


class ChainedEntity():
    def __init__(self,
                 chained_feature,
                 features_chain,
                 chains,
                 pygame_instance,
                 W,
                 H):

        self.W, self.H = W, H

        self.chained_feature = chained_feature
        self.features_chain = features_chain
        self.uid = chained_feature.source + str(chained_feature.start_point)
        self.iuid = chained_feature.start_point

        self.burn_mode = self.chained_feature.is_burning
        self.locked = False

        self.chains = chains
        self.main_title = self.chained_feature.get_main_title() 
        
        self.pygame_instance = pygame_instance

        self.correct = False
        self.error = False

        self.mode = "QUESTION"
        
        self.feedback = None
        self.done = True
        self.time_perce_reserved = 0.0

        min_price, max_price = self.chained_feature.get_question_candles_minmax()
        trading_range = max_price - min_price
        mnp = min_price - trading_range*0.05
        mxp = max_price + trading_range*0.05
        self.question_pxls_to_price = lambda _y : mnp + (1 - (_y / self.H) ) * (mxp - mnp)

        self.entry = None
        self.sl = None
        self.tp = None
        self.idle_coursor = None
        self.idle_x = None
        self.entry_activated = None
        self.stop_activated = None
        self.profit_activated = None

        self.variation = 0
        self.variation_on_rise = True
        self.constant_variations = random.sample([_ for _ in range(10)], 4)
        self.palette = random.choice(colors.palettes) 

        self.question_index = VISUAL_PART
        self.active_index = 0
        self.active_index_float = 0
        self.overflow = 0
        self.clean_overflow = 0

        if not self.burn_mode:
            self.time_estemated = self.chained_feature.get_timing() / 3
        else:
            self.time_estemated = self.chained_feature.get_timing() / 2



    def check_sltp_hit(self):
        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "POSITIVE"
        NEW_EVENT = True

        if not self.sl or not self.entry or not self.tp:
            return False
        candles = self.chained_feature.get_all_candles()
        triggered = False
        within = lambda price, candle: price <= candle.h and price >= candle.l
        for i, c in enumerate(candles[VISUAL_PART:]):
            if within(self.entry, c):
                self.entry_activated = True
                triggered = True

            if triggered and within(self.sl, c):
                self.stop_activated = True
                LAST_EVENT = "ERROR"

                if not self.burn_mode:
                    self.chained_feature.register_error()
                    self.features_chain.update_errors(register_new=True)

                return False
            
            if triggered and within(self.tp, c):
                self.profit_activated = True
                LAST_EVENT = "POSITIVE"
                return True
                
        LAST_EVENT = "ERROR"

        return False

    def register_answers(self):
        if self.mode == "QUESTION":
            if not self.burn_mode:
                is_solved = self.check_sltp_hit()
                self.chained_feature.register_progress(is_solved = is_solved)

        if self.mode == "QUESTION":
            self.mode = "SHOW"
            self.question_index = VISUAL_PART - self.active_index

        elif self.mode == "SHOW":
            self.mode = "DONE"

        return False 

    def match_error(self):
        if self.locked:
            return

        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "ERROR"
        NEW_EVENT = True
        self.locked = True

        if not self.burn_mode:
            self.chained_feature.register_error()
            self.features_chain.update_errors(register_new=True)
        else:
            self.chained_feature.burn_one(positive = False)


    def match_correct(self):
        if self.locked:
            return

        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "POSITIVE"
        NEW_EVENT = True
        self.locked = True

        if not self.burn_mode:
            self.chained_feature.register_error()
            self.features_chain.update_errors(register_new=True)
        else:
            self.chained_feature.burn_one(positive = True)


    def tick(self, time_passed, time_limit):
        self.variate()
        time_prece = time_passed/time_limit
        time_prece += 0.1
        if time_prece >= 1:
            time_prece = 1
        active_position = int(time_prece*STAKE_PART)
        self.active_index = active_position
        self.active_index_float = time_prece*STAKE_PART
        self.calculate_overflow()
        if self.mode == "SHOW":
            self.question_index = VISUAL_PART - self.active_index 

    def calculate_overflow(self):
        self.overflow = int((self.active_index_float - self.active_index)*4)
        self.clean_overflow = self.active_index_float - self.active_index


    def check_answer(self, keys):
        if len([_ for _ in keys if _]) > 1:
            self.match_error()

        for i, _ in enumerate(keys):
            if _ and i == self.chained_feature.burn_key:
                self.match_correct()
                return

        self.match_error()


    def register_keys(self, key_states, time_percent, time_based = False):
        if not time_based and self.burn_mode:
            self.check_answer(key_states)

        if time_based:
            self.variate()
            time_p = time_percent

            if not self.done:
                self.time_perce_reserved = time_percent

            if self.done:
                time_p = (time_p - self.time_perce_reserved)/(1.0 - self.time_perce_reserved)

    def register_mouse(self, mouse_poses):
        if self.burn_mode:
            return
        if self.mode == "QUESTION":
            mouse_position = self.pygame_instance.mouse.get_pos()
            LMB, RMB = 0, 2
            if mouse_poses[LMB]:
                self.entry = self.question_pxls_to_price(mouse_position[1])
        
            if mouse_poses[RMB]:
                self.sl = self.question_pxls_to_price(mouse_position[1])

            if self.entry and self.sl:
                risk = self.entry - self.sl
                reward = risk * 3
                self.tp = self.entry + reward

    def register_idle_mouse(self):
        if self.burn_mode:
            return
        if self.mode == "QUESTION":
                mouse_position = self.pygame_instance.mouse.get_pos()
                self.idle_coursor = self.question_pxls_to_price(mouse_position[1])
                self.idle_x = mouse_position[0] / W
        else:
            self.idle_coursor = self.question_pxls_to_price(int(H/STAKE_PART)*self.active_index_float)


    def get_sltp(self):
        return self.entry, self.sl, self.tp


    def produce_geometries(self):
        graphical_objects = []
        set_color = lambda _ : colors.col_active_lighter
        set_bg_color = lambda _ : colors.col_bt_down
        set_font = lambda _ : ChainUnitType.font_cyrillic
        set_size = lambda _ : 30


        options_x_corners = [W//2 - W//4, W//2 - W//8, W//2 + W//8, W//2 + W//4]
        options_y_corners = [H-50,      H-50,    H-50,  H-50]
        options_w = 200
        options_h = 50

        options = ["LONG", "LONG P", "SHORT P", "SHORT"]
        for i, (x1, y1) in enumerate(zip(options_x_corners, options_y_corners)):
            ctx = options[i]
            ctx_x = x1
            ctx_y = y1
            cx, cy = ctx_x + options_w//2, ctx_y + options_h//2
            ctx_w, ctx_h = options_w, options_h

            graphical_objects.append(WordGraphical(ctx,
                                                   cx,
                                                   cy,
                                                   set_color(ctx),
                                                   None,
                                                   font = set_font(ctx),
                                                   font_size = set_size(ctx)))

        return graphical_objects

    def produce_candles(self):
        if self.mode == "QUESTION":
            return self.chained_feature.get_question_candles()
        else:
            return self.chained_feature.get_candles_with_offset(self.active_index, VISUAL_PART)

    def produce_lines(self):
        if self.mode == "QUESTION":
            return self.chained_feature.get_lines_with_offset(0, VISUAL_PART)
        else:
            return self.chained_feature.get_lines_with_offset(self.active_index, VISUAL_PART)


                                                                 

    def variate(self):
        if self.variation_on_rise:
            self.variation += 1
        else:
            self.variation -= 1

        if self.variation == 0:
            if self.mode == "QUESTION":
                avaliable_numbers = [_ for _ in range(10) if _ not in self.constant_variations]
                self.constant_variations.append(random.choice(avaliable_numbers))
                self.constant_variations.pop(0)
            else:
                self.constant_variations = []


        if self.variation > 40:
            self.variation_on_rise = False
        elif self.variation < -40:
            self.variation_on_rise = True

    def fetch_feedback(self):
        to_return = self.feedback
        self.feedback = None
        return to_return

######################################
### LINES HANDLER GRAPHICS
######################################

class WordGraphical():
    def __init__(self, text, x, y, color, bg_color = (150,150,150),
                 font = ChainUnitType.font_utf,
                 font_size = None,
                 rect = [], transparent = False):
        self.rect = rect
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.bg_color = bg_color
        self.font = font
        self.font_size = font_size
        self.transparent = transparent

class ChainedDrawer():
    def __init__(self, pygame_instance, display_instance, W, H):
        self.pygame_instance = pygame_instance
        self.display_instance = display_instance
        self.W = W
        self.H = H
        self.cyrillic_30 = self.pygame_instance.font.Font(CYRILLIC_FONT, 30, bold = True)
        self.cyrillic_40 = self.pygame_instance.font.Font(CYRILLIC_FONT, 40, bold = True)
        self.cyrillic_60 = self.pygame_instance.font.Font(CYRILLIC_FONT, 60, bold = True)
        self.cyrillic_120 = self.pygame_instance.font.Font(CYRILLIC_FONT, 120, bold = True)

        self.utf_30 = self.pygame_instance.font.Font(CHINESE_FONT, 30, bold = True)
        self.utf_40 = self.pygame_instance.font.Font(CHINESE_FONT, 40, bold = True)
        self.utf_60 = self.pygame_instance.font.Font(CHINESE_FONT, 60, bold = True)
        self.utf_120 = self.pygame_instance.font.Font(CHINESE_FONT, 120, bold = True)


    def pick_font(self, font_type = ChainUnitType.font_utf, size = 40):
        if font_type == ChainUnitType.font_utf:
            if not size:
                return self.utf_30
            elif size <= 30:
                return self.utf_30
            elif size <= 40:
                return self.utf_40
            elif size <= 60:
                return self.utf_60
            else:
                return self.utf_120
        else:
            if not size:
                return self.cyrillic_30 
            elif size <= 30:
                return self.cyrillic_30
            elif size <= 40:
                return self.cyrillic_40
            elif size <= 60:
                return self.cyrillic_60
            else:
                return self.cyrillic_120

    def draw_line(self, line):

        if not line.burn_mode:
            return

        geometries = line.produce_geometries()
        color = (128,128,128)
        for geometry in geometries:
            message = geometry.text
            font = self.pick_font(geometry.font, geometry.font_size)

            if not geometry.transparent:
                text = font.render(message, True, geometry.color, geometry.bg_color)
            else:
                text = font.render(message, True, geometry.color)

            textRect = text.get_rect()
            textRect.center = (geometry.x, geometry.y)

            if geometry.rect:

                x, y, w, h = geometry.rect 
                self.pygame_instance.draw.rect(self.display_instance,
                                  (50,50,50),
                                  (x,y,w,h),
                                   width = 2)

            self.display_instance.blit(text, textRect)

    def display_keys(self, keys, line):
        
        if not line.burn_mode:
            return

        options_x_corners = [W//2 - W//4, W//2 - W//8, W//2 + W//8, W//2 + W//4]
        options_y_corners = [H-50,      H-50,    H-50,  H-50]
        options_w = 200
        options_h = 50

        for i, (x1, y1) in enumerate(zip(options_x_corners, options_y_corners)):
            key_state = keys[i]
            xc, yc = x1 + options_w / 2, y1 + options_h / 2

            color = (255,255,255)
            if key_state == "up":
                color = colors.col_bt_down if LAST_EVENT == "POSITIVE" else colors.col_error 
            elif key_state == "down":
                color = colors.col_bt_pressed if LAST_EVENT == "POSITIVE" else colors.col_active_lighter
            else:
                color = (0,150,100)

            self.pygame_instance.draw.rect(self.display_instance,
                                  color,
                                  (x1, y1, options_w, options_h), border_radius=15)

    def minMaxOfZon(self, candleSeq):
        minP = min(candleSeq, key = lambda _ : _.l).l
        maxP = max(candleSeq, key = lambda _ : _.h).h
        return minP, maxP

    def generateOCHLPicture(self, line):

        last_color = None


        def drwSqrZon(zone ,x1,y1,x2,y2, col, width=0):
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
                clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)
                lighter_col = [clip_color(col[0]*0.6), clip_color(col[1]*0.6), clip_color(col[2]*0.6)]
                self.pygame_instance.draw.line(self.display_instance,lighter_col,(Y1,X1),(Y1,X2),2)
                self.pygame_instance.draw.line(self.display_instance,lighter_col,(Y1,X2),(Y2,X2),2)
                self.pygame_instance.draw.line(self.display_instance,lighter_col,(Y2,X2),(Y2,X1),2)
                self.pygame_instance.draw.line(self.display_instance,lighter_col,(Y2,X1),(Y1,X1),2)
                self.pygame_instance.draw.rect(self.display_instance,col,
                                               (Y1,X1,(Y2-Y1),(X2-X1)), width = width)
            except Exception as e:
                pass

        def drawCircleInZon(zone ,x1,y1,r,col, width=0):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)
                self.pygame_instance.draw.circle(self.display_instance,col,
                                               (Y1,X1),r, width = width)
            except Exception as e:
                pass

        def drwLineZon(zone ,x1,y1,x2,y2, col, strk = 1):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)
                X2 = int(X + dx*x2)
                Y2 = int(Y + dy*y2)
                
                clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)
                lighter_col = [clip_color(col[0]*0.6), clip_color(col[1]*0.6), clip_color(col[2]*0.6)]
                self.pygame_instance.draw.line(self.display_instance,lighter_col,(Y1,X1),(Y2,X2),strk+1)
                self.pygame_instance.draw.line(self.display_instance,col,(Y1,X1),(Y2,X2),strk)

            except Exception as e:
                pass

        def hex_to_bgr(hx):
            hx = hx.lstrip('#')
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

        def getCandleCol(candle, v_rising = False, opposite_blend = False, fred = False, fgreen = False):

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

            if line.mode != "QUESTION":
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

        def fitTozone(val, minP, maxP):
            trading_range = maxP - minP
            mnp = minP-trading_range*0.05
            mxp = maxP+trading_range*0.05
            candleRelative =  (val-mnp)/(mxp-mnp)
            return candleRelative

        def drawCandle(zone, candle, minP, maxP, p1, p2,
                       entry = None, stop = None, profit = None, idle = None,
                       v_rising = False, last = False):
            i = candle.index - p1
            #if 0 in line.constant_variations and line.variation <= 0 and candle.ha and candle.green != candle.ha.green:
            #if False:
                #col = getCandleCol(candle.ha, v_rising, opposite_blend=True)
            #else:

            w0 = 0.5
            w1 = 0.25
            w2 = 0.4
            c0 = i+w0

            _o,_c,_h,_l = candle.ochl()

            two_random = lambda : (random.choice([_o, _c, _h, _l]), random.choice([_o, _c, _h, _l]))

            #if last and line.clean_overflow <=0.2:
                #if candle.red:
                    #_o = _o
                    #_h = random.choice([_o, _h])
                    #_l = random.choice([_o, _c, _l])
                    #_c = random.choice([_o, _c, _h, _l])
                #else:
                    #_o = _o
                    #_h = random.choice([_o, _c, _h])
                    #_l = random.choice([_o, _l])
                    #_c = random.choice([_o, _c, _h, _l])

            col = getCandleCol(candle, v_rising, fred=_o>_c,fgreen=_o<_c)

            oline = fitTozone(_o, minP, maxP)
            cline = fitTozone(_c, minP, maxP)
            lwick = fitTozone(_l, minP, maxP)
            hwick = fitTozone(_h, minP, maxP)

            
            candle_len = hwick - lwick
            candle_mid = (_h+_l)/2 
            body_mid = (_o+_c)/2
            candle_center = fitTozone(candle_mid, minP, maxP)
            body_mid_zone = fitTozone(body_mid, minP, maxP)

            if entry and entry >_l and entry < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if entry > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drwSqrZon(zone, h_position,(c0-0.55)/dpth,
                                       l_position,(c0+0.55)/dpth,(colors.col_bg_darker))
                w1 = 0.35
                w2 = 0.4
            elif stop and stop > _l and stop < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if stop > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drwSqrZon(zone, h_position,(c0-0.55)/dpth,
                                       l_position,(c0+0.55)/dpth,(colors.col_black))
                w1 = 0.35
                w2 = 0.4
            elif profit and profit > _l and profit < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if profit > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drwSqrZon(zone, h_position,(c0-0.55)/dpth,
                                       l_position,(c0+0.55)/dpth,(colors.col_bt_pressed))
                w1 = 0.35
                w2 = 0.4
            elif idle and idle > _l and idle < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if idle > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drwSqrZon(zone, h_position,(c0-0.55)/dpth,
                                       l_position,(c0+0.55)/dpth,(colors.col_wicked_darker))
                w1 = 0.35
                w2 = 0.4
            
            if candle.to_offset and candle.to_price and not line.mode == "QUESTION" and line.burn_mode:
                p_connected = fitTozone(candle.to_price, minP, maxP) 
                i_connected = candle.index + candle.to_offset - p1 

                drwLineZon(zone, 1-candle.from_price,(c0)/dpth,1-p_connected,(i_connected+w0)/dpth,line.palette[4],strk=10)


            if False:
                upper, lower = max(oline, cline), min(oline, cline)

                drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=3)
                drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=3)

                drwSqrZon(zone, 1-cline,(c0-w1)/dpth,
                                       1-oline,(c0+w1)/dpth,col, width = 0)

            else:
                upper, lower = max(oline, cline), min(oline, cline)

                if candle.thick_upper and 9 in line.constant_variations:
                    #drwLineZon(zone, 1-hwick,(c0+0.1)/dpth,1-hwick-0.3/dpth,(c0)/dpth,col,strk=2)
                    #hline = max(oline, cline)
                    #mline = (hwick+hline)/2
                    #drwLineZon(zone, 1-hwick,(c0)/dpth,1-mline,(c0-w1)/dpth,col,strk=2)
                    
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=2)
                    drwLineZon(zone, 1-hwick,(c0-0.15)/dpth,1-upper,(c0-0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-hwick,(c0+0.15)/dpth,1-upper,(c0+0.15)/dpth,col,strk=1)

                elif candle.thick_lower and 9 in line.constant_variations:
                    #lline = min(oline, cline)
                    #mline = (lwick+lline)/2
                    #drwLineZon(zone, 1-lwick,(c0)/dpth,1-mline,(c0+w1)/dpth,col,strk=2)
                    #drwLineZon(zone, 1-lwick,(c0-0.1)/dpth,1-lwick+0.3/dpth,(c0)/dpth,col,strk=2)
                    drwLineZon(zone, 1-lwick,(c0-0.15)/dpth,1-lower,(c0-0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-lwick,(c0+0.15)/dpth,1-lower,(c0+0.15)/dpth,col,strk=1)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=2)
                else:
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lower,(c0)/dpth,col,strk=2)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-upper,(c0)/dpth,col,strk=2)



                if candle.inner and 1 in line.constant_variations:

                    mid_p = (cline + oline)/2

                    drwLineZon(zone, 1-cline,(c0-w1)/dpth,1-oline,(c0+w1)/dpth,col,strk=1)
                    drwLineZon(zone, 1-cline,(c0+w1)/dpth,1-oline,(c0-w1)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(mid_p),(c0-w2)/dpth,1-mid_p,(c0+w2)/dpth,col,strk=1)

                    drwLineZon(zone, 1-cline,(c0+w1)/dpth,1-cline,(c0-w1)/dpth,col,strk=1)
                    drwLineZon(zone, 1-oline,(c0+w1)/dpth,1-oline,(c0-w1)/dpth,col,strk=1)
                    
                    #drwLineZon(zone, 1-oline,(c0+w1)/dpth,1-cline,(c0+w1)/dpth,col,strk=1)
                    #drwLineZon(zone, 1-oline,(c0-w1)/dpth,1-cline,(c0-w1)/dpth,col,strk=1)

                    drwLineZon(zone, 1-(oline),(c0)/dpth,1-oline,(i-w0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-(cline),(c0)/dpth,1-cline,(i-w0+w1)/dpth,col,strk=3)


                elif candle.pierce and 2 in line.constant_variations:
                    upper_p = fitTozone(candle.upper_pierce_line, minP, maxP)
                    lower_p = fitTozone(candle.lower_pierce_line, minP, maxP)
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

                    drwSqrZon(zone,1-lower_p,(c0-w1)/dpth,
                                   1-lower_b,(c0+w1)/dpth,col, width = 0)
                    drwSqrZon(zone,1-upper_p,(c0-w1)/dpth,
                                   1-upper_b,(c0+w1)/dpth,col, width = 0)

                elif candle.up_from_within and 0 in line.constant_variations:
                    upper_p = fitTozone(candle.up_within_p1, minP, maxP)
                    upper_b = max(oline, cline)
                    lower_b = min(oline, cline)

                    mid_1 = upper_p + (upper_b - upper_p)/4
                    mid_2 = upper_p + (upper_b - upper_p)/4*2
                    mid_3 = upper_p + (upper_b - upper_p)/4*3

                    drwSqrZon(zone, 1-lower_b,(c0-w1)/dpth,
                                           1-upper_p,(c0+w1)/dpth,col, width = 0)


                    drwLineZon(zone, 1-upper_b,(c0-w1)/dpth,1-upper_b,(c0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-upper_p,(c0-w1)/dpth,1-upper_b,(c0-w1)/dpth,col,strk=2)
                    drwLineZon(zone, 1-upper_p,(c0+w1)/dpth,1-upper_b,(c0+w1)/dpth,col,strk=2)

                    drwLineZon(zone, 1-mid_1,(c0-w2)/dpth,1-mid_1,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_2,(c0-w2)/dpth,1-mid_2,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_3,(c0-w2)/dpth,1-mid_3,(c0+w2)/dpth,col,strk=3)

                elif candle.down_from_within and 0 in line.constant_variations:
                    lower_p = fitTozone(candle.down_within_p1, minP, maxP)
                    lower_b = min(oline, cline)
                    upper_b = max(oline, cline)
                    mid_p = (lower_p+lower_b)/2

                    mid_1 = lower_p - (lower_p - lower_b)/4
                    mid_2 = lower_p - (lower_p - lower_b)/4*2
                    mid_3 = lower_p - (lower_p - lower_b)/4*3

                    drwSqrZon(zone, 1-upper_b,(c0-w1)/dpth,
                                           1-lower_p,(c0+w1)/dpth,col, width = 0)



                    drwLineZon(zone, 1-lower_b,(c0-w1)/dpth,1-lower_b,(c0+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-lower_p,(c0+w1)/dpth,1-lower_b,(c0+w1)/dpth,col,strk=2)
                    drwLineZon(zone, 1-lower_p,(c0-w1)/dpth,1-lower_b,(c0-w1)/dpth,col,strk=2)

                    drwLineZon(zone, 1-mid_1,(c0-w2)/dpth,1-mid_1,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_2,(c0-w2)/dpth,1-mid_2,(c0+w2)/dpth,col,strk=3)
                    drwLineZon(zone, 1-mid_3,(c0-w2)/dpth,1-mid_3,(c0+w2)/dpth,col,strk=3)


                else:
                    drwSqrZon(zone, 1-cline,(c0-w1)/dpth,
                                           1-oline,(c0+w1)/dpth,col, width = 0)
                    if 3 in line.constant_variations:
                        mid_p = (cline + oline)/2
                        drwLineZon(zone, 1-(mid_p),(c0-w2)/dpth,1-mid_p,(c0+w2)/dpth,col,strk=3)

                    
                if candle.weak_pierce_prev and 4 in line.constant_variations:
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lwick,(i-w0-w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-hwick,(i-w0-w1)/dpth,col,strk=3)

                if candle.weak_pierce_next and 5 in line.constant_variations:
                    drwLineZon(zone, 1-lwick,(c0)/dpth,1-lwick,(i+1.5+w1)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick,(c0)/dpth,1-hwick,(i+1.5+w1)/dpth,col,strk=3)

                if candle.overhigh and 6 in line.constant_variations:
                    #if candle.overhigh:
                    drwLineZon(zone, 1-hwick+0.5/dpth-1/dpth,(c0-0.15)/dpth,1-hwick-0.5/dpth-1/dpth,(c0)/dpth,col,strk=3)
                    drwLineZon(zone, 1-hwick+0.5/dpth-1/dpth,(c0+0.15)/dpth,1-hwick-0.5/dpth-1/dpth,(c0)/dpth,col,strk=3)

                if candle.overlow and 7 in line.constant_variations:
                #if candle.overlow:
                    drwLineZon(zone, 1-lwick-0.5/dpth+1/dpth,(c0-0.15)/dpth,1-lwick+0.5/dpth+1/dpth,(c0)/dpth,col,strk=3)
                    drwLineZon(zone, 1-lwick-0.5/dpth+1/dpth,(c0+0.15)/dpth,1-lwick+0.5/dpth+1/dpth,(c0)/dpth,col,strk=3)



            if idle and (idle>=_l and idle<=_h or last):
                line_level = fitTozone(idle, minP, maxP)
                drwLineZon(zone, 1-line_level,(i-2)/dpth,1-line_level,(i+2)/dpth,
                               colors.col_wicked_darker, strk = 2)

            if entry and (entry>=_l and entry <=_h or last):
                line_level = fitTozone(entry, minP, maxP)
                if not entry_activated:
                    drwLineZon(zone, 1-line_level,
                                   (i-2)/dpth,1-line_level,(i+2)/dpth,
                                   (150,255,150), strk = 2)
                else:
                    drwLineZon(zone, 1-line_level,
                                   (i-2)/dpth,1-line_level,
                                   (i+2)/dpth,(150,255,150),
                                   strk = 5)
            if stop and (stop>=_l and stop<=_h or last):
                line_level = fitTozone(stop, minP, maxP)
                if not stop_activated:
                    drwLineZon(zone,
                                   1-line_level,(i-2)/dpth,1-line_level,(i+2)/dpth,
                                   (255,150,150), strk = 2)
                else:
                    drwLineZon(zone, 1-line_level,(i-2)/dpth,1-line_level,(i+2)/dpth,
                                   (255,150,150), strk = 5)
            if profit and (profit >=_l and profit<=_h or last):
                line_level = fitTozone(profit, minP, maxP)
                if not profit_activated:
                    drwLineZon(zone, 1-line_level,(i-2)/dpth,1-line_level,(i+2)/dpth,
                                   (255,150,255), strk = 2)
                else:
                    drwLineZon(zone, 1-line_level,(i-2)/dpth,1-line_level,(i+2)/dpth,
                                   (255,150,255), strk = 5)



        def drawCandles(line, candles, zone,
                        minV, maxV, p1, p2,
                        entry=None, stop=None,
                        profit=None, idle = None):

            prev_v = candles[0].v

            for i, candle in enumerate(candles):
                if i == line.question_index-1:
                    drwLineZon(zone, 1,(i+0.5)/len(candles),0,(i+0.5)/len(candles),colors.col_bt_down, strk = 6)

                v_rising = candle.v > prev_v
                prev_v = candle.v
                last = i == len(candles)-1
                drawCandle(zone, candle, minV, maxV, p1, p2,
                           entry=entry, stop=stop, profit=profit, idle=idle,
                           v_rising = v_rising, last = last)


        candles = line.produce_candles()
        lines = line.produce_lines()

        dpth = len(candles) + 1
        PIXELS_PER_CANDLE = 10

        W = self.W
        H = self.H

        firstSquare  = [0,  0, H, W]
        minV, maxV = self.minMaxOfZon(candles)
        entry, stop, profit = line.get_sltp()
        idle = line.idle_coursor
        if idle:
            idle_l = fitTozone(idle, minV, maxV)

        entry_activated =  line.entry_activated
        stop_activated = line.stop_activated
        profit_activated = line.profit_activated
        draw_tasks = []
        draw_tasks.append([candles, firstSquare])

        dpth = len(candles)

        if line.mode == "QUESTION" and not line.burn_mode and line.idle_x:
            drwLineZon(draw_tasks[0][1], 1,line.idle_x,0,line.idle_x,colors.col_bt_down, strk = 2)
            drwLineZon(draw_tasks[0][1], 1-idle_l,line.idle_x-(2)/dpth,1-idle_l,line.idle_x+(2/dpth),colors.col_bt_down, strk = 2)

        o1 = candles[0].index
        o2 = candles[-1].index

        inter_color = lambda v1, v2, p: v1 + (v2-v1)*p
        interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                                   inter_color(col1[1], col2[1], percent),
                                                   inter_color(col1[2], col2[2], percent))

                #drwLineZon(draw_tasks[0][1], 1-y1,x1,1-y2,x2,colors.col_bt_down, strk = 10)


        
        for d_task in draw_tasks:

            candles = d_task[0]
            zone = d_task[1]
            dpth = len(candles)

            p1 = candles[0].index
            p2 = candles[-1].index

            minV, maxV = self.minMaxOfZon(candles)

            drawCandles(line, candles, zone, minV, maxV, p1, p2, entry=entry, stop=stop, profit=profit, idle=idle)

        if line.mode != "QUESTION":
            for special_line in lines:
                for p1, p2 in zip(special_line[:-1], special_line[1:]):
                    y1 = fitTozone(p1[1], minV, maxV)
                    y2 = fitTozone(p2[1], minV, maxV)
                    x1 = (p1[0]-o1+0.5)/dpth
                    x2 = (p2[0]-o1+0.5)/dpth
                    rgb_col = interpolate(colors.white, colors.col_black, abs(line.variation/40))
                    drwLineZon(draw_tasks[0][1], 1-y1,x1,1-y2,x2,rgb_col, strk = 2)
 
            

######################################
### SIX MODE CONTROLLER
######################################

class KeyboardChainModel():
    def __init__(self, pygame_instance):
        self.pygame_instance = pygame_instance
        self.up = 'up'
        self.down = 'down'
        self.pressed = 'pressed'
        self.mapping = OrderedDict()
        self.mapping[self.pygame_instance.K_d]         = self.up
        self.mapping[self.pygame_instance.K_f]         = self.up
        self.mapping[self.pygame_instance.K_j]         = self.up
        self.mapping[self.pygame_instance.K_k]         = self.up

        self.keys = [self.up for _ in range(6)]

    def process_button(self, current_state, new_state):
        if current_state == self.up and new_state == self.down:
            return self.down
        elif current_state == self.down and new_state == self.down:
            return self.down
        elif current_state == self.down and new_state == self.up:
            return self.pressed
        elif current_state == self.pressed and new_state == self.up:
            return self.up
        else:
            return self.up

    def prepare_inputs(self):
        self.keys = list(self.mapping.values())

    def get_inputs(self):
        keys = self.pygame_instance.key.get_pressed()
        for control_key in self.mapping:
            if keys[control_key]:
                self.mapping[control_key] = self.process_button(self.mapping[control_key], self.down)
            else:
                self.mapping[control_key] = self.process_button(self.mapping[control_key], self.up)
    
    def get_keys(self):
        self.get_inputs()
        self.prepare_inputs()
        return self.keys
                

class ChainedProcessor():
    def __init__(self, pygame_instance, display_instance, ui_ref, data_label, data_path, beat_time = 1):
        self.W = W
        self.H = H
        self.producer = ChainedsProducer(data_label, data_path, meta_path = META_SCRIPT, minor_meta = META_MINOR, ui_ref = ui_ref)
        self.drawer = ChainedDrawer(pygame_instance, display_instance, W, H)
        self.control = KeyboardChainModel(pygame_instance)
        self.active_line = None
        self.pygame_instance = pygame_instance
        self.display_instance = display_instance
        self.active_beat_time = beat_time 
        self.time_elapsed_cummulative = 0
        self.ui_ref = ui_ref

        self.last_uid = None
        self.uid_changed = False

        self.active_entity = ChainedEntity(self.producer.produce_next_feature(),
                                           self.producer.produce_chain(),
                                           self.producer.chains,
                                           self.pygame_instance, self.W, self.H)
        self.ui_ref.set_image(self.active_entity.chained_feature.ask_for_image())
        self.ui_ref.meta_text = ""
        self.ui_ref.global_progress = self.producer.chains.get_chains_progression()
        self.ui_ref.tiling = self.active_entity.main_title

    def add_line(self):

        line_swapped = False

        if self.active_entity:
            self.active_entity.register_answers()
            self.ui_ref.set_image(self.active_entity.chained_feature.ask_for_image())
            self.ui_ref.meta_text = ""
            self.ui_ref.global_progress = self.producer.chains.get_chains_progression()
            self.ui_ref.move_image = False

        if self.active_entity.mode == "SHOW":
            self.time_elapsed_cummulative = 0
            self.ui_ref.move_image = True

        if self.active_entity.mode == "DONE":
            self.ui_ref.global_progress = self.producer.chains.get_chains_progression()
            
            self.active_entity = ChainedEntity(self.producer.produce_next_feature(),
                                               self.producer.produce_chain(), self.producer.chains,
                                               self.pygame_instance, self.W, self.H)

            self.ui_ref.set_image(self.active_entity.chained_feature.ask_for_image())
            self.ui_ref.tiling = self.active_entity.main_title
            self.ui_ref.meta_text = "" 
            self.ui_ref.move_image = False
            self.time_elapsed_cummulative = 0
            self.active_beat_time = (60*1000)/self.active_entity.time_estemated


        return self.active_entity.time_estemated, self.producer.produce_meta(), self.producer.produce_meta_minor()


    def redraw(self):
        self.drawer.draw_line(self.active_entity)
        self.drawer.generateOCHLPicture(self.active_entity)
    
    def get_pressed(self, key_states):
        mark_pressed = lambda _ : True if _ == "pressed" else False
        return [mark_pressed(_) for _ in key_states]

    def get_feedback(self):
        global NEW_EVENT

        if LAST_EVENT == "POSITIVE" and NEW_EVENT:
            NEW_EVENT = False
            self.ui_ref.bg_color = colors.dark_green

            if not self.active_entity or self.active_entity.uid == self.last_uid:
                return 0

            if self.active_entity and self.active_entity.burn_mode:
                return 0

            self.last_uid = self.active_entity.uid
            return 1
        elif LAST_EVENT == "ERROR" and NEW_EVENT:
            NEW_EVENT = False
            self.ui_ref.bg_color = colors.dark_red

            if not self.active_entity or self.active_entity.uid == self.last_uid:
                return 0

            if self.active_entity and self.active_entity.burn_mode:
                return 0

            self.last_uid = self.active_entity.uid
            return -1
        else:
            return 0

    def process_inputs(self, time_elapsed = 0):
        key_states = self.control.get_keys()

        if self.active_entity:
            self.drawer.display_keys(key_states, self.active_entity)

        pressed_keys = self.get_pressed(key_states)

        if self.active_entity and any(pressed_keys):
            self.active_entity.register_keys(pressed_keys,
                                             self.time_elapsed_cummulative / self.active_beat_time)
        elif self.active_entity:
            self.active_entity.register_keys(pressed_keys,
                                             self.time_elapsed_cummulative / self.active_beat_time, 
                                             time_based = True)

        pressed_mouse = self.pygame_instance.mouse.get_pressed()
        if self.active_entity and any(pressed_mouse):
            self.active_entity.register_mouse(pressed_mouse)
        elif self.active_entity:
            self.active_entity.register_idle_mouse()


    def tick(self, beat_time, time_elapsed):

        self.time_elapsed_cummulative += time_elapsed
         
        if self.active_entity:
            self.active_entity.tick(self.time_elapsed_cummulative, self.active_beat_time)

        self.process_inputs(time_elapsed)
        self.redraw()

        feedback = self.get_feedback()
        return feedback
