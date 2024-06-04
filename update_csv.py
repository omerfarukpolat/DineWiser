import csv
import os
import googlemaps
import datetime
import constants as c
import project as p

def update_csv(dest_lat, dest_lon):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(script_dir, c.CSV_NAME)
    restaurants = []
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            lat = float(row[5])
            lon = float(row[6])
            time_sec = get_time((lat, lon), (dest_lat, dest_lon)) # Seconds
            row[7] = time_sec
            restaurants.append(row)

    # New filename with timestamp: "restaurants-YYYY-MM-DD-HH-MM-SS.csv"
    now = datetime.datetime.now()
    new_csv_name = "restaurants_" + now.strftime("%Y-%m-%d-%H-%M-%S") + ".csv"
    new_csv_file_path = os.path.join(script_dir, new_csv_name)
    with open(new_csv_file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(restaurants)

    return new_csv_name
        
def get_time(origins, destinations):
    gmaps = googlemaps.Client(key=c.MAPS_API_TOKEN)
    return gmaps.distance_matrix(origins, destinations)["rows"][0]["elements"][0]["duration"]["value"]
    
# Test
""""
def main():
    new_csv_name = update_csv(39.9334, 32.8597)
    print(f"New CSV file is created: {new_csv_name}")

if __name__ == "__main__":
    main()
"""