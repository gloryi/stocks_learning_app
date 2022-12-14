import csv

data_selected = []

with open("cities_1m.csv") as datafile:
    reader = csv.DictReader(datafile, delimiter=";")
    headers = reader.fieldnames
    for line in reader:
        ascii_name = line["ASCII Name"]
        country_name = line["Country name EN"]
        population = int(line["Population"])
        if population < 50000:
            continue
# 50 - 100 k for 1
# 100 - 200 k for 3
# 200 - 500 k for 4
# 500k - 1m for 5
# 1m to 2.5m for 6
# 2.5m + > for 10
        data_selected.append([ascii_name, country_name, population])

with open("world_cities_parsed.csv", "w") as datafile:
    writer = csv.writer(datafile)
    writer.writerows(data_selected)

