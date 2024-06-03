import csv
import random
import math
import numpy as np
import os
import json
import sys
import requests
import constants as c

def read_restaurant_data(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    restaurants = []
    with open(filepath, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            name = row[0]
            cuisines_string = row[1]
            cuisines = cuisines_string.split("/")
            cost = int(row[2])
            reviews = int(row[3])
            score = float(row[4])
            lat = float(row[5])
            lon = float(row[6])
            time = int(row[7]) // 60
            location_id = row[8]
            restaurants.append({
                "name": name,
                "cuisine": cuisines,
                "cost": cost,
                "reviews": reviews,
                "score": score,
                "lat": lat,
                "lon": lon,
                "time": time,
                "location_id": location_id
            })
    return restaurants

# Function to calculate distance between two coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lat2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# Function to calculate total score for a restaurant based on user preferences
def calculate_score(restaurant, max_budget, max_time, current_lat, current_lon):
    cost_score = max(0, (max_budget - restaurant["cost"]) / max_budget)
    time_score = max(0, (max_time - restaurant["time"]) / max_time)
    distance = calculate_distance(current_lat, current_lon, restaurant["lat"], restaurant["lon"])
    distance_score = max(0, (40 - distance) / 40)
    return cost_score + time_score + distance_score + restaurant["score"]

# Greedy search to find the best initial restaurant
def greedy_search(cuisine, max_budget, max_time, current_lat, current_lon, restaurants):
    best_restaurant = None
    best_score = -1
    for restaurant in restaurants:
        if cuisine in restaurant["cuisine"]:
            score = calculate_score(restaurant, max_budget, max_time, current_lat, current_lon)
            if score > best_score:
                best_score = score
                best_restaurant = restaurant
    return best_restaurant

# Genetic algorithm to optimize meal selection
def genetic_algorithm(cuisine, max_budget, max_time, current_lat, current_lon, restaurants, population_size=20, generations=50):
    def get_filtered_restaurants(budget, time):
        return [r for r in restaurants if cuisine in r["cuisine"] and r["cost"] <= budget and r["time"] <= time]

    filtered_restaurants = get_filtered_restaurants(max_budget, max_time)

    # If no restaurants are found within the constraints, relax the constraints
    budget_step = 50
    time_step = 10
    while not filtered_restaurants:
        max_budget += budget_step
        max_time += time_step
        filtered_restaurants = get_filtered_restaurants(max_budget, max_time)

    # Ensure the population size does not exceed the number of available restaurants
    population_size = min(population_size, len(filtered_restaurants))

    # Initialize population with random selection
    population = random.sample(filtered_restaurants, population_size)

    def crossover(parent1, parent2):
        return {
            "name": parent1["name"],
            "cuisine": parent1["cuisine"],
            "cost": (parent1["cost"] + parent2["cost"]) // 2,
            "reviews": (parent1["reviews"] + parent2["reviews"]) // 2,
            "score": (parent1["score"] + parent2["score"]) / 2,
            "lat": (parent1["lat"] + parent2["lat"]) / 2,
            "lon": (parent1["lon"] + parent2["lon"]) / 2,
            "time": (parent1["time"] + parent2["time"]) // 2,
        }

    def mutate(child):
        if random.random() < 0.2:  # Mutation chance
            child["cost"] = max(50, child["cost"] + random.randint(-50, 50))
            child["time"] = max(10, child["time"] + random.randint(-20, 20))
        return child

    for generation in range(generations):
        # Evaluate fitness
        fitness_scores = [calculate_score(restaurant, max_budget, max_time, current_lat, current_lon) for restaurant in population]

        # Selection
        selected = [population[i] for i in np.argsort(fitness_scores)[-population_size//2:] if fitness_scores[i] > 0]

        # If not enough valid selections, refill with random valid restaurants
        while len(selected) < population_size // 2:
            selected.append(random.choice(filtered_restaurants))

        # Crossover and mutation
        offspring = []
        while len(offspring) < population_size:
            if len(selected) < 2:
                break  # Avoid sampling when there are less than 2 selected restaurants
            parent1, parent2 = random.sample(selected, 2)
            child = mutate(crossover(parent1, parent2))
            if child["cost"] <= max_budget and child["time"] <= max_time:
                offspring.append(child)

        population = selected + offspring

    # Select the best solution from the original filtered restaurants
    best_solution = max(filtered_restaurants, key=lambda restaurant: calculate_score(restaurant, max_budget, max_time, current_lat, current_lon))
    return best_solution

def get_top_n_restaurants(restaurants, n, max_budget, max_time, current_lat, current_lon):
    scored_restaurants = [
        (restaurant, calculate_score(restaurant, max_budget, max_time, current_lat, current_lon))
        for restaurant in restaurants
    ]
    sorted_restaurants = sorted(scored_restaurants, key=lambda x: x[1], reverse=True)
    return [restaurant for restaurant, score in sorted_restaurants[:n]]

def get_restaurant_detail(location_id):
    response = requests.post(url=c.RAPID_API_SEARCH_URL, headers=c.RAPID_API_HEADERS, json={
        "language": c.EN,
        "location_id": location_id,
        "currency": c.TRY
    })

    if response.status_code != 200:
        return None
    
    return response.json()
    
if __name__ == "__main__":
    current_lat = float(sys.argv[1])
    current_lon = float(sys.argv[2])
    cuisine = sys.argv[3]
    max_budget = int(sys.argv[4])
    max_time = int(sys.argv[5])

    # Read restaurant data from CSV
    restaurants = read_restaurant_data(c.CSV_NAME)

    # Filter by cuisine
    filtered_restaurants = [r for r in restaurants if cuisine in r["cuisine"]]

    # Get top N restaurants using greedy search
    best_restaurant_greedy = [greedy_search(cuisine, max_budget, max_time, current_lat, current_lon, filtered_restaurants)]

    # Get the best restaurant using genetic algorithm
    best_restaurant_genetic = genetic_algorithm(cuisine, max_budget, max_time, current_lat, current_lon, filtered_restaurants)

    # Combine results
    greedy_details = get_restaurant_detail(best_restaurant_greedy[0]["location_id"])
    if greedy_details is not None:
        best_restaurant_greedy = greedy_details["results"]
    genetic_details = get_restaurant_detail(best_restaurant_genetic["location_id"])
    if genetic_details is not None:
        best_restaurant_genetic = genetic_details["results"]
    results = {
        "bestRestaurantGreedy": best_restaurant_greedy,
        "bestRestaurantGenetic": best_restaurant_genetic
    }
    print(json.dumps(results, indent=2))

    """
    results = "{\"status\":200,\"msg\":null,\"results\":{\"location_id\":\"15333482\",\"name\":\"Pago Restaurant\",\"latitude\":\"-6.923463\",\"longitude\":\"107.62351\",\"num_reviews\":\"1347\",\"timezone\":\"Asia/Jakarta\",\"location_string\":\"Bandung, West Java, Java\",\"photo\":{\"images\":{\"small\":{\"width\":\"150\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-l/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"150\"},\"thumbnail\":{\"width\":\"50\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-t/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"50\"},\"original\":{\"width\":\"750\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-o/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"500\"},\"large\":{\"width\":\"750\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-o/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"500\"},\"medium\":{\"width\":\"550\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-s/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"367\"}},\"is_blessed\":true,\"uploaded_date\":\"2018-11-23T05:50:14-0500\",\"caption\":\"Pago Balcony\",\"id\":\"360379394\",\"helpful_votes\":\"6\",\"published_date\":\"2018-11-23T05:50:14-0500\",\"user\":{\"user_id\":null,\"member_id\":\"0\",\"type\":\"user\"}},\"awards\":[],\"doubleclick_zone\":\"as.indonesia.java.bandung\",\"preferred_map_engine\":\"default\",\"raw_ranking\":\"4.94955587387085\",\"ranking_geo\":\"Bandung\",\"ranking_geo_id\":\"297704\",\"ranking_position\":\"2\",\"ranking_denominator\":\"1562\",\"ranking_category\":\"restaurant\",\"ranking\":\"Bandung içinde 2.561 yemek mekanı arasında 2. sırada\",\"distance\":null,\"distance_string\":null,\"bearing\":null,\"rating\":\"5.0\",\"is_closed\":false,\"open_now_text\":\"Şu Anda Kapalı\",\"is_long_closed\":false,\"price_level\":\"$$ - $$$\",\"price\":\"₺2.093.937 - ₺8.053.605\",\"description\":\"\",\"web_url\":\"https://www.tripadvisor.com.tr/Restaurant_Review-g297704-d15333482-Reviews-Pago_Restaurant-Bandung_West_Java_Java.html\",\"write_review\":\"https://www.tripadvisor.com.tr/UserReview-g297704-d15333482-Pago_Restaurant-Bandung_West_Java_Java.html\",\"ancestors\":[{\"subcategory\":[{\"key\":\"city\",\"name\":\"Şehir\"}],\"name\":\"Bandung\",\"abbrv\":null,\"location_id\":\"297704\"},{\"subcategory\":[{\"key\":\"province\",\"name\":\"İl\"}],\"name\":\"West Java\",\"abbrv\":null,\"location_id\":\"2301792\"},{\"subcategory\":[{\"key\":\"region\",\"name\":\"Bölge\"}],\"name\":\"Java\",\"abbrv\":null,\"location_id\":\"294228\"},{\"subcategory\":[{\"key\":\"country\",\"name\":\"Ülke\"}],\"name\":\"Endonezya\",\"abbrv\":null,\"location_id\":\"294225\"}],\"category\":{\"key\":\"restaurant\",\"name\":\"Restoran\"},\"subcategory\":[{\"key\":\"sit_down\",\"name\":\"Masaya servis\"}],\"parent_display_name\":\"Bandung\",\"is_jfy_enabled\":false,\"nearest_metro_station\":[],\"reviews\":[{\"title\":\"Papandayan'da Kahvaltı\",\"rating\":\"5\",\"published_date\":\"2020-02-20T14:49:14-05:00\",\"published_platform\":null,\"summary\":\"Deneyimlerim çok iyiydi. Gıda seçimi yaygın ve servis Alisha mükemmel oldu\",\"author\":\"njwong\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r746395198-Pago_Restaurant-Bandung_West_Java_Java.html#review746395198\",\"review_id\":\"746395198\",\"machine_translated\":false},{\"title\":\"İyi bir atmosfer restoran\",\"rating\":\"5\",\"published_date\":\"2019-12-13T15:51:06-05:00\",\"published_platform\":null,\"summary\":\"Bandung güzel otelde iyi bir atmosfer\\nMenü çeşitliliği, japon, güneş, batı, hint, çince vb. iyi tat. .\\n\\nGüzel hizmet için teşekkür ederiz Kang Gugum. .\",\"author\":\"ridohanggoro\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r732492565-Pago_Restaurant-Bandung_West_Java_Java.html#review732492565\",\"review_id\":\"732492565\",\"machine_translated\":false},{\"title\":\"Pago restoran kahvaltısı\",\"rating\":\"5\",\"published_date\":\"2019-12-13T15:41:03-05:00\",\"published_platform\":null,\"summary\":\"Mükemmel bir kahvaltı. . . . .\\nMükemmel ana yemek. . . .\\nMükemmel yemekler . . . .\\nMükemmel kahve. . . . .\\nMükemmel bir yer. . . .\\nBize iyi hizmet eden Bay Gugun için çok teşekkür ederim. . .\",\"author\":\"linapuspam\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r732491903-Pago_Restaurant-Bandung_West_Java_Java.html#review732491903\",\"review_id\":\"732491903\",\"machine_translated\":false}],\"phone\":\"+62 22 7310799\",\"website\":\"http://www.thepapandayan.com/dining/pago\",\"email\":\"info@thepapandayan.com\",\"address_obj\":{\"street1\":\"Jl. Gatot Subroto No.83\",\"street2\":\"The Papandayan Hotel\",\"city\":\"Bandung\",\"state\":null,\"country\":\"Endonezya\",\"postalcode\":\"40262\"},\"address\":\"Jl. Gatot Subroto No.83 The Papandayan Hotel, Bandung 40262 Endonezya\",\"hours\":{\"week_ranges\":[[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}]],\"timezone\":\"Asia/Jakarta\"},\"local_name\":\"Pago Restaurant\",\"local_address\":\"\",\"local_lang_code\":\"id\",\"is_candidate_for_contact_info_suppression\":false,\"cuisine\":[{\"key\":\"9908\",\"name\":\"Amerikan\"},{\"key\":\"10659\",\"name\":\"Asya\"},{\"key\":\"10690\",\"name\":\"Endonezya\"},{\"key\":\"10651\",\"name\":\"Barbekü\"},{\"key\":\"10665\",\"name\":\"Vejetaryen Dostu\"},{\"key\":\"10697\",\"name\":\"Vegan Seçenekleri\"},{\"key\":\"10751\",\"name\":\"Helal\"},{\"key\":\"10992\",\"name\":\"Glütensiz Seçenekler\"}],\"dietary_restrictions\":[{\"key\":\"10665\",\"name\":\"Vejetaryen Dostu\"},{\"key\":\"10697\",\"name\":\"Vegan Seçenekleri\"},{\"key\":\"10751\",\"name\":\"Helal\"},{\"key\":\"10992\",\"name\":\"Glütensiz Seçenekler\"}],\"menu_web_url\":\"http://thepapandayan.com/menu/pago.html\",\"establishment_category_ranking\":\"2/1.758 (Restoranlar) - Bandung\",\"meal_types\":[{\"key\":\"10597\",\"name\":\"Kahvaltı\"},{\"key\":\"10598\",\"name\":\"Öğle Yemeği\"},{\"key\":\"10599\",\"name\":\"Akşam Yemeği\"},{\"key\":\"10606\",\"name\":\"Brunch\"},{\"key\":\"10949\",\"name\":\"İçecekler\"}],\"establishment_types\":[{\"key\":\"10591\",\"name\":\"Restoranlar\"}],\"dishes\":[{\"key\":\"10891\",\"name\":\"İspanyol Izgarası\"}],\"sub_cuisine\":[],\"photo_count\":\"1000\",\"has_review_draft\":false,\"has_panoramic_photos\":false,\"rating_histogram\":{\"count_1\":\"4\",\"count_2\":\"1\",\"count_3\":\"5\",\"count_4\":\"19\",\"count_5\":\"1318\"}}}"
    results_greedy = "{\"status\":200,\"msg\":null,\"results\":{\"location_id\":\"15333482\",\"name\":\"Pago Restaurant\",\"latitude\":\"-6.923463\",\"longitude\":\"107.62351\",\"num_reviews\":\"1347\",\"timezone\":\"Asia/Jakarta\",\"location_string\":\"Bandung, West Java, Java\",\"photo\":{\"images\":{\"small\":{\"width\":\"150\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-l/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"150\"},\"thumbnail\":{\"width\":\"50\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-t/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"50\"},\"original\":{\"width\":\"750\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-o/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"500\"},\"large\":{\"width\":\"750\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-o/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"500\"},\"medium\":{\"width\":\"550\",\"url\":\"https://media-cdn.tripadvisor.com/media/photo-s/15/7a/f4/02/pago-balcony.jpg\",\"height\":\"367\"}},\"is_blessed\":true,\"uploaded_date\":\"2018-11-23T05:50:14-0500\",\"caption\":\"Pago Balcony\",\"id\":\"360379394\",\"helpful_votes\":\"6\",\"published_date\":\"2018-11-23T05:50:14-0500\",\"user\":{\"user_id\":null,\"member_id\":\"0\",\"type\":\"user\"}},\"awards\":[],\"doubleclick_zone\":\"as.indonesia.java.bandung\",\"preferred_map_engine\":\"default\",\"raw_ranking\":\"4.94955587387085\",\"ranking_geo\":\"Bandung\",\"ranking_geo_id\":\"297704\",\"ranking_position\":\"2\",\"ranking_denominator\":\"1562\",\"ranking_category\":\"restaurant\",\"ranking\":\"Bandung içinde 2.561 yemek mekanı arasında 2. sırada\",\"distance\":null,\"distance_string\":null,\"bearing\":null,\"rating\":\"5.0\",\"is_closed\":false,\"open_now_text\":\"Şu Anda Kapalı\",\"is_long_closed\":false,\"price_level\":\"$$ - $$$\",\"price\":\"₺2.093.937 - ₺8.053.605\",\"description\":\"\",\"web_url\":\"https://www.tripadvisor.com.tr/Restaurant_Review-g297704-d15333482-Reviews-Pago_Restaurant-Bandung_West_Java_Java.html\",\"write_review\":\"https://www.tripadvisor.com.tr/UserReview-g297704-d15333482-Pago_Restaurant-Bandung_West_Java_Java.html\",\"ancestors\":[{\"subcategory\":[{\"key\":\"city\",\"name\":\"Şehir\"}],\"name\":\"Bandung\",\"abbrv\":null,\"location_id\":\"297704\"},{\"subcategory\":[{\"key\":\"province\",\"name\":\"İl\"}],\"name\":\"West Java\",\"abbrv\":null,\"location_id\":\"2301792\"},{\"subcategory\":[{\"key\":\"region\",\"name\":\"Bölge\"}],\"name\":\"Java\",\"abbrv\":null,\"location_id\":\"294228\"},{\"subcategory\":[{\"key\":\"country\",\"name\":\"Ülke\"}],\"name\":\"Endonezya\",\"abbrv\":null,\"location_id\":\"294225\"}],\"category\":{\"key\":\"restaurant\",\"name\":\"Restoran\"},\"subcategory\":[{\"key\":\"sit_down\",\"name\":\"Masaya servis\"}],\"parent_display_name\":\"Bandung\",\"is_jfy_enabled\":false,\"nearest_metro_station\":[],\"reviews\":[{\"title\":\"Papandayan'da Kahvaltı\",\"rating\":\"5\",\"published_date\":\"2020-02-20T14:49:14-05:00\",\"published_platform\":null,\"summary\":\"Deneyimlerim çok iyiydi. Gıda seçimi yaygın ve servis Alisha mükemmel oldu\",\"author\":\"njwong\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r746395198-Pago_Restaurant-Bandung_West_Java_Java.html#review746395198\",\"review_id\":\"746395198\",\"machine_translated\":false},{\"title\":\"İyi bir atmosfer restoran\",\"rating\":\"5\",\"published_date\":\"2019-12-13T15:51:06-05:00\",\"published_platform\":null,\"summary\":\"Bandung güzel otelde iyi bir atmosfer\\nMenü çeşitliliği, japon, güneş, batı, hint, çince vb. iyi tat. .\\n\\nGüzel hizmet için teşekkür ederiz Kang Gugum. .\",\"author\":\"ridohanggoro\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r732492565-Pago_Restaurant-Bandung_West_Java_Java.html#review732492565\",\"review_id\":\"732492565\",\"machine_translated\":false},{\"title\":\"Pago restoran kahvaltısı\",\"rating\":\"5\",\"published_date\":\"2019-12-13T15:41:03-05:00\",\"published_platform\":null,\"summary\":\"Mükemmel bir kahvaltı. . . . .\\nMükemmel ana yemek. . . .\\nMükemmel yemekler . . . .\\nMükemmel kahve. . . . .\\nMükemmel bir yer. . . .\\nBize iyi hizmet eden Bay Gugun için çok teşekkür ederim. . .\",\"author\":\"linapuspam\",\"url\":\"http://www.tripadvisor.com.tr/ShowUserReviews-g297704-d15333482-r732491903-Pago_Restaurant-Bandung_West_Java_Java.html#review732491903\",\"review_id\":\"732491903\",\"machine_translated\":false}],\"phone\":\"+62 22 7310799\",\"website\":\"http://www.thepapandayan.com/dining/pago\",\"email\":\"info@thepapandayan.com\",\"address_obj\":{\"street1\":\"Jl. Gatot Subroto No.83\",\"street2\":\"The Papandayan Hotel\",\"city\":\"Bandung\",\"state\":null,\"country\":\"Endonezya\",\"postalcode\":\"40262\"},\"address\":\"Jl. Gatot Subroto No.83 The Papandayan Hotel, Bandung 40262 Endonezya\",\"hours\":{\"week_ranges\":[[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}],[{\"open_time\":360,\"close_time\":1380}]],\"timezone\":\"Asia/Jakarta\"},\"local_name\":\"Pago Restaurant\",\"local_address\":\"\",\"local_lang_code\":\"id\",\"is_candidate_for_contact_info_suppression\":false,\"cuisine\":[{\"key\":\"9908\",\"name\":\"Amerikan\"},{\"key\":\"10659\",\"name\":\"Asya\"},{\"key\":\"10690\",\"name\":\"Endonezya\"},{\"key\":\"10651\",\"name\":\"Barbekü\"},{\"key\":\"10665\",\"name\":\"Vejetaryen Dostu\"},{\"key\":\"10697\",\"name\":\"Vegan Seçenekleri\"},{\"key\":\"10751\",\"name\":\"Helal\"},{\"key\":\"10992\",\"name\":\"Glütensiz Seçenekler\"}],\"dietary_restrictions\":[{\"key\":\"10665\",\"name\":\"Vejetaryen Dostu\"},{\"key\":\"10697\",\"name\":\"Vegan Seçenekleri\"},{\"key\":\"10751\",\"name\":\"Helal\"},{\"key\":\"10992\",\"name\":\"Glütensiz Seçenekler\"}],\"menu_web_url\":\"http://thepapandayan.com/menu/pago.html\",\"establishment_category_ranking\":\"2/1.758 (Restoranlar) - Bandung\",\"meal_types\":[{\"key\":\"10597\",\"name\":\"Kahvaltı\"},{\"key\":\"10598\",\"name\":\"Öğle Yemeği\"},{\"key\":\"10599\",\"name\":\"Akşam Yemeği\"},{\"key\":\"10606\",\"name\":\"Brunch\"},{\"key\":\"10949\",\"name\":\"İçecekler\"}],\"establishment_types\":[{\"key\":\"10591\",\"name\":\"Restoranlar\"}],\"dishes\":[{\"key\":\"10891\",\"name\":\"İspanyol Izgarası\"}],\"sub_cuisine\":[],\"photo_count\":\"1000\",\"has_review_draft\":false,\"has_panoramic_photos\":false,\"rating_histogram\":{\"count_1\":\"4\",\"count_2\":\"1\",\"count_3\":\"5\",\"count_4\":\"19\",\"count_5\":\"1318\"}}}"
    results_json = json.loads(results)
    results_greedy_json = json.loads(results_greedy)
    results_last = {
        "bestRestaurantGreedy": results_greedy_json,
        "bestRestaurantGenetic": results_json
    }

    print(json.dumps(results_last, indent=2))
    """

