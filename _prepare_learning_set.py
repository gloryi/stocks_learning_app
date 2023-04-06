import os
import csv
import random
import json
from collections import defaultdict

NUM_CHAINS = 100
NUM_ELEMENTS = NUM_CHAINS*5

sets_prefix = os.path.join(os.getcwd(), "learning_sets")

def locate_set(_):
    return os.path.join(sets_prefix, _)

# target_set = "fx_30"
# target_set = "fx_60"
# target_set = "cm_30"
# target_set = "cm_60"
# target_set = "test_set"

target_set = "cm_60"
target_dir = locate_set(target_set)

if not os.path.exists(target_dir):
    os.mkdir(target_dir)

data_directory = os.path.join("/home/gloryi/Documents/SpecialFiles/stocks_data", target_set)

if not os.path.exists(data_directory):
    print(f"Data files for {target_set} are not prepared")
    exit()

selected_files = []

for _r, _d, _f in os.walk(data_directory):
    for f in _f:
        selected_files.append(os.path.join(_r, f))


def generate_random_positions(selected_file):
    random_pos = random.randint(10000, 90000)
    for incr in range(5):
        yield random_pos + incr * 30


target_lines = []
for i in range(NUM_CHAINS):
    active_file = random.choice(selected_files)
    for line_pos in generate_random_positions(active_file):
        target_lines.append([active_file, line_pos])

with open(os.path.join(os.getcwd(), "learning_sets", target_set,  "data.csv"), "w") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(target_lines)

########################################
########################################
########################################
##################### ADD IMAGES MAPPING
########################################
########################################
########################################

images_dirs = []
images_dirs.append("/home/gloryi/Pictures/FlickrSets")
images_dirs.append("/home/gloryi/Pictures/MovieShots")
images_dirs.append("/home/gloryi/Pictures/OldPhotos")
images_dirs.append("/home/gloryi/Pictures/Windows 10 Spotlight")

sets_dir = os.path.join(os.getcwd(), "learning_sets")
set_dir = os.path.join(sets_dir, target_set)

TARGET_NAME = os.path.join(set_dir, "images_mapping.json")

def extract_images_from_root(root_dir):
    images = []
    for _r, _d, _f in os.walk(root_dir):
        for f in _f:
            if ".png" or ".jpg" in f:
                images.append(os.path.join(_r, f))
    return images

images = []
for directory in images_dirs:
    images += extract_images_from_root(directory)

print(f"target {set_dir}")
print(f"images registered {len(images)}")

random.shuffle(images)

images_prepared = images[:NUM_ELEMENTS]


mapping_to_data = defaultdict(list)

for I, i in enumerate(range(0, len(images_prepared), 5)):
    for j in range(5):
        mapping_to_data[I].append(images_prepared[i + j])

with open(TARGET_NAME, "w") as jsonfile:
    json.dump(mapping_to_data, jsonfile, indent=2)
