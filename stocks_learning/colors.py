
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

dark_green = hex_to_rgb("#023020")
dark_red = hex_to_rgb("#560d0d")
