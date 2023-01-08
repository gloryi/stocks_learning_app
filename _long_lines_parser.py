import csv
import os

lines = []
with open("trading_affirmations.csv") as origin_file:
    reader = csv.reader(origin_file)
    for line in reader:
        lines.append(line)

out_lines = []
line = lines.pop(0)[0]

while lines:

    if len(line) < 200:
        try:
            line += " " + lines.pop(0)[0]
        except:
            pass

    if len(line)>=200:
        out_lines.append([line+"."])
        line = ""

with open("trading_affirmations_ex.csv", "w+") as origin_file:
    writer = csv.writer(origin_file)
    writer.writerows(out_lines)
