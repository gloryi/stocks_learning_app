from utils import raw_extracter 
from learning_model import ChainedFeature, FeaturesChain, ChainedModel, ChainUnit, ChainUnitType
from collections import OrderedDict
from math import sqrt
from itertools import compress, groupby
import random
import re
from config import W, H, CYRILLIC_FONT, CHINESE_FONT, VISUAL_PART, STAKE_PART, META_SCRIPT
from colors import col_bg_darker, col_wicked_darker
from colors import col_active_darker, col_bg_lighter
from colors import col_wicked_lighter, col_active_lighter
from colors import col_correct, col_error
import colors

LAST_EVENT = "POSITIVE"
NEW_EVENT = False
######################################
### DATA PRODUCER
######################################

class ChainedsProducer():
    def __init__(self, label, csv_path, meta_path = None, ui_ref = None):
        self.csv_path = csv_path
        self.label = label 
        self.meta_path = meta_path
        self.meta_lines = self.extract_meta(self.meta_path) if self.meta_path else []
        self.chains = self.prepare_data()
        self.active_chain = self.chains.get_active_chain()
        self.ui_ref = ui_ref
        self.is_changed = False

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
        self.is_changed = self.chains.is_changed
        
        return next_features_chain 

    def produce_meta(self):
        if self.meta_lines:
            return random.choice(self.meta_lines)
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
        self.chains = chains
        self.main_title = self.chained_feature.get_main_title() 
        self.context = sorted(self.chained_feature.get_context(), key = lambda _ : _.order_no)
        self.order_in_work = 0 
        
        self.pygame_instance = pygame_instance

        self.correct = False
        self.error = False

        self.mode = "QUESTION"
        
        self.feedback = None
        self.done = True
        self.time_perce_reserved = 0.0

        min_price, max_price = self.chained_feature.get_question_candles_minmax()
        self.question_pxls_to_price = lambda _y : min_price + (1 - (_y / self.H) ) * (max_price - min_price)

        self.entry = None
        self.sl = None
        self.tp = None
        self.idle_coursor = None
        self.entry_activated = None
        self.stop_activated = None
        self.profit_activated = None

        self.variation = 0
        self.variation_on_rise = True

        self.question_index = VISUAL_PART
        self.active_index = 0

        self.options = None
        self.active_question = None
        self.questions_queue = self.extract_questions()
        if self.questions_queue:
            self.time_estemated = self.chained_feature.get_timing() / (len(self.questions_queue)+1) 
            self.done = False
        else:
            self.time_estemated = self.chained_feature.get_timing() / (len(self.context) +1) 


    def extract_questions(self):
        questions = list(filter(lambda _ : _.mode == ChainUnitType.mode_question, self.context))
        if questions:
            self.active_question = questions[0]
            self.active_question.mode = ChainUnitType.mode_active_question
            self.generate_options()
        return questions

    def generate_options(self):
        if self.active_question:
            self.options = self.chains.get_options_list(self.active_question)

    def delete_options(self):
        self.options = [random.choice(["+++", "***", "###"]) for _ in range(6)]

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
                return False
            
            if triggered and within(self.tp, c):
                self.profit_activated = True
                LAST_EVENT = "POSITIVE"
                return True
                
        LAST_EVENT = "ERROR"

        return False

    def register_answers(self):
        if self.mode == "QUESTION":
            is_solved = self.check_sltp_hit()
            self.chained_feature.register_progress(is_solved = is_solved)

        if self.mode == "QUESTION":
            self.mode = "SHOW"
            self.question_index = VISUAL_PART - self.active_index

        elif self.mode == "SHOW":
            self.mode = "DONE"

        return False 

    def match_correct(self):
        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "POSITIVE"
        NEW_EVENT = True
        self.order_in_work += 1
        if self.questions_queue:
            self.questions_queue.pop(0)
            self.active_question.mode = ChainUnitType.mode_open

        if self.questions_queue:
            self.active_question.mode = ChainUnitType.mode_open
            self.active_question = self.questions_queue[0]
            self.generate_options()
        else:
            self.delete_options()
            self.active_question = None
            self.done = True
            self.order_in_work = 0

    def match_error(self):
        global LAST_EVENT
        global NEW_EVENT
        LAST_EVENT = "ERROR"
        NEW_EVENT = True

        self.generate_options()

    def tick(self, time_passed, time_limit):
        self.variate()
        active_position = int(time_passed/time_limit*STAKE_PART)
        self.active_index = active_position
        self.active_index_float = time_passed/time_limit*STAKE_PART
        if self.mode == "SHOW":
            self.question_index = VISUAL_PART - self.active_index 

    def register_keys(self, key_states, time_percent, time_based = False):
        if time_based:
            self.variate()

        if self.active_question and not time_based:
            self.time_perce_reserved = time_percent
            for i, key in enumerate(key_states):
                if key:
                    if self.options[i] == self.active_question.text:
                        self.match_correct()
                    else:
                        self.match_error()

        elif time_based and not self.active_question:
            time_p = time_percent

            if not self.done:
                self.time_perce_reserved = time_percent

            if self.done:
                time_p = (time_p - self.time_perce_reserved)/(1.0 - self.time_perce_reserved)

            n_pairs = len(self.context)
            pair_perce = 1/n_pairs

            pair_to_show = int(time_p/pair_perce)
            self.order_in_work = pair_to_show

    def register_mouse(self, mouse_poses):
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
        if self.mode == "QUESTION":
                mouse_position = self.pygame_instance.mouse.get_pos()
                self.idle_coursor = self.question_pxls_to_price(mouse_position[1])
        else:
            self.idle_coursor = self.question_pxls_to_price(int(H/STAKE_PART)*self.active_index_float)


    def get_sltp(self):
        return self.entry, self.sl, self.tp


    def produce_geometries(self):
        graphical_objects = []
        set_color = lambda _ : colors.col_active_lighter if _.extra else col_wicked_darker if _.type == ChainUnitType.type_key else colors.feature_text_col if _.type == ChainUnitType.type_feature  else colors.col_correct if _.mode == ChainUnitType.mode_highligted else colors.col_black 
        set_bg_color = lambda _ : colors.col_bt_down if _.extra else col_active_darker if _.type == ChainUnitType.type_key else colors.feature_bg 
        get_text  = lambda _ : _.text if self.done or _.mode == ChainUnitType.mode_open else "???"  if _.mode == ChainUnitType.mode_question else ""
        get_y_position = lambda _ : self.H//2 - self.H//4 + self.H//16 if _.position == ChainUnitType.position_subtitle else self.H//2 - self.H//16 if _.position == ChainUnitType.position_keys else self.H//2 + self.H//16
        set_font = lambda _ : ChainUnitType.font_cyrillic if not re.search(u'[\u4e00-\u9fff]', _.text) else ChainUnitType.font_utf
        set_size = lambda _ : 30 if not re.search(u'[\u4e00-\u9fff]', _.text) else 40

        set_font = lambda _ : ChainUnitType.font_cyrillic if not re.search(u'[\u4e00-\u9fff]', _) else ChainUnitType.font_utf
        set_size = lambda _ : 30 if not re.search(u'[\u4e00-\u9fff]', _) else 40

        return graphical_objects

    def produce_candles(self):
        if self.mode == "QUESTION":
            return self.chained_feature.get_question_candles()
        else:
            return self.chained_feature.get_candles_with_offset(self.active_index, VISUAL_PART)
                                                                 

    def variate(self):
        if self.variation_on_rise:
            self.variation += 1
        else:
            self.variation -= 1

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

    def display_keys(self, keys):
        pass

    def minMaxOfZone(self, candleSeq):
        minP = min(candleSeq, key = lambda _ : _.l).l
        maxP = max(candleSeq, key = lambda _ : _.h).h
        return minP, maxP

    def generateOCHLPicture(self, line):


        def drawSquareInZone(zone ,x1,y1,x2,y2, col, width=0):
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
                self.pygame_instance.draw.rect(self.display_instance,col,
                                               (Y1,X1,(Y2-Y1),(X2-X1)), width = width)
            except Exception as e:
                pass

        def drawCircleInZone(zone ,x1,y1,r,col, width=0):
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

        def drawLineInZone(zone ,x1,y1,x2,y2, col, thickness = 1):
            try:
                X = zone[0]
                Y = zone[1]
                dx = zone[2] - X
                dy = zone[3] - Y
                X1 = int(X + dx*x1)
                Y1 = int(Y + dy*y1)
                X2 = int(X + dx*x2)
                Y2 = int(Y + dy*y2)
                self.pygame_instance.draw.line(self.display_instance,col,
                                               (Y1,X1),(Y2,X2),thickness)
            except Exception as e:
                pass

        def hex_to_bgr(hx):
            hx = hx.lstrip('#')
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

        def getCandleCol(candle, v_rising = False, opposite_blend = False):

            base_line_color = colors.col_wicked_darker 
            inter_color = lambda v1, v2, p: v1 + (v2-v1)*p
            interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], percent),
                                                       inter_color(col1[1], col2[1], percent),
                                                       inter_color(col1[2], col2[2], percent))
            rgb_col = colors.white 

            if candle.green:
                if not opposite_blend:
                    rgb_col = interpolate(colors.green2, colors.green1, abs(line.variation/40))
                else:
                    rgb_col = interpolate(colors.mid_color,colors.green2, abs(line.variation/40))

            elif candle.red:
                rgb_col = colors.dark_red 
                if not opposite_blend:
                    rgb_col = interpolate(colors.red1, colors.red2, abs(line.variation/40))
                else:
                    rgb_col = interpolate(colors.mid_color, colors.red1, abs(line.variation/40))

            clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)

            if candle.green:
                rgb_col = (clip_color(rgb_col[0]),
                           clip_color(rgb_col[1]),
                           clip_color(rgb_col[2]))
            else:
                rgb_col = (clip_color(rgb_col[0]),
                           clip_color(rgb_col[1]),
                           clip_color(rgb_col[2]))

            return rgb_col 

        def fitTozone(val, minP, maxP):
            candleRelative =  (val-minP)/(maxP-minP)
            return candleRelative

        def drawCandle( zone, candle, minP,
                       maxP,
                       p1,
                       p2, entry = None, stop = None, profit = None, idle = None, v_rising = False, last = False):
            i = candle.index - p1
            if line.variation <= 0 and candle.ha and candle.green != candle.ha.green:
                col = getCandleCol(candle.ha, v_rising, opposite_blend=True)
            else:
                col = getCandleCol(candle, v_rising)

            _o,_c,_h,_l = candle.ochl()

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
                drawSquareInZone( zone, h_position,(i+0.5-0.55)/depth,l_position,(i+0.5+0.55)/depth,(colors.col_bg_darker))
            elif stop and stop > _l and stop < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if stop > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drawSquareInZone( zone, h_position,(i+0.5-0.55)/depth,l_position,(i+0.5+0.55)/depth,(colors.col_black))
            elif profit and profit > _l and profit < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if profit > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drawSquareInZone( zone, h_position,(i+0.5-0.55)/depth,l_position,(i+0.5+0.55)/depth,(colors.col_bt_pressed))
            elif idle and idle > _l and idle < _h:
                h_position, l_position = (1-hwick-candle_len//8, 1-body_mid_zone) if idle > body_mid else (1-body_mid_zone, 1-lwick+candle_len//8)
                drawSquareInZone( zone, h_position,(i+0.5-0.55)/depth,l_position,(i+0.5+0.55)/depth,(colors.col_wicked_darker))

            if line.variation >=0:
                upper, lower = max(oline, cline), min(oline, cline)

                drawLineInZone( zone, 1-lwick,(i+0.5)/depth,1-lower,(i+0.5)/depth,col,thickness=3)
                drawLineInZone( zone, 1-hwick,(i+0.5)/depth,1-lower,(i+0.5)/depth,col,thickness=3)

                drawSquareInZone( zone, 1-cline,(i+0.5-0.3)/depth,1-oline,(i+0.5+0.3)/depth,col, width = 0)

            else:
                upper, lower = max(oline, cline), min(oline, cline)
                thickness = 4 if candle.thick_lower else 2
                drawLineInZone( zone, 1-lwick,(i+0.5)/depth,1-lower,(i+0.5)/depth,col,thickness=thickness)
                thickness = 4 if candle.thick_upper else 2
                drawLineInZone( zone, 1-hwick,(i+0.5)/depth,1-lower,(i+0.5)/depth,col,thickness=thickness)

                if candle.inner:
                    drawLineInZone( zone, 1-cline,(i+0.5-0.3)/depth,1-oline,(i+0.5+0.3)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-cline,(i+0.5+0.3)/depth,1-oline,(i+0.5-0.3)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-cline,(i+0.5+0.3)/depth,1-cline,(i+0.5-0.3)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-oline,(i+0.5+0.3)/depth,1-oline,(i+0.5-0.3)/depth,col,thickness=3)

                    drawLineInZone( zone, 1-(oline),(i+0.5)/depth,1-oline,(i-0.5+0.3)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-(cline),(i+0.5)/depth,1-cline,(i-0.5+0.3)/depth,col,thickness=3)
                elif candle.pierce:
                    upper_p = fitTozone(candle.upper_pierce_line, minP, maxP)
                    lower_p = fitTozone(candle.lower_pierce_line, minP, maxP)
                    upper_b = max(oline, cline)
                    lower_b = min(oline, cline)
                    drawSquareInZone( zone, 1-upper_b,(i+0.5-0.3)/depth,1-upper_p,(i+0.5+0.3)/depth,col, width = 0)
                    drawSquareInZone( zone, 1-upper_p,(i+0.5)/depth,1-lower_p,(i+0.5+0.3)/depth,col, width = 0)
                    mid_p = (upper_p + lower_p)/2
                    drawLineInZone( zone, 1-(mid_p),(i-0.5+0.3)/depth,1-mid_p,(i+0.5+0.3)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-(upper_p),(i+0.5)/depth,1-upper_p,(i+0.5+0.5)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-(lower_p),(i+0.5)/depth,1-lower_p,(i+0.5+0.5)/depth,col,thickness=3)

                    drawSquareInZone( zone, 1-lower_p,(i+0.5-0.3)/depth,1-lower_b,(i+0.5+0.3)/depth,col, width = 0)
                # elif candle.conjoined:
                #     #drawSquareInZone( zone, 1-cline,(i+0.5-0.5)/depth,1-oline,(i+0.5+0.5)/depth,col, width = 2)
                #     for conjugate in candle.conjugates:
                #         c1, c1w, c2, c2w = conjugate
                #         c1 = fitTozone(c1, minP, maxP)
                #         c1w = fitTozone(c1w, minP, maxP)
                #         c2 = fitTozone(c2, minP, maxP)
                #         c2w = fitTozone(c2w, minP, maxP)
                #
                #         drawLineInZone( zone, 1-c1,(i+0.5-0.3)/depth,1-c1,(i+0.5+0.3)/depth,col,thickness=3)
                #         drawLineInZone( zone, 1-c2,(i+0.5-0.3)/depth,1-c2,(i+0.5+0.3)/depth,col,thickness=3)
                else:
                    mid_p = (cline + oline)/2
                    drawSquareInZone( zone, 1-cline,(i+0.5-0.3)/depth,1-oline,(i+0.5+0.3)/depth,col, width = 0)
                    drawLineInZone( zone, 1-(mid_p),(i+0.5-0.45)/depth,1-mid_p,(i+0.5+0.45)/depth,col,thickness=3)
                    
                if candle.weak_pierce_prev:
                    drawLineInZone( zone, 1-lwick,(i+0.5)/depth,1-lwick,(i-0.5)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-hwick,(i+0.5)/depth,1-hwick,(i-0.5)/depth,col,thickness=3)

                if candle.weak_pierce_next:
                    drawLineInZone( zone, 1-lwick,(i+0.5)/depth,1-lwick,(i+1.5)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-hwick,(i+0.5)/depth,1-hwick,(i+1.5)/depth,col,thickness=3)

                if candle.overhigh:
                    drawLineInZone( zone, 1-hwick+0.5/depth-1/depth,(i+0.5+0.15)/depth,1-hwick-0.5/depth-1/depth,(i+0.5)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-hwick+0.5/depth-1/depth,(i+0.5-0.15)/depth,1-hwick-0.5/depth-1/depth,(i+0.5)/depth,col,thickness=3)
                    #drawCircleInZone( zone, 1-hwick,(i+0.5)/depth,1/depth,col, width = 10)
                if candle.overlow:
                    drawLineInZone( zone, 1-lwick-0.5/depth+1/depth,(i+0.5+0.15)/depth,1-lwick+0.5/depth+1/depth,(i+0.5)/depth,col,thickness=3)
                    drawLineInZone( zone, 1-lwick-0.5/depth+1/depth,(i+0.5-0.15)/depth,1-lwick+0.5/depth+1/depth,(i+0.5)/depth,col,thickness=3)
                    # drawLineInZone( zone, 1-lwick-1/depth,(i+0.5)/depth,1-lwick,(i-0.5)/depth,col,thickness=3)
                    # drawLineInZone( zone, 1-lwick+1/depth,(i+0.5)/depth,1-lwick,(i-0.5)/depth,col,thickness=3)
                    #drawCircleInZone( zone, 1-lwick,(i+0.5)/depth,1/depth,col, width = 10)


                if candle.joined:
                    drawLineInZone( zone, 1-cline,(i+0.5-0.3)/depth,1-cline,(i+1.0+0.3)/depth,col,thickness=3)

            if idle and (idle>=_l and idle<=_h or last):
                line_level = fitTozone(idle, minP, maxP)
                drawLineInZone( zone, 1-line_level,(i-2)/depth,1-line_level,(i+2)/depth,
                               colors.col_wicked_darker, thickness = 2)

            if entry and (entry>=_l and entry <=_h or last):
                line_level = fitTozone(entry, minP, maxP)
                if not entry_activated:
                    drawLineInZone( zone, 1-line_level,
                                   (i-2)/depth,1-line_level,(i+2)/depth,
                                   (150,255,150), thickness = 2)
                else:
                    drawLineInZone( zone, 1-line_level,
                                   (i-2)/depth,1-line_level,
                                   (i+2)/depth,(150,255,150),
                                   thickness = 5)
            if stop and (stop>=_l and stop<=_h or last):
                line_level = fitTozone(stop, minP, maxP)
                if not stop_activated:
                    drawLineInZone( zone,
                                   1-line_level,(i-2)/depth,1-line_level,(i+2)/depth,
                                   (255,150,150), thickness = 2)
                else:
                    drawLineInZone( zone, 1-line_level,(i-2)/depth,1-line_level,(i+2)/depth,
                                   (255,150,150), thickness = 5)
            if profit and (profit >=_l and profit<=_h or last):
                line_level = fitTozone(profit, minP, maxP)
                if not profit_activated:
                    drawLineInZone( zone, 1-line_level,(i-2)/depth,1-line_level,(i+2)/depth,
                                   (255,150,255), thickness = 2)
                else:
                    drawLineInZone( zone, 1-line_level,(i-2)/depth,1-line_level,(i+2)/depth,
                                   (255,150,255), thickness = 5)



        def drawCandles(line, candles, zone, minV, maxV, p1, p2, entry=None, stop=None, profit=None, idle = None):

            prev_v = candles[0].v

            for i, candle in enumerate(candles):
                if i == line.question_index-1:
                    drawLineInZone( zone, 1,(i+0.5)/len(candles),0,(i+0.5)/len(candles),colors.col_bt_down, thickness = 6)
                v_rising = candle.v > prev_v
                prev_v = candle.v
                last = i == len(candles)-1
                drawCandle(zone, candle, minV, maxV, p1, p2, entry=entry, stop=stop, profit=profit, idle=idle, v_rising = v_rising, last = last)


        candles = line.produce_candles()

        depth = len(candles) + 1
        PIXELS_PER_CANDLE = 10

        W = self.W
        H = self.H

        firstSquare  = [0,  0, H, W]
        minV, maxV = self.minMaxOfZone(candles)
        entry, stop, profit = line.get_sltp()
        idle = line.idle_coursor

        entry_activated =  line.entry_activated
        stop_activated = line.stop_activated
        profit_activated = line.profit_activated
        draw_tasks = []
        draw_tasks.append([candles, firstSquare])


        for d_task in draw_tasks:

            candles = d_task[0]
            zone = d_task[1]
            depth = len(candles)

            p1 = candles[0].index
            p2 = candles[-1].index

            minV, maxV = self.minMaxOfZone(candles)
            drawCandles(line, candles, zone, minV, maxV, p1, p2, entry=entry, stop=stop, profit=profit, idle=idle)

        #drawSLTP(H, W, minV, maxV,
                 #firstSquare, entry=entry, stop=stop, profit=profit,
                 #entry_activated=entry_activated,
                 #stop_activated=stop_activated,
                 #profit_activated=profit_activated, idle = idle)

 
            

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
        self.mapping[self.pygame_instance.K_e]         = self.up
        self.mapping[self.pygame_instance.K_d]         = self.up
        self.mapping[self.pygame_instance.K_c]         = self.up
        self.mapping[self.pygame_instance.K_i]         = self.up
        self.mapping[self.pygame_instance.K_k]         = self.up
        self.mapping[self.pygame_instance.K_COMMA]     = self.up

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
        self.producer = ChainedsProducer(data_label, data_path, meta_path = META_SCRIPT, ui_ref = ui_ref)
        self.drawer = ChainedDrawer(pygame_instance, display_instance, W, H)
        self.control = KeyboardChainModel(pygame_instance)
        self.active_line = None
        self.pygame_instance = pygame_instance
        self.display_instance = display_instance
        self.active_beat_time = beat_time 
        self.time_elapsed_cummulative = 0
        self.ui_ref = ui_ref
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
            is_solved = self.active_entity.register_answers()
            self.ui_ref.set_image(self.active_entity.chained_feature.ask_for_image())
            self.ui_ref.meta_text = ""
            self.ui_ref.global_progress = self.producer.chains.get_chains_progression()

        if self.active_entity.mode == "SHOW":
            self.time_elapsed_cummulative = 0
            #self.ui_ref.meta_text = self.producer.produce_meta()

        if self.active_entity.mode == "DONE":
            self.ui_ref.set_image(self.active_entity.chained_feature.ask_for_image())
            self.ui_ref.global_progress = self.producer.chains.get_chains_progression()
            
            self.active_entity = ChainedEntity(self.producer.produce_next_feature(),
                                               self.producer.produce_chain(), self.producer.chains,
                                               self.pygame_instance, self.W, self.H)

            self.ui_ref.tiling = self.active_entity.main_title
            self.ui_ref.meta_text = "" 
            self.time_elapsed_cummulative = 0
            self.active_beat_time = (60*1000)/self.active_entity.time_estemated

        line_swapped = self.producer.is_changed

        return self.active_entity.time_estemated, line_swapped, self.producer.produce_meta()


    def redraw(self):
        self.drawer.draw_line(self.active_entity)
        self.drawer.generateOCHLPicture(self.active_entity)
    
    def get_pressed(self, key_states):
        mark_pressed = lambda _ : True if _ == "pressed" else False
        return [mark_pressed(_) for _ in key_states]

    def get_feedback(self):
        global NEW_EVENT
        if LAST_EVENT == "POSITIVE" and NEW_EVENT:
            self.ui_ref.bg_color = colors.dark_green
            NEW_EVENT = False
            return 1
        elif LAST_EVENT == "ERROR" and NEW_EVENT:
            NEW_EVENT = False
            self.ui_ref.bg_color = colors.dark_red
            return -1
        else:
            return 0

    def process_inputs(self, time_elapsed = 0):
        key_states = self.control.get_keys()
        self.drawer.display_keys(key_states)

        pressed_keys = self.get_pressed(key_states)

        if self.active_entity and any(pressed_keys):
            self.active_entity.register_keys(pressed_keys, self.time_elapsed_cummulative / self.active_beat_time)
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
