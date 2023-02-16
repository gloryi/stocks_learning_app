import random
import json
import os
import csv
from config import PROGRESSION_FILE, IMAGES_MAPPING_FILE
from config import VISUAL_PART, STAKE_PART
from config import HIGHER_TIMEFRAME_SCALE, MID_TIMEFRAME_SCALE
from config import GENERATION_TIME_SIZE
from config import TEST

knwon_prices = {}
dense_prices = {}
mid_prices = {}

class simpleCandle():
    def __init__(self, o, c, h, l, v, index = 0):
        self.o = o
        self.c = c
        self.h = h
        self.l = l
        self.v = v

        self.vRising = False
        self.vCount = 0
        self.index = index
        self.upper_pierce_line = max(self.o, self.c)
        self.lower_pierce_line = min(self.o, self.c)
        self.up_within_p1  = None
        self.up_within_p2 = None
        self.down_within_p1 = None
        self.down_within_p2 = None
        self.burn_ind = None
        self.to_offset = None
        self.to_price = None
        self.from_price = None

        self.green = self.c >= self.o     # green or red
        self.red = self.c < self.o        #
        self.is_same_color = False        # same color or not
        self.overhigh = False             # are overhigh
        self.overlow = False              # are overlow
        self.inner = False                # are candle inner
        self.pierce = False               # are candle pierce
        self.weak_pierce_prev = False     # are candle weak pierces prev
        self.weak_pierce_next = False     # are candle weak pierces next
        self.up_from_within = False       # are candles goes down from within
        self.down_from_within = False     # are candle goes up from within
        self.thick_upper = False          # upper wick taller or lower wick
        self.thick_lower = False          #

        self.upbreak = False
        self.downbreak = False
        self.no_sooner = index
        
    def ochl(self):
        return self.o, self.c, self.h, self.l

    def ochlv(self):
        return self.o, self.c, self.h, self.l, self.v

def extract_ochlv(filepath):
    O, C, H, L, V = [], [], [], [], []
    #O, C, H, L = [], [], [], []
    with open(filepath, "r") as ochlfile:
        reader = csv.reader(ochlfile)
        for line in reader:
            O.append(float(line[0])*100)
            C.append(float(line[1])*100)
            H.append(float(line[2])*100)
            L.append(float(line[3])*100)
            V.append(float(line[4])*100)

    return O,C,H,L,V

def fetch_prices(asset_name):
    global knwon_prices
    global dense_prices
    global mid_prices
    # global mid_prices_2
    O, C, H, L, V = extract_ochlv(asset_name)
    #O, C, H, L = extract_ochl(asset_name)
    knwon_prices[asset_name] = [simpleCandle(o,c,h,l,v,i) for i, (o,c,h,l,v) in enumerate(zip(O,C,H,L,V))]

    candles = knwon_prices[asset_name]

    condensed = []
    for i in range(HIGHER_TIMEFRAME_SCALE,len(candles),HIGHER_TIMEFRAME_SCALE):
        O = candles[i-HIGHER_TIMEFRAME_SCALE].o
        C = candles[i-1].c
        H = max(candles[i-HIGHER_TIMEFRAME_SCALE:i], key = lambda _ : _.h).h
        L = min(candles[i-HIGHER_TIMEFRAME_SCALE:i], key = lambda _ : _.l).l
        V = sum(_.v for _ in candles[i-HIGHER_TIMEFRAME_SCALE:i])
        I = candles[i-1].index
        condensed.append(simpleCandle(O,C,H,L,V,I))

    dense_prices[asset_name] = condensed

    candles = knwon_prices[asset_name]

    condensed = []
    for i in range(MID_TIMEFRAME_SCALE,len(candles),MID_TIMEFRAME_SCALE):
        O = candles[i-MID_TIMEFRAME_SCALE].o
        C = candles[i-1].c
        H = max(candles[i-MID_TIMEFRAME_SCALE:i], key = lambda _ : _.h).h
        L = min(candles[i-MID_TIMEFRAME_SCALE:i], key = lambda _ : _.l).l
        V = sum(_.v for _ in candles[i-MID_TIMEFRAME_SCALE:i])
        I = candles[i-1].index
        condensed.append(simpleCandle(O,C,H,L,V,I))

    mid_prices[asset_name] = condensed

    candles = knwon_prices[asset_name]


