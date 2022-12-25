
def hex_to_rgb(h):
    h = h[1:]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

col_bg_darker     = hex_to_rgb("#93A0D9")
col_wicked_darker = hex_to_rgb("#A6A17C")
col_active_darker = hex_to_rgb("#5B7DD9")

col_bg_lighter     = hex_to_rgb("#F8A9EF")
col_wicked_lighter = hex_to_rgb("#F9D6C2")
col_active_lighter = hex_to_rgb("#F368F8")

col_correct = hex_to_rgb("#006A68")
col_error   = hex_to_rgb("#ED1500")

white = hex_to_rgb("#F2F1DF")

feature_text_col = hex_to_rgb("#FFCB96")
feature_bg = hex_to_rgb("#2E849E")

option_fg = hex_to_rgb("#68A834")
option_bg = hex_to_rgb("#F48F6C")

col_black = hex_to_rgb("#000030")

col_bt_pressed = hex_to_rgb("#4E52AF")
col_bt_down    = hex_to_rgb("#1D1313")
col_bt_text = hex_to_rgb("#FFFFFF")

dark_green = hex_to_rgb("#008F30")
dark_red = hex_to_rgb("#F50600")

red1 = hex_to_rgb("#DE045B")
red2 = hex_to_rgb("#700F3C")

green1 = hex_to_rgb("#44803F")
green2 = hex_to_rgb("#146152")

mid_color = hex_to_rgb("#FFCD39")

palettes = [] 
palettes.append([green1, green2, red1, red2, mid_color])
palettes.append([hex_to_rgb("#F2CA52"),
                 hex_to_rgb("#F28705"),
                 hex_to_rgb("#D91604"),
                 hex_to_rgb("#8C0303"),
                 hex_to_rgb("#F2D4C2")])

palettes.append([hex_to_rgb("#31AFE0"),
                 hex_to_rgb("#2F47AD"),
                 hex_to_rgb("#E47632"),
                 hex_to_rgb("#AD4728"),
                 hex_to_rgb("#4C557A")])

palettes.append([hex_to_rgb("#3DE073"),
                 hex_to_rgb("#008F30"),
                 hex_to_rgb("#F50600"),
                 hex_to_rgb("#8F3633"),
                 hex_to_rgb("#DEDAD9")])

palettes.append([hex_to_rgb("#38DFEB"),
                 hex_to_rgb("#2E979E"),
                 hex_to_rgb("#EB50AD"),
                 hex_to_rgb("#9E266E"),
                 hex_to_rgb("#FAE55F")])

palettes.append([hex_to_rgb("#6459D9"),
                 hex_to_rgb("#47418C"),
                 hex_to_rgb("#D943A7"),
                 hex_to_rgb("#8C246A"),
                 hex_to_rgb("#BFD94E")])

palettes.append([hex_to_rgb("#51E0A0"),
                 hex_to_rgb("#329468"),
                 hex_to_rgb("#5B3AE0"),
                 hex_to_rgb("#2E1594"),
                 hex_to_rgb("#E09935")])
