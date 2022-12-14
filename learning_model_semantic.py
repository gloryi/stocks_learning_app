import random
import json
import os
from config_semantic import PROGRESSION_FILE, IMAGES_MAPPING_FILE

class MarkedAlias():
    def __init__(self, content, key, attached_unit, active = False):
        self.content = content
        self.content_type = "text"
        self.active = active
        self.correct = False
        self.wrong = False
        self.attached_unit = attached_unit
        self.key = key

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def register_match(self):
        self.attached_unit.deactivate(positive_feedback = True)

    def register_error(self):
        self.attached_unit.deactivate(positive_feedback = False)

class SemanticUnit():
    def __init__(self, aliases):
        self.aliases = aliases
        self.activated = False
        self.learning_score = 100 
        self.key = id(self)

    def __increment(self):
        self.learning_score += 1
            

    def __decrement(self):
        self.learning_score -= 1 
        if self.learning_score <= 98:
            self.learning_score = 98

    def activate(self):
        self.activated = True

    def produce_pair(self):
        if not self.activated:
            return [MarkedAlias(_, self.key, self) for _ in random.sample(self.aliases, 2)]
        else:
            selected = [MarkedAlias(_, self.key, self) for _ in random.sample(self.aliases, 2)]
            active = random.choice(selected)
            active.activate()
            
            return selected

    def deactivate(self, positive_feedback = False):
        if self.activated:

            if positive_feedback:
                self.__increment()
            else:
                self.__decrement()

        self.activated = False

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
    def __init__(self, entity, in_key, out_key, main_feature, key_feature_pairs): 
        self.entity = entity
        self.in_key = in_key.upper()
        self.out_key = out_key.upper()
        self.main_feature = main_feature
        self.keys = [_.upper() for _ in key_feature_pairs[0::2]]
        self.features = key_feature_pairs[1::2]
        self.progression_level = 0
        self.decreased = False
        self.rised = False
        self.attached_image = "" 
        self.basic_timing_per_level = {0:30,
                                       1:30,
                                       2:30}
                                       # 3:30,
                                       # 4:30,
                                       # 5:30}

    def set_mode(self, unit_type):
        if self.progression_level == 0:
            return ChainUnitType.mode_open
        elif self.progression_level >= 1 and unit_type == ChainUnitType.type_feature:
            return ChainUnitType.mode_question
        else:
            return ChainUnitType.mode_open
        # elif self.progression_level == 1 and unit_type == ChainUnitType.type_key:
        #     return ChainUnitType.mode_question 
        # elif self.progression_level == 2 and unit_type == ChainUnitType.type_feature:
        #     return ChainUnitType.mode_question
        # elif self.progression_level >= 3 and unit_type == ChainUnitType.type_feature:
        #     return ChainUnitType.mode_question
        # elif self.progression_level >= 3 and unit_type == ChainUnitType.type_key:
        #     return ChainUnitType.mode_hidden
        # else:
        #     return ChainUnitType.mode_open

    def ask_for_image(self):
        if self.attached_image and self.progression_level <2:
            return self.attached_image
        else:
            return ""


    def set_extra(self, unit_type):
        return ChainUnitType.extra_focus
        # if self.progression_level == 0 and unit_type == ChainUnitType.type_key:
        #     return ChainUnitType.extra_focus
        # if self.progression_level == 1 and unit_type == ChainUnitType.type_key:
        #     return ChainUnitType.extra_focus 
        # elif self.progression_level == 2 and unit_type == ChainUnitType.type_feature:
        #     return ChainUnitType.extra_focus
        # elif self.progression_level >= 3 and unit_type == ChainUnitType.type_feature:
        #     return ChainUnitType.extra_focus
        # else:
        #     return None

    def get_timing(self):
        return self.basic_timing_per_level[self.progression_level]


    def get_context(self):
       # keys = [ChainUnit(_, ChainUnitType.type_key,
       #                   self.set_mode(ChainUnitType.type_key),
       #                   ChainUnitType.position_keys, i+1,
       #                   font=ChainUnitType.font_cyrillic,
       #                   preferred_position = i,
       #                   extra = self.set_extra(ChainUnitType.type_key)) for (i,_) in enumerate(self.keys)] 
       features = [ChainUnit(_, ChainUnitType.type_feature,
                                 self.set_mode(ChainUnitType.type_feature),
                                 ChainUnitType.position_features, i+1,
                              preferred_position = i,
                             extra = self.set_extra(ChainUnitType.type_feature)) for (i,_) in enumerate(self.features)]
       # subtitle = [ChainUnit(self.in_key, ChainUnitType.type_key,
       #                           self.set_mode(ChainUnitType.type_key),
       #                           ChainUnitType.position_keys, 0,
       #                           font = ChainUnitType.font_cyrillic,
       #                       preferred_position = "IN_KEY",
       #                       extra = self.set_extra(ChainUnitType.type_key))]
       subtitle = [ChainUnit(self.main_feature, ChainUnitType.type_feature,
                                 self.set_mode(ChainUnitType.type_feature),
                                 ChainUnitType.position_keys, 0,
                              preferred_position = "MAIN_FEATURE",
                              extra = self.set_extra(ChainUnitType.type_feature))]
       #return keys + features + subtitle
       return features + subtitle


    def get_main_title(self):
        return self.entity

    def register_progress(self, is_solved = False):
        timing = self.basic_timing_per_level[self.progression_level]
        level = self.progression_level
        if is_solved:
            # if not self.progression_level == 1:
            #     self.basic_timing_per_level[self.progression_level] = timing +4 if timing < 40 else 40 
            self.basic_timing_per_level[self.progression_level] = timing +4 if timing < 40 else 40 
            self.progression_level = level + 1 if level < 2 else 2 
            self.rised = True
            self.decreased = False
        else:
            self.basic_timing_per_level[self.progression_level] = timing -4 if timing > 20 else 20 
            self.progression_level = level -1 if level > 0 else 0 
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


