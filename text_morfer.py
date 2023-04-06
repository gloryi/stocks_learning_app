import random
import time
from zalgo_text import zalgo


class textMorfer:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(textMorfer, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.seed = time.time()
        random.seed(self.seed)
        self.glith_glyphs = "!@#$%^&*(){}[]|;:'<>,./?~ "
        self.a = [
            "a",
            "4",
            "@",
            "/-\\",
            "/\\",
            "/_\\",
            "^",
            "aye",
            "ci",
            "λ",
            "∂",
            "//-\\\\",
            "/=\\",
            "ae",
        ]
        self.b = [
            "b",
            "8",
            "|3",
            "6",
            "13",
            "l3",
            "]3",
            "|o",
            "1o",
            "lo",
            "ß",
            "]]3",
            "|8",
            "l8",
            "18",
            "]8",
        ]
        self.c = ["c", "(", "<", "[", "{", "sea", "see", "k", "©", "¢", "€"]
        self.d = [
            "d",
            "|]",
            "l]",
            "1]",
            "|)",
            "l)",
            "1)",
            "[)",
            "|}",
            "l]",
            "1}",
            "])",
            "i>",
            "|>",
            "l>",
            "1>",
            "0",
            "cl",
            "o|",
            "o1",
            "ol",
            "Ð",
            "∂",
            "ð",
        ]
        self.e = ["e", "3", "&", "[-", "€", "ii", "ə", "£", "iii"]
        self.f = ["f", "|=", "]=", "}", "ph", "(=", "[=", "ʃ", "eph", "ph"]
        self.g = [
            "g",
            "6",
            "9",
            "&",
            "(_+",
            "C-",
            "gee",
            "jee",
            "(Y,",
            "cj",
            "[",
            "-",
            "(γ,",
            "(_-",
        ]
        self.h = [
            "h",
            "|-|",
            "#",
            "[-]",
            "{-}",
            "]-[",
            ")-(",
            "(-)",
            ":-:",
            "}{",
            "}-{",
            "aych",
            "╫",
            "]]-[[",
            "aech",
        ]
        self.i = ["!", "1", "|", "l", "eye", "3y3", "ai", "i"]
        self.j = [
            "j",
            "_|",
            "_/",
            "]",
            "</",
            "_)",
            "_l",
            "_1",
            "¿",
            "ʝ",
            "ul",
            "u1",
            "u|",
            "jay",
            "(/",
            "_]",
        ]
        self.k = ["k", "x", "|<", "|x", "|{", "/<", "\\<", "/x", "\\x", "ɮ", "kay"]
        self.l = ["l", "1", "7", "|_", "1_", "l_", "lJ", "£", "¬", "el"]
        self.m = [
            "m",
            "/\/\\",
            "|\\/|",
            "em",
            "|v|",
            "[v]",
            "^^",
            "nn",
            "//\\\\//\\\\",
            "(V)",
            "(\/)",
            "/|\\",
            "/|/|",
            ".\\\\",
            "/^^\\",
            "/V\\",
            "|^^|",
            "JVL",
            "][\\\\//][",
            "[]\/[]",
            "[]v[]",
            "(t)",
        ]
        self.n = [
            "n",
            "|\\|",
            "/\\/",
            "//\\\\//",
            "[\\]",
            "<\\>",
            "{\\}",
            "//",
            "[]\\[]",
            "]\\[",
            "~",
            "₪",
            "/|/",
            "in",
        ]
        self.o = ["o", "0", "()", "oh", "[]", "{}", "¤", "Ω", "ω", "*", "[[]]", "oh"]
        self.p = [
            "p",
            "|*",
            "l*",
            "1*",
            "|o",
            "lo",
            "1o",
            "|>",
            "l>",
            "1>",
            '|"',
            'l"',
            '1"',
            "?",
            "9",
            "[]d",
            "|7",
            "l7",
            "17",
            "q",
            "|d",
            "ld",
            "1d",
            "℗",
            "|º",
            "1º",
            "lº",
            "þ",
            "¶",
            "pee",
        ]
        self.q = [
            "q",
            "0_",
            "o_",
            "0,",
            "o,",
            "(,)",
            "[,]",
            "<|",
            "<l",
            "<1",
            "cue",
            "9",
            "¶",
            "kew",
        ]
        self.r = [
            "r",
            "|2",
            "l2",
            "12",
            "2",
            "/2",
            "I2",
            "|^",
            "l^",
            "1^",
            "|~",
            "l~",
            "1~",
            "lz",
            "[z",
            "|`",
            "l`",
            "1`",
            ".-",
            "®",
            "Я",
            "ʁ",
            "|?",
            "l?",
            "1?",
            "arr",
        ]
        self.s = ["s", "5", "$", "z", "es", "2", "§", "š", ",,\\``"]
        self.t = ["t", "7", "+", "-|-", "-l-", "-1-", "1", "']['", "†"]
        self.u = [
            "u",
            "|_|",
            "l_l",
            "1_1",
            "(_)",
            "[_]",
            "{_}",
            "y3w",
            "m",
            "\\_/",
            "\\_\\",
            "/_/",
            "µ",
            "yew",
            "yoo",
            "yuu",
        ]
        self.v = ["v", "\\/", "\\\\//", "√"]
        self.w = [
            "w",
            "\\/\\/",
            "vv",
            "'//",
            "\\\\'",
            "\\^/",
            "(n)",
            "\\x/",
            "\\|/",
            "\\_|_/",
            "\\_l_/",
            "\\_1_/",
            "\\//\\//",
            "\\_:_/",
            "]i[",
            "uu",
            "Ш",
            "ɰ",
            "1/\\/",
            "\\/1/",
            "1/1/",
        ]
        self.x = ["x", "%", "><", "><,", "}{", "ecks", "x", "*", ")(", "ex", "Ж", "×"]
        self.y = [
            "y",
            "j",
            "`/",
            "`(",
            "-/",
            "'/",
            "\\-/",
            "Ψ",
            "φ",
            "λ",
            "Ч",
            "¥",
            "``//",
            "\\j",
            "wai",
        ]
        self.z = ["z", "2", "~/_", "%", "7_", "ʒ", "≥", "`/_"]
        self.zero = ["0", "o", "zero", "cero", "()"]
        self.one = ["1", "won", "one", "l", "|", "]["]
        self.two = ["two", "to", "too", "2", "z"]
        self.three = ["e", "3", "three"]
        self.four = ["4", "four", "for", "fore", "a"]
        self.five = ["5", "five", "s"]
        self.six = ["6", "six", "g"]
        self.seven = ["7", "seven", "t", "l"]
        self.eight = ["8", "eight", "b"]
        self.nine = ["9", "nine", "g"]

        # "0":self.zero,"1":self.one,"2":self.two,"3":self.three,"4":self.four,"5":self.five,"6":self.six,"7":self.seven,"8":self.eight,"9":self.nine
        self.alphabet = {
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
            "e": self.e,
            "f": self.f,
            "g": self.g,
            "h": self.h,
            "i": self.i,
            "j": self.j,
            "k": self.k,
            "l": self.l,
            "m": self.m,
            "n": self.n,
            "o": self.o,
            "p": self.p,
            "q": self.q,
            "r": self.r,
            "s": self.s,
            "t": self.t,
            "u": self.u,
            "v": self.v,
            "w": self.w,
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
        self.alphabet_2 = {"#": ["#", "@", "*", "$", "%", "^", "&", "=", "♡", "♥"]}

    def update_seed(self):
        self.seed = time.time()
        random.seed(self.seed)

    def double_letters(self, word):
        return re.sub(r"(.)\1", r"\1" + u"\u0305", word)

    def vovels(self, word):
        word = re.sub(r"(.)a", r"\1" + u"\u0302", word)
        word = re.sub(r"(.)e", r"\1" + u"\u030E", word)
        return word

    def constant_ipa(self, word):
        contant_dict = {}
        contant_dict["th"] = "ð"
        contant_dict["sh"] = "ʃ"
        contant_dict["ing"] = "ŋ"
        contant_dict["ё"] = "ɵ"
        for key in contant_dict.keys():
            if key in word.lower():
                word = re.sub(key, contant_dict[key], word.lower(), re.IGNORECASE)
        return word

    def modify_word(self, word):
        word = constant_ipa(word)
        word = vovels(word)
        word = double_letters(word)
        return wod

    def morf_text(self, text):
        # Case morfer
        random.seed(self.seed)
        text = "".join(_ if random.randint(0, 20) < 15 else _.upper() for _ in text)
        text = "".join(_ if random.randint(0, 20) < 15 else _.lower() for _ in text)
        # text = "".join(_ if random.randint(0,30) < 29 else random.choice(self.glith_glyphs) for _ in text)
        text = "".join(
            _
            if random.randint(0, 30) < 29
            else random.choice(self.alphabet[_.lower()])
            if _.lower() in self.alphabet
            else _
            for _ in text
        )
        text = "".join(
            _
            if random.randint(0, 10) < 5
            else random.choice(self.alphabet_2[_])
            if _ in self.alphabet_2
            else _
            for _ in text
        )
        # text = "".join(_ if random.randint(0,20)<19 else zalgo.zalgo().zalgofy(_) for _ in text)
        return text
