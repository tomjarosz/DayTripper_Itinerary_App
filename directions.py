import googlemaps
from datetime import datetime

key_google = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'

gmaps = googlemaps.Client(key= key_google)

# Geocoding an address
geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
print(geocode_result)

# Look up an address with reverse geocoding
reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))
print(reverse_geocode_result)

# Request directions via public transit
now = datetime.now()
directions_result = gmaps.directions("Sydney Town Hall",
                                     "Parramatta, NSW",
                                     mode="transit",
                                     departure_time=now)

print(directions_result)