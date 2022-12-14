from config import BPM

def global_timer(pygame_instance):
    last_frame_timestamp = pygame_instance.time.get_ticks()
    skip_even_frames = True
    while True:
        current_frame_timestamp = pygame_instance.time.get_ticks()
        frame_timedelta = (current_frame_timestamp - last_frame_timestamp)
        last_frame_timestamp = current_frame_timestamp
        #skip_even_frames = False if skip_even_frames else True 
        #if skip_even_frames:
            #continue
        yield frame_timedelta

class Counter():
    def __init__(self,
                 ui_ref = None,
                 bpm = None):

        if not bpm:
            self.bpm = BPM
        else:
            self.bpm = bpm

        self.basic_tick_ms = (60 * 1000) / self.bpm
        self.drop_time = self.basic_tick_ms
        self.time_elapsed = 0 
        self.ui_ref = ui_ref

    def is_tick(self, time_delta):

        self.time_elapsed += time_delta
        if self.ui_ref:
            self.ui_ref.timing_ratio = 1.0 - self.time_elapsed / self.drop_time

        if self.time_elapsed >= self.drop_time:

            self.time_elapsed = 0
            return True

        return False

    def modify_bpm(self, new_bpm):
        self.bpm = new_bpm
        self.basic_tick_ms = (60 * 1000) / self.bpm
        self.drop_time = self.basic_tick_ms

    def drop_elapsed(self):
        self.time_elapsed = 0

class Progression():
    def __init__(self,
                 update_counter,
                 ui_ref):

        self.correct = 3
        self.missed  = 1

        self.new_event = False
        self.correct_event = False
        self.combo = 0
        self.speed_combo = 0
        self.bpm = BPM

        self.basic_tick_ms = (60 * 1000) / self.bpm

        self.update_counter = update_counter
        self.ui_ref = ui_ref

    def get_percent(self):
        percent = self.correct / (self.correct + self.missed)
        self.ui_ref.percent = percent
        return percent

    def register_correct(self):
        if self.correct <= 3:
            self.correct += 1
        else:
            if self.missed > 0:
                self.missed -= 1

        self.new_event = True
        self.correct_event = True
        self.combo += 1
        self.speed_combo += 1
        self.ui_ref.combo = self.combo

    def register_miss(self):
        if self.missed <= 3:
            self.missed += 1
        else:
            if self.correct > 0:
                self.correct -= 1
        self.new_event = True
        self.correct_event = False
        self.combo = 0
        self.speed_combo -= 1
        self.ui_ref.combo = self.combo

    def register_event(self, value):
        if value > 0:
            self.register_correct()
        elif value < 0:
            self.register_miss()

        if self.get_percent() == 0:
            self.correct = 3 
            self.missed  = 1
            self.get_percent()
            return False

        return True

    def is_more_intense_required(self):
        return self.get_percent() > 0.75

    def is_less_intense_required(self):
        return self.get_percent() < 0.7


    def modify_basic_beat(self, value, modifier):
        value += modifier
        return 2 if value < 2 else 8 if value > 8 else value

    def update_basic_tick(self):
        self.basic_tick_ms = (60 * 1000) / self.bpm
    
    def normalize_bpm(self):
        self.bpm = 30 if self.bpm < 30 else 200 if self.bpm > 200 else self.bpm

    def synchronize_tick(self):
        #if self.new_event:
            #self.new_event = False

            #if self.correct_event and self.speed_combo >= 3:
                #self.bpm += self.bpm//32 
                #self.speed_combo = 0

            #elif not self.correct_event and self.speed_combo <= -2:
                #self.bpm -= self.bpm//8 
                #self.speed_combo = 0

            #self.normalize_bpm()

            #self.ui_ref.speed_index = self.bpm 
            #self.update_basic_tick()

            #self.update_counter.modify_bpm(self.bpm)
            
        return self.basic_tick_ms
