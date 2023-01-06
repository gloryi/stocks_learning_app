import os
import csv
import random
target_directory = "/home/gloryi/Pictures/FlickrSets/stocks_datasets"
#target_directory = "/home/gloryi/Pictures/MovieShots"
#target_directory = "/home/gloryi/Pictures/OldPhotos"
#target_directory = "/home/gloryi/Pictures/Windows 10 Spotlight"
#target_directory = os.path.join(os.getcwd(), "stocks_datasets") 
selected_files = []

for _r, _d, _f in os.walk(target_directory):
    for f in _f:
        selected_files.append(os.path.join(_r, f))

def generate_random_positions(selected_file):
    random_pos = random.randint(250,99000)
    for incr in range(10):
        yield random_pos+incr*30


target_lines = []
for i in range(200):
    active_file = random.choice(selected_files)
    for line_pos in generate_random_positions(active_file):
        target_lines.append([active_file, line_pos])

with open("stocks_data.csv", "w") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(target_lines)


