import pygame


class backend_switch:
    def get_backend_ref(self):
        return pygame_backend()


class pygame_backend:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(pygame_backend, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._api = pygame

        self.keys_mapping = {}

        self.keys_mapping["q"] = self._api.K_q 
        self.keys_mapping["w"] = self._api.K_w 
        self.keys_mapping["e"] = self._api.K_e 
        self.keys_mapping["r"] = self._api.K_r 
        self.keys_mapping["t"] = self._api.K_t 
        self.keys_mapping["y"] = self._api.K_y 
        self.keys_mapping["u"] = self._api.K_u 
        self.keys_mapping["i"] = self._api.K_i 
        self.keys_mapping["o"] = self._api.K_o 
        self.keys_mapping["p"] = self._api.K_p 
        self.keys_mapping["a"] = self._api.K_a 
        self.keys_mapping["s"] = self._api.K_s 
        self.keys_mapping["d"] = self._api.K_d 
        self.keys_mapping["f"] = self._api.K_f 
        self.keys_mapping["g"] = self._api.K_g 
        self.keys_mapping["h"] = self._api.K_h 
        self.keys_mapping["j"] = self._api.K_j 
        self.keys_mapping["k"] = self._api.K_k 
        self.keys_mapping["l"] = self._api.K_l 
        self.keys_mapping["z"] = self._api.K_z 
        self.keys_mapping["x"] = self._api.K_x 
        self.keys_mapping["c"] = self._api.K_c 
        self.keys_mapping["v"] = self._api.K_v 
        self.keys_mapping["b"] = self._api.K_b 
        self.keys_mapping["n"] = self._api.K_n 
        self.keys_mapping["m"] = self._api.K_m 
        self.keys_mapping[" "] = self._api.K_SPACE
        self.keys_mapping["return"] = self._api.K_RETURN
        self.keys_mapping["backspace"] = self._api.K_BACKSPACE
        self.keys_mapping["rshift"] = self._api.K_RSHIFT
        self.keys_mapping["lshift"] = self._api.K_LSHIFT
        self.keys_mapping["\t"] = self._api.K_TAB
        self.keys_mapping["!"] = self._api.K_EXCLAIM
        self.keys_mapping["\""] = self._api.K_QUOTEDBL
        self.keys_mapping["\'"] = self._api.K_QUOTE
        self.keys_mapping["#"] = self._api.K_HASH
        self.keys_mapping["$"] = self._api.K_DOLLAR
        self.keys_mapping["%"] = self._api.K_AMPERSAND
        self.keys_mapping["("] = self._api.K_LEFTPAREN
        self.keys_mapping[")"] = self._api.K_RIGHTPAREN
        self.keys_mapping["*"] = self._api.K_ASTERISK
        self.keys_mapping["+"] = self._api.K_PLUS
        self.keys_mapping[","] = self._api.K_COMMA
        self.keys_mapping["-"] = self._api.K_MINUS
        self.keys_mapping["."] = self._api.K_PERIOD
        self.keys_mapping["/"] = self._api.K_SLASH
        self.keys_mapping["0"] = self._api.K_0
        self.keys_mapping["1"] = self._api.K_1
        self.keys_mapping["2"] = self._api.K_2
        self.keys_mapping["3"] = self._api.K_3
        self.keys_mapping["4"] = self._api.K_4
        self.keys_mapping["5"] = self._api.K_5
        self.keys_mapping["6"] = self._api.K_6
        self.keys_mapping["7"] = self._api.K_7
        self.keys_mapping["8"] = self._api.K_8
        self.keys_mapping["9"] = self._api.K_9
        self.keys_mapping[":"] = self._api.K_COLON
        self.keys_mapping[";"] = self._api.K_SEMICOLON
        self.keys_mapping["<"] = self._api.K_LESS
        self.keys_mapping["="] = self._api.K_EQUALS
        self.keys_mapping[">"] = self._api.K_GREATER
        self.keys_mapping["?"] = self._api.K_QUESTION
        self.keys_mapping["@"] = self._api.K_AT
        self.keys_mapping["["] = self._api.K_LEFTBRACKET
        self.keys_mapping["\\"] = self._api.K_BACKSLASH
        self.keys_mapping["]"] = self._api.K_RIGHTBRACKET
        self.keys_mapping["^"] = self._api.K_CARET
        self.keys_mapping["_"] = self._api.K_UNDERSCORE
        self.keys_mapping["`"] = self._api.K_BACKQUOTE

    def api(self):
        return self._api

    def draw(self):
        return self._api.draw

    def draw_line(self, display, col, P1, P2, strk, *args, **kwards):
        self.draw().line(display, col, P1, P2, strk, *args, **kwards)

    def get_key_code(self, key):
        if key in self.keys_mapping:
            return self.keys_mapping[key]
        else:
            print(f"key {key} is undefined")
            return self.keys_mapping[" "]

    def get_pressed_keys(self):
        return self.api().key.get_pressed() 

    def bake_font(self, font_path, font_size, *args, **kvards):
        return self.api().font.Font(font_path, font_size)

