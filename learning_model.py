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
    def __init__(S, o, c, h, l, v, index = 0):
        S.o = o
        S.c = c
        S.h = h
        S.l = l
        S.v = v

        S.vRising = False
        S.vCount = 0
        S.index = index
        S.upper_pierce_line = max(S.o, S.c)
        S.lower_pierce_line = min(S.o, S.c)
        S.up_within_p1  = None
        S.up_within_p2 = None
        S.down_within_p1 = None
        S.down_within_p2 = None
        S.burn_ind = None
        S.to_offset = None
        S.to_price = None
        S.from_price = None

        S.green = S.c >= S.o     # green or red
        S.red = S.c < S.o        #
        S.is_same_color = False        # same color or not
        S.overhigh = False             # are overhigh
        S.overlow = False              # are overlow
        S.inner = False                # are candle inner
        S.pierce = False               # are candle pierce
        S.weak_pierce_prev = False     # are candle weak pierces prev
        S.weak_pierce_next = False     # are candle weak pierces next
        S.up_from_within = False       # are candles goes down from within
        S.down_from_within = False     # are candle goes up from within
        S.thick_upper = False          # upper wick taller or lower wick
        S.thick_lower = False          #

        S.upbreak = False
        S.downbreak = False
        S.no_sooner = index
        
    def ochl(S):
        return S.o, S.c, S.h, S.l

    def ochlv(S):
        return S.o, S.c, S.h, S.l, S.v

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
    def __init__(S,
                 text,
                 type = None,
                 mode = None,
                 position = None,
                 order_no = None,
                 extra = None,
                 preferred_position = None,
                 font = ChainUnitType.font_utf):

        S.text = text
        S.type = type
        S.mode = mode
        S.position = position
        S.order_no = order_no
        S.font = font
        S.preferred_position = preferred_position
        S.extra = extra

burn_keys = {}
burn_keys["LONG"] = 0
burn_keys["LONG P"] = 1
burn_keys["SHORT P"] = 2
burn_keys["SHORT"] = 3

