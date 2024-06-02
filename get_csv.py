import googlemaps.distance_matrix
import requests
import csv
import random
import googlemaps


def get_list(offset):
    url = "https://worldwide-restaurants.p.rapidapi.com/search"
    response = requests.post(url=url, headers={
        "x-rapidapi-host":"worldwide-restaurants.p.rapidapi.com",
        "x-rapidapi-key":"<RAPID_API_KEY>",
        "Content-Type":"application/json"
    }, json={
        "language": "en_EN",
        "location_id": "298656", ## Ankara
        "currency": "TRY",
        "offset": offset
    })

    if response.status_code != 200:
        return None
    
    data = []
    response_data = response.json()["results"]["data"]
    for restaurant in response_data:
        if "name" not in restaurant or "cuisine" not in restaurant or "price_level" not in restaurant or "rating" not in restaurant or "latitude" not in restaurant or "longitude" not in restaurant or "location_id" not in restaurant:
            continue

        name = restaurant["name"]
        cousine = ""
        for c in restaurant["cuisine"]:
            cousine += c["name"] + "/"
        cost = int(find_cost(restaurant["price_level"])*random.uniform(0.8, 1.2)*100)
        if "num_reviews" not in restaurant:
            restaurant["num_reviews"] = "0"
        reviews = restaurant["num_reviews"]
        score = restaurant["rating"]
        lat = restaurant["latitude"]
        lon = restaurant["longitude"]
        location_id = restaurant["location_id"]

        gmaps = googlemaps.Client(key="<MAPS_API_KEY>")
        origins = (lat, lon)
        destinations = ("39.9180091","32.8232624")
        time = gmaps.distance_matrix(origins, destinations)["rows"][0]["elements"][0]["duration"]["value"]

        data.append([name, cousine, cost, reviews, score, lat, lon, time, location_id])

    with open('test.csv', 'a', encoding='UTF8', newline='') as f:
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
    else:
        interval = price_level.split("-")
        level = (find_cost(interval[0]) + find_cost(interval[1])) / 2
    
    return level

if __name__ == "__main__":
    for i in range (0, 200, 20):
        get_list(i)