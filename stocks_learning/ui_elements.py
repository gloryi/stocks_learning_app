from config import W, H, CHINESE_FONT
from colors import white
from itertools import islice
import os

class UpperLayout():
    def __init__(self, pygame_instance, display_instance):
        self.W = W
        self.H = H
        self.y1 = 0 
        self.y2 = self.H//8
        self.y3 = self.H - self.H//16
        self.higher_center = (self.y1 + self.y2)/2
        self.pygame_instance = pygame_instance
        self.display_instance = display_instance
        self.backgroudn_color = (60, 60, 60)
        font_file = pygame_instance.font.match_font("setofont")
        self.font = pygame_instance.font.Font(font_file, 50)
        self.large_font = pygame_instance.font.Font(font_file, 80)
        self.utf_font = self.pygame_instance.font.Font(CHINESE_FONT, 150, bold = True)
        self.combo = 1
        self.tiling = ""
        self.tiling_utf = True
        self.bg_color = (128,128,128)

        self.global_progress = ""

        self.speed_index = 5000
        self.percent = 0.8
        self.progress_ratio = 0.0
        self.timing_ratio = 1.0
        self.mastered = 0
        self.to_master = 0
        self.variation = 0
        self.variation_on_rise = True
        self.images_cached = {} 
        self.image = None
        self.meta_text = ""

    def place_text(self, text, x, y, transparent = False, renderer = None, base_col = (80,80,80)):
        if renderer is None:
            renderer = self.font
        if not transparent:
            text = renderer.render(text, True, base_col, (150,150,151))
        else:
            text = renderer.render(text, True, base_col)
        textRect = text.get_rect()
        textRect.center = (x, y)
        self.display_instance.blit(text, textRect)

    def set_image(self, path_to_image):

        if not path_to_image:
            self.image = None

        elif not path_to_image in self.images_cached and os.path.exists(path_to_image):
            if len(self.images_cached) > 100:
                self.images_cached = dict(itertools.islice(self.images_cached.items(), 50))

            self.images_cached[path_to_image] = self.pygame_instance.image.load(path_to_image).convert()
            self.image = self.images_cached[path_to_image]

        else:
            self.image = self.images_cached[path_to_image]



    def redraw(self):
        clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)

        self.display_instance.fill(white)
        tiling_step = 200

        if self.image:
            self.display_instance.blit(self.image, (0, 0))
            tiling_step = 300


        if self.variation_on_rise:
            self.variation += 1
        else:
            self.variation -= 1

        if self.variation > 10:
            self.variation_on_rise = False
        elif self.variation < 0:
            self.variation_on_rise = True

        line_color = (int(255*(1-self.percent)),int(255*(self.percent)),0)

        self.place_text(str(self.combo)+"x", 420 - 100,
                        60,
                        transparent = True,
                        renderer = self.large_font,
                        base_col = (50,50,50))

        self.place_text(str(self.global_progress), 420 - 300,
                        40,
                        transparent = True,
                        renderer = self.font,
                        base_col = (50,50,50))

        self.place_text(str(self.combo)+"x", 920 + 100,
                        60,
                        transparent = True,
                        renderer = self.large_font,
                        base_col = (50,50,50))

        self.place_text(str(self.global_progress), 920 + 300,
                        40,
                        transparent = True,
                        renderer = self.font,
                        base_col = (50,50,50))

        if self.meta_text:
            chunks = [self.meta_text[i:i+40] for i in range(0, len(self.meta_text), 40)]
            for i, chunk in enumerate(chunks):
                self.place_text(chunk,
                                W//2,
                                40*(i+1),
                                transparent = False,
                                renderer = self.font,
                                base_col = (clip_color(self.bg_color[0]+self.variation*3),
                                            clip_color(self.bg_color[1]+self.variation*3),
                                            clip_color(self.bg_color[2]+self.variation*3)))

        line_color = (clip_color((178)*(1-self.timing_ratio)),
                      clip_color((150)*(self.timing_ratio)),
                      clip_color((150)*(1-self.timing_ratio)))

        self.pygame_instance.draw.rect(self.display_instance,
                                  line_color,
                                  ((575+25 - 200 + ((200+400)*(1-self.timing_ratio))/2),
                                   275+25+25,
                                   (200+400)*self.timing_ratio,
                                   200-50-50))

        self.pygame_instance.draw.rect(self.display_instance,
                                  line_color,
                                  (575+50+25,
                                   (275-200 + ((200+400)*(1-self.timing_ratio))/2),
                                   200-50-50,

                                   (200+400)*self.timing_ratio))

        line_color = (int((235)*(1-self.percent)),int((235)*(self.percent)),0)

        self.pygame_instance.draw.rect(self.display_instance,
                                  line_color,
                                  ((320 + (250*3*(1-self.percent))/2),
                                   0,
                                   250*3*self.percent,
                                   25))

        self.pygame_instance.draw.rect(self.display_instance,
                                  line_color,
                                  ((320 + (250*3*(1-self.percent))/2),
                                   self.H-25,
                                   250*3*self.percent,
                                   25))