def get_candles(asset_name, index):

    if asset_name not in knwon_prices:
        fetch_prices(asset_name)

    for candle in knwon_prices[asset_name][int(index)-(VISUAL_PART-GENERATION_TIME_SIZE):]:
        yield candle

def get_dense(asset_name, index):

    if asset_name not in dense_prices:
        fetch_prices(asset_name)

    initial_ind = max(0, (int(index)-(VISUAL_PART-GENERATION_TIME_SIZE)+VISUAL_PART) - VISUAL_PART*HIGHER_TIMEFRAME_SCALE)
    range_selector = filter(lambda _ : _.index >= initial_ind, dense_prices[asset_name])

    for candle in range_selector:
        yield candle

# def get_mid(asset_name, index):
#
#     if asset_name not in mid_prices:
#         fetch_prices(asset_name)
#
#     initial_ind = max(0, (int(index)-210+VISUAL_PART) - VISUAL_PART*MID_TIMEFRAME_SCALE)
#     range_selector = filter(lambda _ : _.index >= initial_ind, mid_prices[asset_name])
#
#     for candle in range_selector:
#         yield candle

class ChainUnitType():
    type_key = "type_key"
    type_feature = "type_feature"
    mode_open =  "mode_open"
    mode_question =  "mode_question"
    mode_active_question = "mode_active_question"
    mode_hidden = "mode_hidden"
    mode_highligted = "mode_highligted"
    extra_focus = "extra_focus"
    position_subtitle = "position_subtitle"
    position_features = "position_features"
    position_keys = "position_keys"
    font_cyrillic = "font_cyrillic"
    font_utf = "font_utf"
    font_short_utf = "font_short_utf"

class ChainUnit():
    def __init__(self,
                 text,
                 type = None,
                 mode = None,
                 position = None,
                 order_no = None,
                 extra = None,
                 preferred_position = None,
                 font = ChainUnitType.font_utf):

        self.text = text
        self.type = type
        self.mode = mode
        self.position = position
        self.order_no = order_no
        self.font = font
        self.preferred_position = preferred_position
        self.extra = extra

burn_keys = {}
burn_keys["LONG"] = 0
burn_keys["LONG P"] = 1
burn_keys["SHORT P"] = 2
burn_keys["SHORT"] = 3

