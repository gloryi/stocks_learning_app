import os
STOCKS_DATA = os.path.join(os.getcwd(), "stocks_data.csv")
PROGRESSION_FILE = os.path.join(os.getcwd(), "stocks_progress.json")
IMAGES_MAPPING_FILE = os.path.join(os.getcwd(), "dataset_mapping_2500.json")
CHINESE_FONT = os.path.join(os.getcwd(), "fonts", "simhei.ttf")
CYRILLIC_FONT = os.path.join(os.getcwd(), "fonts", "Inter_font.ttf")
META_SCRIPT = os.path.join(os.getcwd(), "trading_affirmations.csv")

META_ACTION = os.path.join(os.getcwd(), "action_affirmations.csv")
META_DIR = os.path.join(os.getcwd(), "Knowledge")
META_MINOR_DIR = os.path.join(os.getcwd(), "Affirm")
IMAGES_MINOR_DIR = os.path.join("/home/gloryi/Pictures/Lightning")

MONITORING_LIST = os.path.join(os.getcwd(), "data_collector", "capital_asset_urls.csv")

HAPTIC_FEEDBACK_CMD = os.path.join(os.getcwd(), "controller_features", "example.sh")
HAPTIC_ERROR_CMD = os.path.join(os.getcwd(), "controller_features", "error.sh")
HAPTIC_CORRECT_CMD = os.path.join(os.getcwd(), "controller_features", "correct.sh")

BPM = 10

W = int(2800)
H = int(1425)

HIGHER_TIMEFRAME_SCALE = 16
MID_TIMEFRAME_SCALE = 2
MID_TIMEFRAME_SCALE_2 = 8
#VISUAL_PART = 350
GENERATION_TIME_SIZE = 140
VISUAL_PART = 300
STAKE_PART = 15
