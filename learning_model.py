import random
import json
import os
import csv
from config import PROGRESSION_FILE, IMAGES_MAPPING_FILE, VISUAL_PART, STAKE_PART

knwon_prices = {}


class simpleCandle():
    def __init__(self, o, c, h, l, v, index = 0):
        self.o = o
        self.c = c
        self.h = h
        self.l = l
        self.v = v
        self.ha = []

        self.green = self.c >= self.o
        self.red = self.c < self.o
        self.last = False
        self.vRising = False
        self.index = index

        self.joined = False
        self.inner = False
        self.pierce = False
        self.conjoined = False
        self.doji = False
        self.overhigh = False
        self.overlow = False
        self.conjugates = []
        self.weak_pierce_prev = False
        self.weak_pierce_next = False
        self.upper_pierce_line = max(self.o, self.c)
        self.lower_pierce_line = min(self.o, self.c)

        self.thick_upper = False
        self.thick_lower = False

    def ochl(self):
        return self.o, self.c, self.h, self.l

def calculateHA(prev, current, index):
    hC = (current.o + current.c + current.h + current.l)/4
    hO = (prev.o + prev.c)/2
    hH = max(current.o, current.h, current.c)
    hL = min(current.o, current.h, current.c)
    hV = current.v
    return simpleCandle(hO, hC, hH, hL, hV, index)

def extract_ochlv(filepath):
    O, C, H, L, V = [], [], [], [], []
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
    O, C, H, L, V = extract_ochlv(asset_name)
    knwon_prices[asset_name] = [simpleCandle(o,c,h,l,v,i) for i, (o,c,h,l,v) in enumerate(zip(O,C,H,L,V))]

def get_candles(asset_name, index):

    if asset_name not in knwon_prices:
        fetch_prices(asset_name)

    for candle in knwon_prices[asset_name][int(index):]:
        yield candle

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

class ChainedFeature():
    def __init__(self, source, start_point):

        self.source = source
        self.start_point = start_point
        self.candles = self.pre_process_candles()

        self.feature_errors = []
        self.cummulative_error = 0
        self.decreased = False
        self.rised = False
        self.review = False
        self.attached_image = "" 
        self.basic_timing_per_level = {0:30,
                                       1:30,
                                       2:30}
    def pre_process_candles(self):
        candles_generator = get_candles(self.source, self.start_point)
        candles = []
        index_shift = 0
        for candle in candles_generator:
            candle.index -= index_shift

            if len(candles) >= VISUAL_PART + STAKE_PART:
                break

            if candles and len(candles) < VISUAL_PART:

                candles[-1].ha = calculateHA(candles[-1], candle, candle.index)

                upper_next, lower_next = max(candle.o, candle.c), min(candle.o, candle.c)
                upper_prev, lower_prev = max(candles[-1].o, candles[-1].c), min(candles[-1].o, candles[-1].c)

                if candle.h - upper_next > lower_next - candle.l:
                    candle.thick_upper = True
                elif candle.h - upper_next < lower_next - candle.l:
                    candle.thick_lower = True
                

                if candle.red and upper_next == lower_prev:
                    candles[-1].joined = True

                if candle.green and upper_prev == lower_next:
                    candles[-1].joined = True
                
                if candles[-1].h > candle.h and candles[-1].l < candle.l:
                    candles[-1].weak_pierce_next = True

                if candle.h > candles[-1].h and candle.l < candles[-1].l:
                    candle.weak_pierce_prev = True

                elif candle.h > candles[-1].h:
                    candle.overhigh = True

                elif candle.l < candles[-1].l:
                    candle.overlow = True


                if candle.o == candle.c:
                    candle.doji = True
                
                if upper_next <= upper_prev and lower_next >= lower_prev:
                    candle.inner = True
                
                if upper_prev <= upper_next and lower_prev >= lower_next:
                    candle.pierce = True
                    candle.upper_pierce_line = max(candles[-1].o, candles[-1].c)
                    candle.lower_pierce_line = min(candles[-1].o, candles[-1].c)


                    
            candles.append(candle)

        return candles

    def get_question_candles(self):
        return self.candles[:VISUAL_PART]

    def get_question_candles_minmax(self):
        min_price = min(self.candles[:VISUAL_PART], key = lambda _ : _.l).l
        max_price = max(self.candles[:VISUAL_PART], key = lambda _ : _.h).h
        return min_price, max_price


    def get_resulting_candles(self):
        return self.candles[STAKE_PART:]

    def get_candles_with_offset(self, offset_a, offset_b):
        return self.candles[offset_a:offset_a+offset_b]

    def get_all_candles(self):
        return self.candles

    def set_mode(self, unit_type):
        if self.feature_level == 0:
            return ChainUnitType.mode_open
        elif self.feature_level >= 1 and unit_type == ChainUnitType.type_feature:
            return ChainUnitType.mode_question
        else:
            return ChainUnitType.mode_open

    def ask_for_image(self):
        if self.attached_image and self.feature_level <2:
            return self.attached_image
        else:
            return ""


    def set_extra(self, unit_type):
        return ChainUnitType.extra_focus

    def get_timing(self):
        return self.basic_timing_per_level[self.feature_level]


    def get_context(self):
       source = [ChainUnit(self.source, ChainUnitType.type_feature,
                                 self.set_mode(ChainUnitType.type_feature),
                                 ChainUnitType.position_keys, 0,
                              preferred_position = "MAIN_FEATURE",
                              extra = self.set_extra(ChainUnitType.type_feature))]

       start_point = [ChainUnit(self.start_point, ChainUnitType.type_feature,
                                 self.set_mode(ChainUnitType.type_feature),
                                 ChainUnitType.position_keys, 0,
                              preferred_position = "MAIN_FEATURE",
                              extra = self.set_extra(ChainUnitType.type_feature))]
       return source + start_point

    def register_error(self, error_index):
        if error_index < len(self.feature_errors):
            self.feature_errors[error_index] += 1
            self.cummulative_error += 1

    def decrease_errors(self):
        if self.cummulative_error > 1:
            self.cummulative_error //= 2
        else:
            self.cummulative_error = 0

        for i in range(len(self.feature_errors)):
            error = self.feature_errors[i]
            if error > 1:
                self.feature_errors[i]//=2
            else:
                self.feature_errors[i] = 0



    def get_main_title(self):
        return self.source

    def register_progress(self, is_solved = False):
        timing = self.basic_timing_per_level[self.feature_level]
        level = self.feature_level
        if is_solved:
            self.basic_timing_per_level[self.feature_level] = timing +5 if timing < 50 else 50 
            self.feature_level = level + 1 if level < 2 else 2 
            self.rised = True
            self.decreased = False
        else:
            self.basic_timing_per_level[self.feature_level] = timing -5 if timing > 30 else 30 
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
        return f"{self.source} | progress = {self.feature_level} | errors = {self.cummulative_error}"


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
        for image, feature in zip(images_list, self.features):
            feature.attached_image = image

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
                self.progression_level = self.progression_level
            else:
                self.progression_level -= 1
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
        self.old_limit = 2
        self.new_limit = 2
        self.mistakes_trigger = False
        self.mistakes_chain = []
        self.burning_chain = []

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
        next_feature = self.active_chain.get_next_feature()
        if not next_feature:
            self.change_active_chain()
            next_feature = self.active_chain.get_next_feature()

        if not next_feature.review and not next_feature in self.burning_chain:
            self.burning_chain.append(next_feature)
            print(self.burning_chain)

        return next_feature

    def is_burning(self):
        return len(self.burning_chain) == 30

    def get_burning_features_list(self):
        pass

    def dump_results(self, progression_file):
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