class ChainedFeature():
    def __init__(self, source, start_point):

        self.source = source
        self.start_point = start_point
        self.candles = self.pre_process_candles()
        self.dense_candles = self.pre_process_candles(get_dense(source, start_point), only_visual = True)
        #self.mid_candles = self.pre_process_candles(get_mid(source, start_point), only_visual = True)
        #for i in range(len(self.mid_candles)):
            #self.mid_candles[i].index = i


        self.feature_level = 0

        self.is_burning = False
        self.burn_level = 0
        self.burn_key = burn_keys["LONG"]
        self.burn_ind = None

        self.set_burn_answer()

        self.feature_errors = []
        self.cummulative_error = 0
        self.decreased = False
        self.rised = False
        self.attached_image = "" 
        self.basic_timing_per_level = {0:45,
                                       1:45,
                                       2:45}
    def pre_process_candles(self, source = None, only_visual = False):

        if not source:
            candles_generator = get_candles(self.source, self.start_point)
        else:
            candles_generator = source

        candles = []
        index_shift = 0
        limit = VISUAL_PART + STAKE_PART if not only_visual else VISUAL_PART

        in_out_queue = []

        for candle in candles_generator:
            candle.index -= index_shift

            if len(candles) >= limit:
                break

            if candles and len(candles) < VISUAL_PART:

                upper_next, lower_next = max(candle.o, candle.c), min(candle.o, candle.c)
                upper_prev, lower_prev = max(candles[-1].o, candles[-1].c), min(candles[-1].o, candles[-1].c)

                if candles[-1].green == candle.green:
                    candle.is_same_color = True

                if candle.h - upper_next > lower_next - candle.l:
                    candle.thick_upper = True

                elif candle.h - upper_next < lower_next - candle.l:
                    candle.thick_lower = True
                
                if candles[-1].h > candle.h and candles[-1].l < candle.l:
                    candles[-1].weak_pierce_next = True

                if candle.h > candles[-1].h and candle.l < candles[-1].l:
                    candle.weak_pierce_prev = True

                if candle.v > candles[-1].v:
                    candle.vCount = candles[-1].vCount+1
                    if candle.vCount >= 2:
                        candle.vRising = True
                else:
                    candle.vCount = 0

                high_delta = candle.h - candles[-1].h
                low_delta = candles[-1].l - candle.l

                if high_delta >= 0 and low_delta < 0:
                    candle.overhigh = True

                elif low_delta >=0 and high_delta < 0:
                    candle.overlow = True

                elif high_delta >=0 and low_delta >=0:
                    if abs(high_delta) > abs(low_delta):
                        candle.overhigh = True
                    else:
                        candle.overlow = True
                
                if upper_next <= upper_prev and lower_next >= lower_prev:
                    candle.inner = True
                
                if upper_prev <= upper_next and lower_prev >= lower_next:
                    candle.pierce = True
                    candle.upper_pierce_line = max(candles[-1].o, candles[-1].c)
                    candle.lower_pierce_line = min(candles[-1].o, candles[-1].c)

                if upper_next > upper_prev and lower_next > lower_prev and lower_next < upper_prev:
                    candle.up_from_within = True
                    candle.up_within_p1 = upper_prev
                    candle.up_within_p2 = upper_next

                if lower_next < lower_prev and upper_next < upper_prev and upper_next > lower_prev:
                    candle.down_from_within = True
                    candle.down_within_p1 = lower_prev
                    candle.down_within_p2 = lower_next


                for to_check in in_out_queue[::-1]:
                    if upper_next > to_check.h:
                        to_check.upbreak = True
                        to_check.no_sooner = candle.index
                    if lower_next < to_check.l:
                        to_check.downbreak = True
                        to_check.no_sooner = candle.index


            in_out_queue = list(filter(lambda _ : not _.upbreak and not _.downbreak, in_out_queue))

            candles.append(candle)

        return candles

    def set_burn_answer(self):
        decision_candle = self.candles[VISUAL_PART-1]

        anchor = (decision_candle.c+decision_candle.o)/2
        anchor_i = VISUAL_PART-1

        min_low = min(decision_candle.o, decision_candle.c)
        min_low_i = VISUAL_PART-1
        max_high = max(decision_candle.o, decision_candle.c)
        max_high_i = VISUAL_PART-1
        
        for i, candle in enumerate(self.candles[VISUAL_PART:]):
            if candle.h > max_high:
                max_high = candle.h
                max_high_i = i + VISUAL_PART
            elif candle.l < min_low:
                min_low = candle.l
                min_low_i = i + VISUAL_PART

        low_range = anchor - min_low
        high_range = max_high - anchor
        low_first = min_low_i < max_high_i

        if high_range > low_range and min_low > decision_candle.l:
            self.burn_key = burn_keys["LONG"] 
            self.candles[VISUAL_PART-1].to_offset = (max_high_i - anchor_i)
            self.candles[VISUAL_PART-1].to_price = max_high
            self.candles[VISUAL_PART-1].from_price = self.candles[VISUAL_PART-1].l
            self.candles[VISUAL_PART-1].burn_flag = "LONG"
            self.burn_ind = VISUAL_PART-1

        elif low_range > high_range and max_high < decision_candle.h:
            self.burn_key = burn_keys["SHORT"]
            self.candles[VISUAL_PART-1].to_offset = (min_low_i - anchor_i)
            self.candles[VISUAL_PART-1].from_price = self.candles[VISUAL_PART-1].h
            self.candles[VISUAL_PART-1].to_price = min_low
            self.candles[VISUAL_PART-1].burn_flag = "SHORT"
            self.burn_ind == VISUAL_PART-1

        elif low_first:
            self.burn_key = burn_keys["LONG P"] 
            self.candles[min_low_i].to_offset = (max_high_i - min_low_i)
            self.candles[min_low_i].from_price = self.candles[min_low_i].l
            self.candles[min_low_i].to_price = max_high
            self.candles[min_low_i].burn_flag = "LONG P"
            self.burn_ind = min_low_i

        else:
            self.burn_key = burn_keys["SHORT P"]
            self.candles[max_high_i].to_offset = (min_low_i - max_high_i)
            self.candles[max_high_i].from_price = self.candles[max_high_i].h
            self.candles[max_high_i].to_price = min_low
            self.candles[max_high_i].burn_flag = "SHORT P"
            self.burn_ind = max_high_i


    def get_question_candles(self):
        return self.candles[:VISUAL_PART]

    #def get_mid_candles(self):
        #return self.mid_candles[:]

    def set_burn_mode(self):
        self.is_burning = True
        self.burn_level = 0

    def burn_one(self, positive = False):
        if not positive:
            self.burn_level -= 1
            if self.burn_level < 0:
                self.burn_level = 0
        else:
            self.burn_level += 1

        if self.burn_level == 2:
            self.burn_level = 0
            self.is_burning = False

    def get_question_candles_minmax(self):
        min_price = min(self.candles[:VISUAL_PART], key = lambda _ : _.l).l
        max_price = max(self.candles[:VISUAL_PART], key = lambda _ : _.h).h
        return min_price, max_price

    def get_resulting_candles(self):
        return self.candles[STAKE_PART:]

    def get_candles_with_offset(self, offset_a, offset_b):
        return self.candles[offset_a:offset_a+offset_b]

    def get_lines_with_offset(self, offset_a, offset_b):
        selected_candles = self.candles[offset_a:offset_a+offset_b]
        special_lines = []
        
        high_low_line = []
        horisontals = []

        last_high = False
        for i, candle in enumerate(selected_candles):
            if candle.overhigh:
                if not last_high or not high_low_line:
                    high_low_line.append([candle.index, candle.h])
                    last_high = True
                    if len(high_low_line) > 6: 
                        if high_low_line[-4][1] > high_low_line[-6][1] and high_low_line[-4][1] > high_low_line[-2][1]:
                            del high_low_line[-4]
                            high_low_line[-4].append(2)
                elif candle.h > high_low_line[-1][1]:
                    high_low_line[-1] = [candle.index, candle.h]
                    last_high = True
                
            elif candle.overlow:
                if last_high or not high_low_line:
                    high_low_line.append([candle.index, candle.l])
                    high_low_line[-1] = [candle.index, candle.l]
                    last_high = False
                    if len(high_low_line) > 6: 
                        if high_low_line[-4][1] < high_low_line[-6][1] and high_low_line[-4][1] < high_low_line[-1][1]:
                            del high_low_line[-4]
                            high_low_line[-4].append(2)
                elif candle.l < high_low_line[-1][1]:
                    high_low_line[-1] = [candle.index, candle.l]
                    last_high = False

        special_lines.append(high_low_line)

        for i1, p1 in enumerate(high_low_line[::4]):
            for i2, p2 in enumerate(high_low_line):
                if p2[0] - p1[0] <= 3 or p2[0] - p1[0] >= 50:
                    continue

                p3 =  high_low_line[i2-1] 
                miv = min(p2[1], p3[1])
                mxv = max(p2[1], p3[1])

                if p1[1] >= miv and p1[1] <= mxv:

                    if (mxv-miv)!=0:
                        v_perce = (p1[1]-miv)/(mxv-miv) 
                    else:
                        v_perce = 1

                    if p3[1] < p2[1]:
                        I2 = p3[0]+(v_perce*(p2[0]-p3[0]))
                    else:
                        I2 = p2[0]-(v_perce*(p2[0]-p3[0]))

                    horisontals.append([[p1[0], p1[1]], [I2, p1[1]]])
                    break

        special_lines += horisontals

        return special_lines

    def get_high_tf_context(self):
        selected_candles = self.dense_candles 
        high_low_line = []
        last_high = False
        for i, candle in enumerate(selected_candles):
            if candle.overhigh:
                if not last_high or not high_low_line:
                    high_low_line.append([len(high_low_line), candle.h])
                    last_high = True
                    if len(high_low_line) > 6: 
                        if high_low_line[-4][1] > high_low_line[-6][1] and high_low_line[-4][1] > high_low_line[-2][1]:
                            del high_low_line[-4]
                elif candle.h > high_low_line[-1][1]:
                    high_low_line[-1] = [len(high_low_line)-1, candle.h]
                    last_high = True
                
            elif candle.overlow:
                if last_high or not high_low_line:
                    high_low_line.append([len(high_low_line), candle.l])
                    last_high = False
                    if len(high_low_line) > 6: 
                        if high_low_line[-4][1] < high_low_line[-6][1] and high_low_line[-4][1] < high_low_line[-1][1]:
                            del high_low_line[-4]
                elif candle.l < high_low_line[-1][1]:
                    high_low_line[-1] = [len(high_low_line)-1, candle.l]
                    last_high = False

        return high_low_line


    def get_all_candles(self):
        return self.candles

    def set_mode(self, unit_type):
        if self.feature_level == 0:
            return ChainUnitType.mode_open
        elif self.feature_level >= 1 and unit_type == ChainUnitType.type_feature:
            return ChainUnitType.mode_question
        else:
            return ChainUnitType.mode_open

    def ask_for_image(self, forced=False):
        if self.attached_image and self.feature_level <2 or forced:
            return self.attached_image
        else:
            return None


    def set_extra(self, unit_type):
        return ChainUnitType.extra_focus

    def get_timing(self):
        return self.basic_timing_per_level[self.feature_level]

    def register_error(self):
        self.feature_errors[0] += 1
        self.cummulative_error += 1

    def decrease_errors(self):
        if self.cummulative_error > 1:
            self.cummulative_error //= 2
        else:
            self.cummulative_error = 0

        if self.feature_errors[0] >1:
            self.feature_errors[0] //= 2
        else:
            self.feature_errors[0] = 0


    def get_main_title(self):
        return self.source

    def register_progress(self, is_solved = False):
        timing = self.basic_timing_per_level[self.feature_level]
        level = self.feature_level
        if is_solved:
            self.basic_timing_per_level[self.feature_level] = timing +3 if timing < 80 else 80 
            self.feature_level = level + 1 if level < 2 else 2 
            self.rised = True
            self.decreased = False
        else:
            self.basic_timing_per_level[self.feature_level] = timing -3 if timing > 40 else 40 
            self.feature_level = level -1 if level > 0 else 0 
            self.decreased = True
            self.rised = False

    def select(self):
        self.rised = False
        self.decreased = False

    def deselect(self):
        self.rised = False
        self.decreased = False

    def get_features_len(self):
        return len(self.keys)

    def __repr__(self):
        return f"{self.source[-10:]}~{self.start_point} | progress = {self.feature_level} | errors = {self.cummulative_error} | burn = {self.burn_level}"


