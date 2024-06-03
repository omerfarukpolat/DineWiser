import csv
import json
import os
import constants as c

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, c.CSV_NAME)

cuisines = []
with open(csv_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        cuisines_string = row[1][:-1]
        cuisines.extend(cuisines_string.split("/"))

unique_cuisines = set(cuisines)
unique_cuisines.remove("")

print(json.dumps(list(unique_cuisines)))
