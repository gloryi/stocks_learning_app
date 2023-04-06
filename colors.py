colors_list = []


def hex_to_rgb(h, cache=False):
    h = h[1:]
    resulting = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    if cache:
        colors_list.append(resulting)
    return resulting


col_bg_darker = hex_to_rgb("#93A0D9")
col_wicked_darker = hex_to_rgb("#A6A17C")
col_active_darker = hex_to_rgb("#5B7DD9")

col_bg_lighter = hex_to_rgb("#F8A9EF")
col_wicked_lighter = hex_to_rgb("#F9D6C2")
col_active_lighter = hex_to_rgb("#F368F8")

col_correct = hex_to_rgb("#006A68")
col_error = hex_to_rgb("#ED1500")
col_error_2 = hex_to_rgb("#8F3633")

white = hex_to_rgb("#F2F1DF")

feature_text_col = hex_to_rgb("#FFCB96")
feature_bg = hex_to_rgb("#2E849E")

option_fg = hex_to_rgb("#68A834")
option_bg = hex_to_rgb("#F48F6C")

col_black = hex_to_rgb("#000030", cache=True)

col_bt_pressed = hex_to_rgb("#4E52AF")
col_bt_down = hex_to_rgb("#1D1313")
col_bt_text = hex_to_rgb("#FFFFFF", cache=True)

dark_green = hex_to_rgb("#008F30")
dark_red = hex_to_rgb("#F50600")

red1 = hex_to_rgb("#DE045B")
red2 = hex_to_rgb("#700F3C")

green1 = hex_to_rgb("#44803F")
green2 = hex_to_rgb("#146152")

mid_color = hex_to_rgb("#FFCD39")

palettes = []
palettes.append([green1, green2, red1, red2, mid_color])
# green and blue for green
# red and orange for red

palettes.append(
    [
        hex_to_rgb("#3DE073"),
        hex_to_rgb("#008F30"),
        hex_to_rgb("#F50600"),
        hex_to_rgb("#8F3633"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#00B3AD"),
        hex_to_rgb("#006663"),
        hex_to_rgb("#B33F00"),
        hex_to_rgb("#B33F00"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#18818C"),
        hex_to_rgb("#343D59"),
        hex_to_rgb("#D90707"),
        hex_to_rgb("#D40404"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#C2FFE0"),
        hex_to_rgb("#00B258"),
        hex_to_rgb("#FF8475"),
        hex_to_rgb("#FF1B00"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#598053"),
        hex_to_rgb("#204127"),
        hex_to_rgb("#CB0111"),
        hex_to_rgb("#8C030E"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#024959"),
        hex_to_rgb("#092140"),
        hex_to_rgb("#F24738"),
        hex_to_rgb("#BF2A2A"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#8AF084"),
        hex_to_rgb("#3FA339"),
        hex_to_rgb("#FFA6DA"),
        hex_to_rgb("#F083C3"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#0BDB15"),
        hex_to_rgb("#008F07"),
        hex_to_rgb("#DB0B62"),
        hex_to_rgb("#8F043E"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#21EB74"),
        hex_to_rgb("#009E41"),
        hex_to_rgb("#EB2E20"),
        hex_to_rgb("#9E150B"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#31EB8A"),
        hex_to_rgb("#029E4C"),
        hex_to_rgb("#EB4531"),
        hex_to_rgb("#9E1F11"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#57EB52"),
        hex_to_rgb("#1C9E18"),
        hex_to_rgb("#EB52A6"),
        hex_to_rgb("#9E2869"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#57EB8A"),
        hex_to_rgb("#1B9E49"),
        hex_to_rgb("#EB5C58"),
        hex_to_rgb("#9E2F2B"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#0EEB9B"),
        hex_to_rgb("#009E65"),
        hex_to_rgb("#EB370F"),
        hex_to_rgb("#9E2105"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#57EB29"),
        hex_to_rgb("#259E00"),
        hex_to_rgb("#EB28CA"),
        hex_to_rgb("#9E0084"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#A6EB54"),
        hex_to_rgb("#649E1E"),
        hex_to_rgb("#D354EB"),
        hex_to_rgb("#89199E"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#48EB9E"),
        hex_to_rgb("#169E5F"),
        hex_to_rgb("#EB5E49"),
        hex_to_rgb("#9E2411"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#0EEB7A"),
        hex_to_rgb("#2B9E62"),
        hex_to_rgb("#EB250E"),
        hex_to_rgb("#9E1000"),
        hex_to_rgb("#FAE55F"),
    ]
)
palettes.append(
    [
        hex_to_rgb("#55EB7D"),
        hex_to_rgb("#139E38"),
        hex_to_rgb("#EB5459"),
        hex_to_rgb("#9E191D"),
        hex_to_rgb("#FAE55F"),
    ]
)

palettes2 = []
palettes2.append(
    [
        hex_to_rgb("#55EB7D"),
        hex_to_rgb("#139E38"),
        hex_to_rgb("#EB5459"),
        hex_to_rgb("#9E191D"),
        hex_to_rgb("#FAE55F"),
    ]
)