class ChainedFeature():
    def __init__(S, source, start_point):

        S.source = source
        S.start_point = start_point
        S.candles = S.pre_process_candles()
        S.dense_candles = S.pre_process_candles(get_dense(source, start_point), only_visual = True)
        #S.mid_candles = S.pre_process_candles(get_mid(source, start_point), only_visual = True)
        #for i in range(len(S.mid_candles)):
            #S.mid_candles[i].index = i


        S.feature_level = 0

        S.is_burning = False
        S.burn_level = 0
        S.burn_key = burn_keys["LONG"]
        S.burn_ind = None

        S.set_burn_answer()

        S.feature_errors = []
        S.cummulative_error = 0
        S.decreased = False
        S.rised = False
        S.attached_image = "" 
        S.basic_timing_per_level = {0:45,
                                       1:45,
                                       2:45}
    def pre_process_candles(S, source = None, only_visual = False):

        if not source:
            candles_generator = get_candles(S.source, S.start_point)
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

    def set_burn_answer(S):
        decision_candle = S.candles[VISUAL_PART-1]

        anchor = (decision_candle.c+decision_candle.o)/2
        anchor_i = VISUAL_PART-1

        min_low = min(decision_candle.o, decision_candle.c)
        min_low_i = VISUAL_PART-1
        max_high = max(decision_candle.o, decision_candle.c)
        max_high_i = VISUAL_PART-1
        
        for i, candle in enumerate(S.candles[VISUAL_PART:]):
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
            S.burn_key = burn_keys["LONG"] 
            S.candles[VISUAL_PART-1].to_offset = (max_high_i - anchor_i)
            S.candles[VISUAL_PART-1].to_price = max_high
            S.candles[VISUAL_PART-1].from_price = S.candles[VISUAL_PART-1].l
            S.candles[VISUAL_PART-1].burn_flag = "LONG"
            S.burn_ind = VISUAL_PART-1

        elif low_range > high_range and max_high < decision_candle.h:
            S.burn_key = burn_keys["SHORT"]
            S.candles[VISUAL_PART-1].to_offset = (min_low_i - anchor_i)
            S.candles[VISUAL_PART-1].from_price = S.candles[VISUAL_PART-1].h
            S.candles[VISUAL_PART-1].to_price = min_low
            S.candles[VISUAL_PART-1].burn_flag = "SHORT"
            S.burn_ind == VISUAL_PART-1

        elif low_first:
            S.burn_key = burn_keys["LONG P"] 
            S.candles[min_low_i].to_offset = (max_high_i - min_low_i)
            S.candles[min_low_i].from_price = S.candles[min_low_i].l
            S.candles[min_low_i].to_price = max_high
            S.candles[min_low_i].burn_flag = "LONG P"
            S.burn_ind = min_low_i

        else:
            S.burn_key = burn_keys["SHORT P"]
            S.candles[max_high_i].to_offset = (min_low_i - max_high_i)
            S.candles[max_high_i].from_price = S.candles[max_high_i].h
            S.candles[max_high_i].to_price = min_low
            S.candles[max_high_i].burn_flag = "SHORT P"
            S.burn_ind = max_high_i


    def get_question_candles(S):
        return S.candles[:VISUAL_PART]

    #def get_mid_candles(S):
        #return S.mid_candles[:]

    def set_burn_mode(S):
        S.is_burning = True
        S.burn_level = 0

    def burn_one(S, positive = False):
        if not positive:
            S.burn_level -= 1
            if S.burn_level < 0:
                S.burn_level = 0
        else:
            S.burn_level += 1

        if S.burn_level == 2:
            S.burn_level = 0
            S.is_burning = False

    def get_question_candles_minmax(S):
        min_price = min(S.candles[:VISUAL_PART], key = lambda _ : _.l).l
        max_price = max(S.candles[:VISUAL_PART], key = lambda _ : _.h).h
        return min_price, max_price

    def get_resulting_candles(S):
        return S.candles[STAKE_PART:]

    def get_candles_with_offset(S, offset_a, offset_b):
        return S.candles[offset_a:offset_a+offset_b]

    def get_lines_with_offset(S, offset_a, offset_b):
        selected_candles = S.candles[offset_a:offset_a+offset_b]
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

    def get_high_tf_context(S):
        selected_candles = S.dense_candles 
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


    def get_all_candles(S):
        return S.candles

    def set_mode(S, unit_type):
        if S.feature_level == 0:
            return ChainUnitType.mode_open
        elif S.feature_level >= 1 and unit_type == ChainUnitType.type_feature:
            return ChainUnitType.mode_question
        else:
            return ChainUnitType.mode_open

    def ask_for_image(S, forced=False):
        if S.attached_image and S.feature_level <2 or forced:
            return S.attached_image
        else:
            return None


    def set_extra(S, unit_type):
        return ChainUnitType.extra_focus

    def get_timing(S):
        return S.basic_timing_per_level[S.feature_level]

    def register_error(S):
        S.feature_errors[0] += 1
        S.cummulative_error += 1

    def decrease_errors(S):
        if S.cummulative_error > 1:
            S.cummulative_error //= 2
        else:
            S.cummulative_error = 0

        if S.feature_errors[0] >1:
            S.feature_errors[0] //= 2
        else:
            S.feature_errors[0] = 0


    def get_main_title(S):
        return S.source

    def register_progress(S, is_solved = False):
        timing = S.basic_timing_per_level[S.feature_level]
        level = S.feature_level
        if is_solved:
            S.basic_timing_per_level[S.feature_level] = timing +3 if timing < 80 else 80 
            S.feature_level = level + 1 if level < 2 else 2 
            S.rised = True
            S.decreased = False
        else:
            S.basic_timing_per_level[S.feature_level] = timing -3 if timing > 40 else 40 
            S.feature_level = level -1 if level > 0 else 0 
            S.decreased = True
            S.rised = False

    def select(S):
        S.rised = False
        S.decreased = False

    def deselect(S):
        S.rised = False
        S.decreased = False

    def get_features_len(S):
        return len(S.keys)

    def __repr__(S):
        return f"{S.source[-10:]}~{S.start_point} | progress = {S.feature_level} | errors = {S.cummulative_error} | burn = {S.burn_level}"


