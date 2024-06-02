import csv
import random
import math
import numpy as np
import os
import json
import sys

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


if __name__ == "__main__":
    current_lat, current_lon = 39.888470, 32.827494  # Ankara coordinates
    cuisine = "American"
    max_budget = 200
    max_time = 60  # in minutes

    # Read restaurant data from CSV
    restaurants = read_restaurant_data('restaurants.csv')

    # Filter by cuisine
    filtered_restaurants = [r for r in restaurants if cuisine == r["cuisine"]]

    # Get top N restaurants using greedy search
    top_restaurants_greedy = [greedy_search(cuisine, max_budget, max_time, current_lat, current_lon, restaurants)]

    # Get the best restaurant using genetic algorithm
    best_restaurant_genetic = genetic_algorithm(cuisine, max_budget, max_time, current_lat, current_lon, restaurants)

    # Combine results
    results = {
        "topRestaurantsGreedy": top_restaurants_greedy,
        "bestRestaurantGenetic": best_restaurant_genetic
    }

    print(json.dumps(results, indent=2))