class FeaturesChain():
    def __init__(self, chain_no, features):
        self.chain_no = chain_no
        self.features = features
        self.features.append(self.create_review_chain(self.features))
        self.progression_level = 0
        self.recall_level = 0
        self.active_position = -1
        self.ascended = False
        self.active_changed = False

    def create_review_chain(self, features):
        in_key = features[0].main_feature
        out_key = features[-1].main_feature
        entity = "*"
        main_feature = features[0].entity
        key_feature_pairs = []
        for feature in features[1:]:
            key_feature_pairs.append(feature.main_feature)
            key_feature_pairs.append(feature.entity)
        return ChainedFeature(entity, in_key, out_key, main_feature, key_feature_pairs)

    def ascend(self):
        for feature in self.features:
            # feature.progression_level = 4
            feature.progression_level = 2
            feature.deselect()

    def initialize_images(self, images_list):
        for image, feature in zip(images_list, self.features):
            feature.attached_image = image

    def check_active_changed(self):
        if self.active_changed:
            self.active_changed = False
            return True
        return False

    def get_next_feature(self):
        # 0 level - card readed.
        # Next step is to restore associated keys
        level = self.features[self.active_position].progression_level
        is_fallback = self.features[self.active_position].decreased
        is_up = self.features[self.active_position].rised
        # two main factors are card chain level and
        # the way level was acheived - by recall or by forgetting some
        if level == 0 and is_fallback:
            # back to zero means - learn chain again
            return self.features[self.active_position]
        if level == 1:
            # reached 1 means - learn keys
            return self.features[self.active_position]
        # if level == 2:
        #     return self.features[self.active_position]
        # if level == 3:
        #     return self.features[self.active_position]
        # if level == 4 and not is_up:
        #     return self.features[self.active_position]
        if level == 2 and not is_up:
            return self.features[self.active_position]
        
        self.features[self.active_position].deselect()
        self.active_position += 1
        self.active_changed = True
        if self.active_position >= len(self.features):
            self.active_position = 0
            self.progression_level += 1
            return None
        self.features[self.active_position].select()
        return self.features[self.active_position]

    # def get_options_list(self, sample):
    #     options = [sample.text]
    #     for i in range(5):
    #         random_chain = random.choice(self.features)
    #         if sample.type == ChainUnitType.type_key:
    #             selected = random.choice(random_chain.keys)
    #             options.append(selected)
    #         if sample.type == ChainUnitType.type_feature:
    #             selected = random.choice(random_chain.features)
    #             options.append(selected)
    #     random.shuffle(options)
    #     return options

    def get_features_list(self):
        units_list = [ChainUnit(_.entity + f" {_.progression_level}", font = ChainUnitType.font_utf) for _ in self.features]
        # TODO specify in config
        if len(units_list) < 12:
            delta_len = 12 - len(units_list)
            units_list += [ChainUnit("") for _ in range(delta_len)]
        elif len(units_list) > 12:
            units_list = units_list[:12]
        return units_list


