import csv

## get cuisines from restaurants.csv
## and unique cuisines

cuisines = []
with open("restaurants.csv", mode='r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        cuisines_string = row[1][:-1]
        cuisines.extend(cuisines_string.split("/"))

unique_cuisines = set(cuisines)
unique_cuisines.remove("")

print(unique_cuisines)
