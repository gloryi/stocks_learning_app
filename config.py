import os
from collections import OrderedDict
import random
import subprocess

sets_prefix = os.path.join(os.getcwd(), "learning_sets")

# POSITIVE_TEST = True
POSITIVE_TEST = False

TEST = True
#TEST = False

def locate_set(_):
    return os.path.join(sets_prefix, _)

LEARNING_FOLDERS = []
if not TEST:
    LEARNING_FOLDERS.append(locate_set("fx_30"))
    LEARNING_FOLDERS.append(locate_set("fx_60"))
    LEARNING_FOLDERS.append(locate_set("cm_30"))
    LEARNING_FOLDERS.append(locate_set("cm_60"))
    LEARNING_FOLDERS.append(locate_set("legacy"))
else:
    LEARNING_FOLDERS.append(locate_set("test_set"))

# random.seed(time())
LEARNING_SET_FOLDER = random.choice(LEARNING_FOLDERS)

META_SCRIPT = os.path.join(os.getcwd(), "trading_affirmations.csv")

STOCKS_DATA = os.path.join(LEARNING_SET_FOLDER, "data.csv")
_META_SCRIPT = os.path.join(LEARNING_SET_FOLDER, "trading_affirmations.csv")
PROGRESSION_FILE = os.path.join(LEARNING_SET_FOLDER, "progress.json")
IMAGES_MAPPING_FILE = os.path.join(LEARNING_SET_FOLDER, "images_mapping.json")
_SET_CONFIG = os.path.join(LEARNING_SET_FOLDER, "config.json")

CHINESE_FONT = os.path.join(os.getcwd(), "fonts", "simhei.ttf")
CYRILLIC_FONT = os.path.join(os.getcwd(), "fonts", "Inter_font.ttf")

META_ACTION = os.path.join(
    "/home/gloryi/Documents/SpecialFiles", "action_affirmations.csv"
)
META_ACTION_STACK = OrderedDict()
META_ACTION_STACK["*** 1XBACK ***"] = []
META_ACTION_STACK["*** 1XKEYS ***"] = []
META_ACTION_STACK["*** 1XTEXT ***"] = []
META_ACTION_STACK["*** IBACK ***"] = []
META_ACTION_STACK["*** IBACKV ***"] = []
META_ACTION_STACK["*** MU ***"] = []
META_ACTION_STACK["*** PERM ***"] = []
META_ACTION_STACK["*** OUT ***"] = []

META_DIR = os.path.join(os.getcwd(), "Knowledge")
META_MINOR_DIR = os.path.join(os.getcwd(), "Affirm")
IMAGES_MINOR_DIR = os.path.join("/home/gloryi/Pictures/Lightning")

MONITORING_LIST = os.path.join(os.getcwd(), "data_collector", "capital_asset_urls.csv")

HAPTIC_PATH = "/home/gloryi/Documents/SpecialFiles/xbox_haptic/haptic_ultimate"
DEVICE_NAME = "/dev/input/by-id/usb-Microsoft_Controller_7EED82417161-event-joystick"

def HAPTIC_FEEDBACK(lower_freq=500, higher_freq=50000, duration=995):
    command = " ".join([HAPTIC_PATH, DEVICE_NAME,
                        str(lower_freq), str(higher_freq), str(duration)])
    subprocess.Popen(command, shell=True)

REPORTS_FILE = os.path.join("/home/gloryi/Documents/SpecialFiles", "results.csv")

BPM = 10

W = int(2800)
H = int(1425)

HIGHER_TIMEFRAME_SCALE = 16
MID_TIMEFRAME_SCALE = 2
MID_TIMEFRAME_SCALE_2 = 8
# VISUAL_PART = 350
GENERATION_TIME_SIZE = 140
VISUAL_PART = 180
STAKE_PART = 8
