"""
gmaps = googlemaps.Client(key=c.MAPS_API_TOKEN)
origins = ("39.9180091","32.8232624")
destinations = (lat, lon)
time = gmaps.distance_matrix(origins, destinations)["rows"][0]["elements"][0]["duration"]["value"]
"""