class FeaturesChain():
    def __init__(S, chain_no, features):
        S.chain_no = chain_no
        S.features = features

        S.progression_level = 0
        S.errors_mapping = [[0 for _ in range(10)] for j in range(5)]
        S.max_error = 0
        S.cummulative_error = 0
        S.fresh_errors = 0
        S.last_review_urge = 0
        S.active_position = -1
        S.ascended = False
        S.again = False

    def ascend(S):
        for feature in S.features:
            # feature.progression_level = 4
            feature.feature_level = 2
            feature.deselect()

    def set_errors(S, errors_mapping):
        S.errors_mapping = errors_mapping
        for feature, feature_errors in zip(S.features, S.errors_mapping):
            feature.feature_errors = feature_errors
            feature.cummulative_error = sum(feature_errors)
        S.max_error = max([max(feature.feature_errors, default=0) for feature in S.features], default=0)
        S.cummulative_error = sum(sum(feature.feature_errors) for feature in S.features)

    def update_errors(S, register_new = False):
        if register_new:
            S.fresh_errors += 1

        for error_index, (feature, _) in enumerate(zip(S.features, S.errors_mapping)):
            S.errors_mapping[error_index] = feature.feature_errors
        S.max_error = max([max(feature.feature_errors, default = 0) for feature in S.features], default=0)
        S.cummulative_error = sum(sum(feature.feature_errors) for feature in S.features)

    def get_worst_features(S, features_no = 1):
        sorted_by_mistake = sorted(S.features,key = lambda _ : _.cummulative_error, reverse = True)
        return sorted_by_mistake[:features_no] 

    def initialize_images(S, images_list):
        #for image, feature in zip(images_list, S.features):
            #feature.attached_image = image
        for i, feature in enumerate(images_list):
            i2 = (i+1)%len(images_list)
            if i < len(S.features):
                S.features[i].attached_image = [images_list[i], images_list[i2]]
            else:
                break

    def check_active_changed(S):
        if S.active_changed:
            S.active_changed = False
            return True
        return False

    def get_next_feature(S):
        level = S.features[S.active_position].feature_level
        is_fallback = S.features[S.active_position].decreased
        is_up = S.features[S.active_position].rised
        if level == 0 and is_fallback:
            return S.features[S.active_position]
        if level == 1:
            return S.features[S.active_position]
        if level == 2 and not is_up:
            return S.features[S.active_position]
        
        S.features[S.active_position].deselect()
        S.active_position += 1
        if S.active_position >= len(S.features):
            S.active_position = 0
            if S.fresh_errors <= 3:
                S.progression_level += 1
            elif S.fresh_errors <= 6:
                S.again = True
                S.progression_level = S.progression_level
            else:
                S.progression_level -= 1
                S.again = True
                if S.progression_level < 0:
                    S.progression_level = 0

            S.fresh_errors = 0

            return None
        S.features[S.active_position].select()
        return S.features[S.active_position]

