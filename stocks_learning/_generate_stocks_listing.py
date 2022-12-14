import os
import csv
import random

target_directory = os.path.join(os.getcwd(), "stocks_datasets") 
selected_files = []

for _r, _d, _f in os.walk(target_directory):
    for f in _f:
        selected_files.append(os.path.join(_r, f))

target_lines = []
for i in range(1000):
    active_file = random.choice(selected_files)
    target_lines.append([active_file, random.randint(100,99000)])

with open("stocks_data.csv", "w") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(target_lines)


