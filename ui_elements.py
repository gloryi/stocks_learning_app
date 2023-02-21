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
    def __init__(S, display_instance):
        S.W = W
        S.H = H
        S.y1 = 0 
        S.y2 = S.H//8
        S.y3 = S.H - S.H//16
        S.higher_center = (S.y1 + S.y2)/2

        S.display_instance = display_instance
        S.backgroudn_color = (60, 60, 60)
        font_file = backend.api().font.match_font("setofont")
        S.smallest_font2 = backend.api().font.Font(font_file, 15)
        S.smallest_font = backend.api().font.Font(font_file, 20)
        S.small_font = backend.api().font.Font(font_file, 30)

        S.morfer = textMorfer()
        S.font = backend.api().font.Font(font_file, 50)
        S.large_font = backend.api().font.Font(font_file, 60)

        S.utf_font = backend.api().font.Font(CHINESE_FONT, 150, bold = True)
        S.utf_font1 = backend.api().font.Font(CHINESE_FONT, 100, bold = True)
        S.utf_font2 = backend.api().font.Font(CHINESE_FONT, 50, bold = True)
        S.combo = 1
        S.tiling = ""
        S.tiling_utf = True
        S.bg_color = (128,128,128)

        S.global_progress = ""
        S.active_balance = ""

        S.speed_index = 5000
        S.percent = 0.8
        S.progress_ratio = 0.0
        S.timing_ratio = 1.0
        S.move_image = False
        S.mastered = 0
        S.to_master = 0
        S.variation = 0
        S.random_variation = 0
        S.variation_on_rise = True
        S.blink = False
        #S.blink = True
        S.timer_x = W//2
        S.timer_y = H//2

        S.images_cached = {} 
        S.images_set_cached = {} 
        
        S.image = None
        S.images_set = []
        S.image_minor = None
        S.meta_text = ""
        S.last_positive = False

        S.trans_surface = backend.api().Surface((W,H)) 
        S.trans_surface.set_alpha(160)
        S.trans_surface.fill((30,0,30))

        S.trans_surface_minor = backend.api().Surface((W,H)) 
        S.trans_surface_minor.set_alpha(40)
        S.trans_surface_minor.fill((30,0,30))

        S.quadra_w_perce1 = 0.0
        S.quadra_w_perce2 = 0.0
        S.back_v = ""

        S.show_mode = False
        S.tiling_text = ""
        S.tiling_cooldown = 0
        S.tiling_var = lambda a,b : a==b
        

    def place_text(S, text, x, y, transparent = False, renderer = None, base_col = (80,80,80)):
        text = S.morfer.morf_text(text)
        if renderer is None:
            renderer = S.font
        if not transparent:
            text = renderer.render(text, True, base_col, (150,150,151))
        else:
            text = renderer.render(text, True, base_col)
        textRect = text.get_rect()
        textRect.center = (x, y)
        S.display_instance.blit(text, textRect)

    def co_variate(S):
        S.random_variation = random.randint(0,10)

        if S.tiling_cooldown:
            S.tiling_cooldown -= 1
        else:
            S.tiling_cooldown = random.randint(15,30)
            S.tiling_text = random.choice(["levels", "volume", 
           "right side", "upper",
           "lower", "volatility",
           "flow el.", "nih pattr", "pa pattr",
           "imb", "htf", "acc/dst", "up/down",
           "hh ll", "boses","clasc ta",
           "high/lows", "inner bars", "ob", "swings",
           "engulfs", "dojis", "image rec",
           "color/series", "rallies", "probityie", "otboy", "lp",
            "hairy", "marubozu", "hollow", "spikes",
            "subm prev", "subm nxt", "high tf yell",
            "high tf r/g", "overflows",
            "gaps", "opposites"])
        
            S.tiling_text += random.choice([""," FP"])

        if S.random_variation > 5:
            S.timer_x = random.randint(W//2-W//4, W//2+W//4)
            S.timer_y = random.randint(H//2-H//4, H//2+H//4)

        S.tiling_var = random.choice([lambda a,b : a==b,
                                      lambda a,b : a==1,
                                      lambda a,b : a==2,
                                      lambda a,b : a==3,
                                      lambda a,b : b==1,
                                      lambda a,b : b==2,
                                      lambda a,b : b==3,
                                      lambda a,b : a==4-b,
                                      lambda a,b : b==4-a,
                                      lambda a,b : a==3-b,
                                      lambda a,b : b==3-a,
                                      lambda a,b : a==2-b,
                                      lambda a,b : b==2-a])

    def check_cached_image(S, path_to_image):
        if len(S.images_cached) > 100:
            S.images_cached = dict(islice(S.images_cached.items(), 50))

        if not path_to_image or not os.path.exists(path_to_image):
            S.images_cached[path_to_image] = None
            return

        if path_to_image in S.images_cached:
            return

        image_converted = backend.api().image.load(path_to_image).convert()
        #image_converted.set_alpha(200)
        image_scaled = backend.api().transform.scale(image_converted, (W, H))
        S.images_cached[path_to_image]  = image_scaled

    def set_image(S, path_to_image, minor=False):
        S.co_variate()

        # TWO IMAGES
        if isinstance(path_to_image, list) and not minor:

            if path_to_image == S.images_set_cached:
                return

            S.images_set = []
            S.images_set_cached = []
            S.image = None

            for image_name in path_to_image:
                S.check_cached_image(image_name)
                if image_name in S.images_cached and S.images_cached[image_name]:
                    S.images_set.append(S.images_cached[image_name])
                else:
                    S.images_set.append(None)
            return

        # SINGLE IMAGE
        if not path_to_image in S.images_cached:
            S.check_cached_image(path_to_image)

        S.image = S.images_cached[path_to_image]

        if not path_to_image:
            if not minor:
                S.image = None
                S.images_set = []
                S.images_set_cached = []
            else:
                S.image_minor = None

        elif not path_to_image in S.images_cached and os.path.exists(path_to_image):
            if len(S.images_cached) > 100:
                S.images_cached = dict(islice(S.images_cached.items(), 50))

            image_converted = backend.api().image.load(path_to_image).convert()


            image_scaled = backend.api().transform.scale(image_converted, (W, H))

            S.images_cached[path_to_image]  = image_scaled

            if not minor:
                S.image = S.images_cached[path_to_image]
            else:
                S.image_minor = backend.api().transform.flip(S.images_cached[path_to_image], random.choice([True, False]), False)
        else:
            if not minor:
                S.image = S.images_cached[path_to_image]
            else:
                S.image_minor = backend.api().transform.flip(S.images_cached[path_to_image], random.choice([True, False]), False)


    def redraw(S):
        clip_color = lambda _ : 0 if _ <=0 else 255 if _ >=255 else int(_)

        S.display_instance.fill(white)

        if S.image:
            S.display_instance.blit(S.image, (0, 0))
            S.display_instance.blit(S.trans_surface, (0,0))

        if S.images_set:
            set_locations = []
            
            if len(S.images_set)==2:
                set_locations.append((int(-1*(W//2)), int(0)))
                set_locations.append((int(W//2), int(0)))

            for i in range(len(S.images_set)):
                if i < len(S.images_set) and S.images_set[i]:
                    S.display_instance.blit(S.images_set[i], set_locations[i])
            S.display_instance.blit(S.trans_surface, (0,0))

        if S.image_minor:
            S.trans_surface_minor.blit(S.image_minor, (0,0))
            S.display_instance.blit(S.trans_surface_minor, (0,0))

        if S.variation_on_rise:
            S.variation += 1
        else:
            S.variation -= 1

        if S.variation > 2:
            S.variation_on_rise = False
        elif S.variation < 0:
            S.variation_on_rise = True

        if S.show_mode or S.blink:
            t_font = S.utf_font2 if not S.blink else S.utf_font1
            for i,x in enumerate(range(100,W,500)):
                for j,y in enumerate(range(100,H,500)):

                    if not S.tiling_var(i,j):
                        continue

                    S.place_text(S.tiling_text + f" {S.tiling_cooldown//5}",
                                    x,
                                    y,
                                    transparent=True,
                                    renderer = S.utf_font2,
                                    base_col = (clip_color(225+S.variation*4),
                                                225-S.variation,
                                                225+S.random_variation))

        line_color = (int(255*(1-S.percent)),int(255*(S.percent)),0)

        S.place_text(str(S.combo)+"x",  W//2,
                        20,
                        transparent = True,
                        renderer = S.large_font,
                        base_col = (50,50,50))

        S.place_text(str(S.global_progress), W//2 + W//8,
                        20,
                        transparent = True,
                        renderer = S.small_font,
                        base_col = (50,50,50))

        S.place_text(str(S.global_progress), W//2 - W//8,
                        20,
                        transparent = True,
                        renderer = S.small_font,
                        base_col = (50,50,50))


        inter_color = lambda v1, v2, p: clip_color(v1 + (v2-v1)*p)
        interpolate = lambda col1, col2, percent: (inter_color(col1[0], col2[0], S.timing_ratio),
                                                   inter_color(col1[1], col2[1], S.timing_ratio),
                                                   inter_color(col1[2], col2[2], S.timing_ratio))


        wdth = 5 if not S.blink else 75
        r_factor = 1 if not S.blink else 2
        col2 = interpolate(colors.col_wicked_darker, colors.col_correct, S.combo/10)
        if not S.blink:
            line_color = interpolate(colors.col_active_lighter, col2, 1.0-S.timing_ratio)
        else:
            line_color = random.choice([colors.mid_color, colors.col_black, colors.dark_red, colors.dark_green, colors.white])
            #line_color = interpolate(colors.mid_color, colors.col_black, 1.0-S.variation/2)

        max_r = r_factor*min(W-S.timer_x, S.timer_x, H-S.timer_y, S.timer_y)
        backend.api().draw.circle(S.display_instance,
                                  line_color, (S.timer_x, S.timer_y),
                                  max_r*S.timing_ratio, width=wdth)

        backend.api().draw.circle(S.display_instance,
                                  line_color, (W//2, H//2),
                                  (H//2)*S.quadra_w_perce1, width=1)
        #backend.api().draw.circle(S.display_instance,
                                  #line_color, (S.timer_x, S.timer_y),
                                  #max_r*S.quadra_w_perce2, width=1)

        if S.meta_text:
            line_1 = H//2 - H//4
            line_2 = H//2
            line_3 = H//2 + H//4
            delta_1 = H//4
            delta_05 = H//8
            delta_2 = H//2
            w_line = line_2
            w_pos_1 =  (W//2)*(1-S.timing_ratio)**2
            w_pos_2 =  W - (W//2)*(1-S.timing_ratio)**2
            w_pos = w_pos_1

            if "PAPERCUT" in S.meta_text:
                w_line = line_1
                w_pos = w_pos_2
            elif "EXECUTION" in S.meta_text:
                w_line = line_3
                w_pos = w_pos_2
            elif "WOUNDED" in S.meta_text:
                w_line = line_3 - delta_1*S.timing_ratio**2
                w_pos = w_pos_2
            elif "INJURED" in S.meta_text:
                w_line = line_1 + delta_1*S.timing_ratio**2
                w_pos = w_pos_2
            elif "MASACRE" in S.meta_text or "BLAST" in S.meta_text:
                w_line = line_2
            elif "CLATCH" in S.meta_text:
                w_line = line_3 - delta_05*S.timing_ratio**2
            elif "FLEED" in S.meta_text:
                w_line = line_1 + delta_05*S.timing_ratio**2
            elif "STUBBED" in S.meta_text:
                w_line = line_3 - delta_2*S.timing_ratio**2
            elif "NAILED" in S.meta_text:
                w_line = line_1 + delta_2*S.timing_ratio**2
            elif "DROP" in S.meta_text:
                w_line = line_3 + delta_05*S.timing_ratio**2
                w_pos = w_pos_2
            elif "MISFIRE" in S.meta_text:
                w_line = line_1 - delta_05*S.timing_ratio**2
                w_pos = w_pos_2
            else:
                w_line = line_2

            text_placed = S.meta_text
            if ("STUBBED" in S.meta_text or "NAILED" in S.meta_text) and S.back_v:
                text_placed = S.back_v.replace("*** IBACKV ***", "").replace("#","")

            S.place_text(f"{text_placed}",
                        w_pos,
                        w_line,
                        transparent = True,
                        renderer = S.large_font,
                        base_col = (90,150,90) if S.last_positive else (150, 90, 90))


        line_color = (int((235)*(1-S.percent)),int((235)*(S.percent)),0)


        if S.blink:
            return

        backend.api().draw.rect(S.display_instance,
                                  line_color,
                                  ((W//2 - ((W//4)*(S.percent))/2),
                                   45,
                                   (W//4*S.percent),
                                   20))

        lower_p = lambda _ :  int(int(_) - int(_)*0.25)
        greater_p = lambda _ :  int(int(_) + int(_)*0.25*3)

        pm1 = lower_p(S.active_balance)
        pm2 = lower_p(pm1)
        pm3 = lower_p(pm2)
        pg1 = greater_p(S.active_balance)
        pg2 = greater_p(pg1)
        pg3 = greater_p(pg2)

        S.place_text(f"{pm3}$", W//2-W//8,
                        55,
                        transparent = True,
                        renderer = S.smallest_font2,
                        base_col = (90,50,10))

        S.place_text(f"{pm2}$", W//2-W//10,
                        55,
                        transparent = True,
                        renderer = S.smallest_font,
                        base_col = (90,50,10))
        S.place_text(f"{pm1}$", W//2-W//16,
                        55,
                        transparent = True,
                        renderer = S.small_font,
                        base_col = (90,50,10))
        
        S.place_text(f"{S.active_balance}$", W//2,
                        55,
                        transparent = True,
                        renderer = S.font,
                        base_col = (50,50,50))

        S.place_text(f"{pg1}$", W//2+W//16,
                        55,
                        transparent = True,
                        renderer = S.small_font,
                        base_col = (50,10,90))
        S.place_text(f"{pg2}$", W//2+W//10,
                        55,
                        transparent = True,
                        renderer = S.smallest_font,
                        base_col = (50,10,90))
        S.place_text(f"{pg3}$", W//2+W//8,
                        55,
                        transparent = True,
                        renderer = S.smallest_font2,
                        base_col = (50,10,90))