class ChainedModel():
    def __init__(self, chains):
        self.chains = chains
        self.active_chain_index = 0
        self.old_limit = 2
        self.is_changed = False

        is_restored = self.restore_results(PROGRESSION_FILE)

        if not is_restored:
            self.active_chain = self.get_active_chain()
            self.dump_results(PROGRESSION_FILE)
        else:
            self.change_active_chain()

        self.attach_images(IMAGES_MAPPING_FILE)

    def resample(self):
        # TODO - pick old fresh ones if old_counter > 4
        for chain in self.chains:
            if chain.progression_level > 0:
                chain.recall_level = chain.recall_level - 1
        if self.old_limit:
            self.chains.sort(key = lambda _ : _.progression_level + _.recall_level * 0.25)
        else:
            self.chains.sort(key = lambda _ : _.progression_level)
            self.old_limit = 2
        self.dump_results(PROGRESSION_FILE)

    def change_active_chain(self):
        self.resample()
        self.active_chain_index = 0
        self.active_chain = self.chains[0]
        if self.active_chain.recall_level < 0:
            self.old_limit -= 1
        self.active_chain.recall_level = 0

    def get_options_list(self, sample):
        options = [sample.text]
        for i in range(5):
            random_chain = random.choice(random.choice(self.chains).features)
            preferred_position = sample.preferred_position
            # if sample.type == ChainUnitType.type_key:
            #     if preferred_position == "IN_KEY":
            #         selected = random_chain.in_key
            #     elif preferred_position is None or preferred_position >= len(random_chain.keys):
            #         #print("random picked key")
            #         selected = random.choice(random_chain.keys)
            #     else:
            #         selected = random_chain.keys[preferred_position]
            #     options.append(selected)
            if sample.type == ChainUnitType.type_feature:
                if preferred_position == "MAIN_FEATURE":
                    selected = random_chain.main_feature
                elif preferred_position is None or preferred_position >= len(random_chain.features):
                    selected = random.choice(random_chain.features)
                else:
                    selected = random_chain.features[preferred_position]
                options.append(selected)
        random.shuffle(options)
        return options

    def get_next_feature(self):
        next_chain = self.active_chain.get_next_feature()
        if not next_chain:
            self.change_active_chain()
            next_chain = self.active_chain.get_next_feature()

        self.is_changed = self.active_chain.check_active_changed()

        return next_chain

    def dump_results(self, progression_file):
        backup = {}
        for chain in self.chains:
            backup[chain.chain_no] = [chain.progression_level, chain.recall_level]
        with open(progression_file, "w") as current_progress:
            json.dump(backup, current_progress)

    def attach_images(self, images_file):
        if os.path.exists(images_file):
            images = {}
            with open(images_file) as images_ordered:
                images = json.load(images_ordered)
            if images:
                for chain in self.chains:
                    chain.initialize_images(images[chain.chain_no])

    def restore_results(self, progression_file):
        if os.path.exists(progression_file):
            progress = {}
            with open(progression_file) as saved_prgress:
                progress = json.load(saved_prgress)
            if progress:
                for chain in self.chains:
                    chain.progression_level = progress[chain.chain_no][0]
                    chain.recall_level = progress[chain.chain_no][1]
                    if chain.progression_level > 0:
                        chain.ascend()
            return True
        else:
            return False

    def get_chains_list(self):
        units_list = [ChainUnit(_.features[0].entity + "..." + _.features[-1].entity + f" {_.progression_level} | {_.recall_level}", font = ChainUnitType.font_utf) for _ in sorted(self.chains, key = lambda _ : _.progression_level + _.recall_level*0.25, reverse = True)]
        # TODO specify in config
        if len(units_list) < 12:
            delta_len = 12 - len(units_list)
            units_list += [ChainUnit("") for _ in range(delta_len)]
        elif len(units_list) > 12:
            units_list = units_list[:12]
        return units_list

    def get_active_chain(self):
        return self.chains[self.active_chain_index]
