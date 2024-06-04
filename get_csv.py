import googlemaps.distance_matrix
import requests
import csv
import os
import random
import googlemaps
import constants as c


def get_list(offset):
    response = requests.post(url=c.RAPID_API_SEARCH_URL, headers=c.RAPID_API_HEADERS, json={
        "language": c.EN,
        "location_id": c.ANKARA_LOCATION_ID,
        "currency": c.TRY,
        "offset": offset
    })
    if response.status_code != 200:
        return None
    
    data = []
    response_data = response.json()["results"]["data"]
    for restaurant in response_data:
        if "name" not in restaurant or "cuisine" not in restaurant or \
            "price_level" not in restaurant or "rating" not in restaurant or \
                "latitude" not in restaurant or "longitude" not in restaurant or \
                    "location_id" not in restaurant:
            continue

        name = restaurant["name"]
        cuisines = ""
        for cuisine in restaurant["cuisine"]:
            cuisines += cuisine["name"] + "/"
        cuisines = cuisines[:-1]
        cost = int(find_cost(restaurant["price_level"])*random.uniform(0.8, 1.2)*100)
        if "num_reviews" not in restaurant:
            restaurant["num_reviews"] = "0"
        reviews = restaurant["num_reviews"]
        score = restaurant["rating"]
        lat = restaurant["latitude"]
        lon = restaurant["longitude"]
        location_id = restaurant["location_id"]
        time = random.randint(200, 1500)

        data.append([name, cuisines, cost, reviews, score, lat, lon, time, location_id])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(script_dir, c.CSV_NAME)
    with open(csv_file_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def find_cost(price_level):
    price_level = price_level.replace(" ", "")
    if price_level == "":
        level = random.uniform(1, 5)
    elif price_level == "$":
        level = 1
    elif price_level == "$$":
        level = 2
    elif price_level == "$$$":
        level = 3
    elif price_level == "$$$$":
        level = 4
    elif price_level == "$$$$$":
        level = 5
    elif "-" in price_level:
        interval = price_level.split("-")
        level = (find_cost(interval[0]) + find_cost(interval[1])) / 2
    else:
        level = 5
    
    return level

if __name__ == "__main__":
    for i in range (0, 5000, 20):
        get_list(i)