class FeaturesChain():
    def __init__(self, chain_no, features):
        self.chain_no = chain_no
        self.features = features

        self.progression_level = 0
        self.errors_mapping = [[0 for _ in range(10)] for j in range(5)]
        self.max_error = 0
        self.cummulative_error = 0
        self.fresh_errors = 0
        self.last_review_urge = 0
        self.active_position = -1
        self.ascended = False
        self.again = False

    def ascend(self):
        for feature in self.features:
            # feature.progression_level = 4
            feature.feature_level = 2
            feature.deselect()

    def set_errors(self, errors_mapping):
        self.errors_mapping = errors_mapping
        for feature, feature_errors in zip(self.features, self.errors_mapping):
            feature.feature_errors = feature_errors
            feature.cummulative_error = sum(feature_errors)
        self.max_error = max([max(feature.feature_errors, default=0) for feature in self.features], default=0)
        self.cummulative_error = sum(sum(feature.feature_errors) for feature in self.features)

    def update_errors(self, register_new = False):
        if register_new:
            self.fresh_errors += 1

        for error_index, (feature, _) in enumerate(zip(self.features, self.errors_mapping)):
            self.errors_mapping[error_index] = feature.feature_errors
        self.max_error = max([max(feature.feature_errors, default = 0) for feature in self.features], default=0)
        self.cummulative_error = sum(sum(feature.feature_errors) for feature in self.features)

    def get_worst_features(self, features_no = 1):
        sorted_by_mistake = sorted(self.features,key = lambda _ : _.cummulative_error, reverse = True)
        return sorted_by_mistake[:features_no] 

    def initialize_images(self, images_list):
        #for image, feature in zip(images_list, self.features):
            #feature.attached_image = image
        for i, feature in enumerate(images_list):
            i2 = (i+1)%len(images_list)
            if i < len(self.features):
                self.features[i].attached_image = [images_list[i], images_list[i2]]
            else:
                break

    def check_active_changed(self):
        if self.active_changed:
            self.active_changed = False
            return True
        return False

    def get_next_feature(self):
        level = self.features[self.active_position].feature_level
        is_fallback = self.features[self.active_position].decreased
        is_up = self.features[self.active_position].rised
        if level == 0 and is_fallback:
            return self.features[self.active_position]
        if level == 1:
            return self.features[self.active_position]
        if level == 2 and not is_up:
            return self.features[self.active_position]
        
        self.features[self.active_position].deselect()
        self.active_position += 1
        if self.active_position >= len(self.features):
            self.active_position = 0
            if self.fresh_errors <= 3:
                self.progression_level += 1
            elif self.fresh_errors <= 6:
                self.again = True
                self.progression_level = self.progression_level
            else:
                self.progression_level -= 1
                self.again = True
                if self.progression_level < 0:
                    self.progression_level = 0

            self.fresh_errors = 0

            return None
        self.features[self.active_position].select()
        return self.features[self.active_position]

