from config import W, H, CHINESE_FONT
from colors import white
import colors
from itertools import islice
import random
import os

from text_morfer import textMorfer

from rendering_backend import backend_switch
backend = backend_switch().get_backend_ref()

class UpperLayout():
    def __init__(self, display_instance):
        self.W = W
        self.H = H
        self.y1 = 0 
        self.y2 = self.H//8
        self.y3 = self.H - self.H//16
        self.higher_center = (self.y1 + self.y2)/2

        self.display_instance = display_instance
        self.backgroudn_color = (60, 60, 60)
        font_file = backend.api().font.match_font("setofont")
        self.smallest_font2 = backend.api().font.Font(font_file, 15)
        self.smallest_font = backend.api().font.Font(font_file, 20)
        self.small_font = backend.api().font.Font(font_file, 30)

        self.morfer = textMorfer()
        self.font = backend.api().font.Font(font_file, 50)
        self.large_font = backend.api().font.Font(font_file, 60)

        self.utf_font = backend.api().font.Font(CHINESE_FONT, 150, bold = True)
        self.combo = 1
        self.tiling = ""
        self.tiling_utf = True
        self.bg_color = (128,128,128)

        self.global_progress = ""
        self.active_balance = ""

        self.speed_index = 5000
        self.percent = 0.8
        self.progress_ratio = 0.0
        self.timing_ratio = 1.0
        self.move_image = False
        self.mastered = 0
        self.to_master = 0
        self.variation = 0
        self.random_variation = 0
        self.variation_on_rise = True
        self.blink = False
        #self.blink = True
        self.timer_x = W//2
        self.timer_y = H//2

        self.images_cached = {} 
        self.images_set_cached = {} 
        
        self.image = None
        self.images_set = []
        self.image_minor = None
        self.meta_text = ""
        self.last_positive = False

        self.trans_surface = backend.api().Surface((W,H)) 
        self.trans_surface.set_alpha(160)
        self.trans_surface.fill((30,0,30))

        self.trans_surface_minor = backend.api().Surface((W,H)) 
        self.trans_surface_minor.set_alpha(40)
        self.trans_surface_minor.fill((30,0,30))

    def place_text(self, text, x, y, transparent = False, renderer = None, base_col = (80,80,80)):
        text = self.morfer.morf_text(text)
        if renderer is None:
            renderer = self.font
        if not transparent:
            text = renderer.render(text, True, base_col, (150,150,151))
        else:
            text = renderer.render(text, True, base_col)
        textRect = text.get_rect()
        textRect.center = (x, y)
        self.display_instance.blit(text, textRect)

    def co_variate(self):
        self.random_variation = random.randint(0,10)

        # if self.random_variation >9:
        #     self.blink = True
        # else:
        #     self.blink = False

        if self.random_variation > 5:
            self.timer_x = random.randint(W//2-W//4, W//2+W//4)
            self.timer_y = random.randint(H//2-H//4, H//2+H//4)

    def check_cached_image(self, path_to_image):
        if len(self.images_cached) > 100:
            self.images_cached = dict(islice(self.images_cached.items(), 50))

        if not path_to_image or not os.path.exists(path_to_image):
            self.images_cached[path_to_image] = None
            return

        if path_to_image in self.images_cached:
            return

        image_converted = backend.api().image.load(path_to_image).convert()
        #image_converted.set_alpha(200)
        image_scaled = backend.api().transform.scale(image_converted, (W, H))
        self.images_cached[path_to_image]  = image_scaled

    def set_image(self, path_to_image, minor=False):
        self.co_variate()

        if isinstance(path_to_image, list):
            if path_to_image == self.images_set_cached:
                return

            self.images_set = []
            self.images_set_cached = []
            self.image = None

            for image_name in path_to_image:
                self.check_cached_image(image_name)
                if image_name in self.images_cached and self.images_cached[image_name]:
                    self.images_set.append(self.images_cached[image_name])
                else:
                    self.images_set.append(None)
            return

        if not path_to_image in self.images_cached:
            self.check_cached_image(path_to_image)

        self.image = self.images_cached[path_to_image]

        if not path_to_image:
            if not minor:
                self.image = None
                self.images_set = []
                self.images_set_cached = []
            else:
                self.image_minor = None

        elif not path_to_image in self.images_cached and os.path.exists(path_to_image):
            if len(self.images_cached) > 100:
                self.images_cached = dict(islice(self.images_cached.items(), 50))

            image_converted = backend.api().image.load(path_to_image).convert()


            image_scaled = backend.api().transform.scale(image_converted, (W, H))

            self.images_cached[path_to_image]  = image_scaled

            if not minor:
                self.image = self.images_cached[path_to_image]
            else:
                self.image_minor = backend.api().transform.flip(self.images_cached[path_to_image], random.choice([True, False]), False)
        else:
            if not minor:
                self.image = self.images_cached[path_to_image]
            else:
                self.image_minor = backend.api().transform.flip(self.images_cached[path_to_image], random.choice([True, False]), False)


    def redraw(self):
        clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)

        self.display_instance.fill(white)

        if self.image:
            self.display_instance.blit(self.image, (0, 0))
            self.display_instance.blit(self.trans_surface, (0,0))

        if self.images_set:
            set_locations = []
            
            if len(self.images_set)==2:
                set_locations.append((int(-1*(W//2)), int(0)))
                set_locations.append((int(W//2), int(0)))

            for i in range(len(self.images_set)):
                if i < len(self.images_set) and self.images_set[i]:
                    self.display_instance.blit(self.images_set[i], set_locations[i])


        if self.image_minor:
            self.trans_surface_minor.blit(self.image_minor, (0,0))
            self.display_instance.blit(self.trans_surface_minor, (0,0))

        if self.variation_on_rise:
            self.variation += 1
        else:
            self.variation -= 1

        if self.variation > 2:
            self.variation_on_rise = False
        elif self.variation < 0:
            self.variation_on_rise = True

        line_color = (int(255*(1-self.percent)),int(255*(self.percent)),0)

        self.place_text(str(self.combo)+"x",  W//2,
                        20,
                        transparent = True,
                        renderer = self.large_font,
                        base_col = (50,50,50))

        self.place_text(str(self.global_progress), W//2 + W//8,
                        20,
                        transparent = True,
                        renderer = self.small_font,
                        base_col = (50,50,50))

        self.place_text(str(self.global_progress), W//2 - W//8,
                        20,
                        transparent = True,
                        renderer = self.small_font,
                        base_col = (50,50,50))


        inter_color = lambda v1, v2, p: clip_color(v1 + (v2-v1)*p)
        interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], self.timing_ratio),
                                                   inter_color(col1[1], col2[1], self.timing_ratio),
                                                   inter_color(col1[2], col2[2], self.timing_ratio))


        wdth = 5 if not self.blink else 75
        r_factor = 1 if not self.blink else 2
        col2 = interpolate(colors.col_wicked_darker, colors.col_correct, self.combo/10)
        if not self.blink:
            line_color = interpolate(colors.col_active_lighter, col2, 1.0-self.timing_ratio)
        else:
            line_color = random.choice([colors.mid_color, colors.col_black, colors.dark_red, colors.dark_green, colors.white])
            #line_color = interpolate(colors.mid_color, colors.col_black, 1.0-self.variation/2)
        backend.api().draw.circle(self.display_instance,
                                  line_color, (self.timer_x, self.timer_y),
                                  r_factor*min(W-self.timer_x, self.timer_x, H-self.timer_y, self.timer_y)*self.timing_ratio, width=wdth)

        if self.meta_text:
            line_1 = H//2 - H//4
            line_2 = H//2
            line_3 = H//2 + H//4
            delta_1 = H//4
            delta_05 = H//8
            delta_2 = H//2
            w_line = line_2
            w_pos_1 =  (W//2)*(1-self.timing_ratio)**2
            w_pos_2 =  W - (W//2)*(1-self.timing_ratio)**2
            w_pos = w_pos_1
            if "PAPERCUT" in self.meta_text:
                w_line = line_1
                w_pos = w_pos_2
            elif "EXECUTION" in self.meta_text:
                w_line = line_3
                w_pos = w_pos_2
            elif "WOUNDED" in self.meta_text:
                w_line = line_3 - delta_1*self.timing_ratio**2
                w_pos = w_pos_2
            elif "INJURED" in self.meta_text:
                w_line = line_1 + delta_1*self.timing_ratio**2
                w_pos = w_pos_2
            elif "MASACRE" in self.meta_text or "BLAST" in self.meta_text:
                w_line = line_2
            elif "CLATCH" in self.meta_text:
                w_line = line_3 - delta_05*self.timing_ratio**2
            elif "FLEED" in self.meta_text:
                w_line = line_1 + delta_05*self.timing_ratio**2
            elif "STUBBED" in self.meta_text:
                w_line = line_3 - delta_2*self.timing_ratio**2
            elif "NAILED" in self.meta_text:
                w_line = line_1 + delta_2*self.timing_ratio**2
            elif "DROP" in self.meta_text:
                w_line = line_3 + delta_05*self.timing_ratio**2
                w_pos = w_pos_2
            elif "MISFIRE" in self.meta_text:
                w_line = line_1 - delta_05*self.timing_ratio**2
                w_pos = w_pos_2
            else:
                w_line = line_2


            self.place_text(f"{self.meta_text}",
                        w_pos,
                        w_line,
                        transparent = True,
                        renderer = self.large_font,
                        base_col = (90,150,90) if self.last_positive else (150, 90, 90))


        line_color = (int((235)*(1-self.percent)),int((235)*(self.percent)),0)


        if self.blink:
            return

        backend.api().draw.rect(self.display_instance,
                                  line_color,
                                  ((W//2 - ((W//4)*(self.percent))/2),
                                   45,
                                   (W//4*self.percent),
                                   20))

        lower_p = lambda _ :  int(int(_) - int(_)*0.25)
        greater_p = lambda _ :  int(int(_) + int(_)*0.25*3)

        pm1 = lower_p(self.active_balance)
        pm2 = lower_p(pm1)
        pm3 = lower_p(pm2)
        pg1 = greater_p(self.active_balance)
        pg2 = greater_p(pg1)
        pg3 = greater_p(pg2)

        self.place_text(f"{pm3}$", W//2-W//8,
                        55,
                        transparent = True,
                        renderer = self.smallest_font2,
                        base_col = (90,50,10))

        self.place_text(f"{pm2}$", W//2-W//10,
                        55,
                        transparent = True,
                        renderer = self.smallest_font,
                        base_col = (90,50,10))
        self.place_text(f"{pm1}$", W//2-W//16,
                        55,
                        transparent = True,
                        renderer = self.small_font,
                        base_col = (90,50,10))
        
        self.place_text(f"{self.active_balance}$", W//2,
                        55,
                        transparent = True,
                        renderer = self.font,
                        base_col = (50,50,50))

        self.place_text(f"{pg1}$", W//2+W//16,
                        55,
                        transparent = True,
                        renderer = self.small_font,
                        base_col = (50,10,90))
        self.place_text(f"{pg2}$", W//2+W//10,
                        55,
                        transparent = True,
                        renderer = self.smallest_font,
                        base_col = (50,10,90))
        self.place_text(f"{pg3}$", W//2+W//8,
                        55,
                        transparent = True,
                        renderer = self.smallest_font2,
                        base_col = (50,10,90))