class ChainedModel():
    def __init__(S, chains):
        S.chains = chains
        S.active_chain = None
        S.old_limit = 1
        S.new_limit = 2
        S.mistakes_trigger = False
        S.mistakes_chain = []

        S.burning_chain = []
        S.burning_in_work = []
        S.burning_size = 5 
        S.burn_tick = 0

        is_restored = S.restore_results(PROGRESSION_FILE)

        if not is_restored:
            S.active_chain = S.get_active_chain()
            S.dump_results(PROGRESSION_FILE)
        else:
            S.change_active_chain()

        S.attach_images(IMAGES_MAPPING_FILE)

    def resample(S):

        if len(S.mistakes_chain) >= 5:
            S.mistakes_trigger = True

        for chain in S.chains:
            if chain.progression_level > 0:

                chain.last_review_urge = chain.last_review_urge - 1

        if S.old_limit:
            S.chains.sort(key = lambda _ : _.progression_level + _.last_review_urge * 0.25)
        else:
            random.shuffle(S.chains)
            S.chains.sort(key = lambda _ : _.progression_level)
            if not S.new_limit:

                S.old_limit = 2
                S.new_limit = 2
        S.dump_results(PROGRESSION_FILE)

    def add_mistake_chains(S):

        if not S.active_chain:
            return

        worst_features = S.active_chain.get_worst_features(features_no = 2)

        for feature in worst_features:
            if feature.cummulative_error == 0 or feature in S.mistakes_chain:
                continue
            S.mistakes_chain.append(feature)

        S.mistakes_chain.sort(key = lambda _ : _.cummulative_error, reverse = True)

    def change_active_chain(S):

        S.add_mistake_chains()

        S.resample()

        if S.mistakes_trigger:
            S.mistakes_trigger = False

            if len(S.mistakes_chain) > 5:
                mistakes_to_work, S.mistakes_chain = S.mistakes_chain[:5], S.mistakes_chain[5:]

                for mistake in mistakes_to_work:
                    mistake.decrease_errors()
                S.active_chain =  FeaturesChain(-1, mistakes_to_work)
                return

        S.active_chain = S.chains[0]

        if S.active_chain.last_review_urge < 0:
            S.old_limit -= 1
        else:
            S.new_limit -= 1

        S.active_chain.last_review_urge = 0
        S.active_chain.update_errors()

    def get_options_list(S, sample):
        options = [sample.text]
        for i in range(5):
            random_chain = random.choice(random.choice(S.chains).features)
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

    def get_next_feature(S):

        S.burning_in_work = list(filter(lambda _: _.is_burning, S.burning_in_work))

        if S.burning_in_work:

            S.burn_tick += 1
            S.burn_tick %= 2
            if S.burn_tick == 0:
                random.shuffle(S.burning_in_work)

            return S.burning_in_work[-1]
        else:
            S.set_burning_in_work()

        if not S.active_chain:
            S.change_active_chain()

        next_feature = S.active_chain.get_next_feature()
        if not next_feature:
            if S.active_chain.again:
                S.active_chain.again = False
            else:
                S.change_active_chain()
            next_feature = S.active_chain.get_next_feature()

        if not next_feature in S.burning_chain:
            if random.randint(0,10)%3 == 0:
                S.burning_chain.append(next_feature)

        return next_feature

    def is_burning(S):
        return len(S.burning_chain) >= S.burning_size

    def set_burning_in_work(S):
        if S.is_burning():
            S.burning_in_work, S.burning_chain = S.burning_chain[:S.burning_size], S.burning_chain[S.burning_size:]

            for feature in S.burning_in_work:
                feature.set_burn_mode()

    def dump_results(S, progression_file):
        if TEST:
            return

        backup = {}
        for chain in S.chains:
            backup[chain.chain_no] = [chain.progression_level, chain.last_review_urge, chain.errors_mapping]
        with open(progression_file, "w") as current_progress:
            json.dump(backup, current_progress, indent=2)

    def attach_images(S, images_file):
        if os.path.exists(images_file):
            images = {}
            with open(images_file) as images_ordered:
                images = json.load(images_ordered)
            if images:
                for chain in S.chains:
                    if chain.chain_no in images:
                        chain.initialize_images(images[chain.chain_no])
                    else:
                        print(f"Chain {chain.chain_no} have no image prepared")

    def restore_results(S, progression_file):
        if os.path.exists(progression_file):
            progress = {}
            with open(progression_file) as saved_prgress:
                progress = json.load(saved_prgress)
            if progress:
                for chain in S.chains:
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

    def get_chains_progression(S):
        minimal_level = min(S.chains, key = lambda _ : _.progression_level).progression_level
        mastered = len(list(filter(lambda _: _.progression_level > minimal_level, S.chains)))
        return f"{minimal_level}x {mastered}/{len(S.chains)}"


    def get_active_chain(S):

        return S.active_chain