class ChainedModel():
    def __init__(self, chains):
        self.chains = chains
        self.active_chain = None
        self.old_limit = 1
        self.new_limit = 2
        self.mistakes_trigger = False
        self.mistakes_chain = []

        self.burning_chain = []
        self.burning_in_work = []
        self.burning_size = 5 
        self.burn_tick = 0

        is_restored = self.restore_results(PROGRESSION_FILE)

        if not is_restored:
            self.active_chain = self.get_active_chain()
            self.dump_results(PROGRESSION_FILE)
        else:
            self.change_active_chain()

        self.attach_images(IMAGES_MAPPING_FILE)

    def resample(self):

        if len(self.mistakes_chain) >= 5:
            self.mistakes_trigger = True

        for chain in self.chains:
            if chain.progression_level > 0:

                chain.last_review_urge = chain.last_review_urge - 1

        if self.old_limit:
            self.chains.sort(key = lambda _ : _.progression_level + _.last_review_urge * 0.25)
        else:
            random.shuffle(self.chains)
            self.chains.sort(key = lambda _ : _.progression_level)
            if not self.new_limit:

                self.old_limit = 2
                self.new_limit = 2
        self.dump_results(PROGRESSION_FILE)

    def add_mistake_chains(self):

        if not self.active_chain:
            return

        worst_features = self.active_chain.get_worst_features(features_no = 2)

        for feature in worst_features:
            if feature.cummulative_error == 0 or feature in self.mistakes_chain:
                continue
            self.mistakes_chain.append(feature)

        self.mistakes_chain.sort(key = lambda _ : _.cummulative_error, reverse = True)

    def change_active_chain(self):

        self.add_mistake_chains()

        self.resample()

        if self.mistakes_trigger:
            self.mistakes_trigger = False

            if len(self.mistakes_chain) > 5:
                mistakes_to_work, self.mistakes_chain = self.mistakes_chain[:5], self.mistakes_chain[5:]

                for mistake in mistakes_to_work:
                    mistake.decrease_errors()
                self.active_chain =  FeaturesChain(-1, mistakes_to_work)
                return

        self.active_chain = self.chains[0]

        if self.active_chain.last_review_urge < 0:
            self.old_limit -= 1
        else:
            self.new_limit -= 1

        self.active_chain.last_review_urge = 0
        self.active_chain.update_errors()

    def get_options_list(self, sample):
        options = [sample.text]
        for i in range(5):
            random_chain = random.choice(random.choice(self.chains).features)
            preferred_position = sample.preferred_position
            if sample.type == ChainUnitType.type_feature:
                if preferred_position == "MAIN_FEATURE":
                    selected = random_chain.start_point
                elif preferred_position is None or preferred_position >= len(random_chain.features):
                    selected = random.choice(random_chain.features)
                else:
                    selected = random_chain.features[preferred_position]
                options.append(selected)
        random.shuffle(options)
        return options

    def get_next_feature(self):

        self.burning_in_work = list(filter(lambda _: _.is_burning, self.burning_in_work))

        if self.burning_in_work:

            self.burn_tick += 1
            self.burn_tick %= 2
            if self.burn_tick == 0:
                random.shuffle(self.burning_in_work)

            return self.burning_in_work[-1]
        else:
            self.set_burning_in_work()

        if not self.active_chain:
            self.change_active_chain()

        next_feature = self.active_chain.get_next_feature()
        if not next_feature:
            if self.active_chain.again:
                self.active_chain.again = False
            else:
                self.change_active_chain()
            next_feature = self.active_chain.get_next_feature()

        if not next_feature in self.burning_chain:
            if random.randint(0,10)%3 == 0:
                self.burning_chain.append(next_feature)

        return next_feature

    def is_burning(self):
        return len(self.burning_chain) >= self.burning_size

    def set_burning_in_work(self):
        if self.is_burning():
            self.burning_in_work, self.burning_chain = self.burning_chain[:self.burning_size], self.burning_chain[self.burning_size:]

            for feature in self.burning_in_work:
                feature.set_burn_mode()

    def dump_results(self, progression_file):
        if TEST:
            return

        backup = {}
        for chain in self.chains:
            backup[chain.chain_no] = [chain.progression_level, chain.last_review_urge, chain.errors_mapping]
        with open(progression_file, "w") as current_progress:
            json.dump(backup, current_progress, indent=2)

    def attach_images(self, images_file):
        if os.path.exists(images_file):
            images = {}
            with open(images_file) as images_ordered:
                images = json.load(images_ordered)
            if images:
                for chain in self.chains:
                    if chain.chain_no in images:
                        chain.initialize_images(images[chain.chain_no])
                    else:
                        print(f"Chain {chain.chain_no} have no image prepared")

    def restore_results(self, progression_file):
        if os.path.exists(progression_file):
            progress = {}
            with open(progression_file) as saved_prgress:
                progress = json.load(saved_prgress)
            if progress:
                for chain in self.chains:
                    chain.progression_level = progress[chain.chain_no][0]
                    chain.last_review_urge = progress[chain.chain_no][1]
                    if chain.progression_level > 0:
                        chain.ascend()
                    errors_mapping = []
                    if len(progress[chain.chain_no]) == 2:
                        errors_mapping = [[0 for _ in range(10)] for j in range(5)]
                    else:
                        errors_mapping = progress[chain.chain_no][2]

                    chain.set_errors(errors_mapping)

            return True
        else:
            return False

    def get_chains_progression(self):
        minimal_level = min(self.chains, key = lambda _ : _.progression_level).progression_level
        mastered = len(list(filter(lambda _: _.progression_level > minimal_level, self.chains)))
        return f"{minimal_level}x {mastered}/{len(self.chains)}"


    def get_active_chain(self):

        return self.active_chain
