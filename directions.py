import googlemaps
import json
import requests
from datetime import datetime

def get_json_places(query):
    places = requests.get(query)
    
    return json.loads(places.text)

def get_gmaps():
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


if __name__ == '__main__':

    key_google = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'

    query = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius=500&types=food&name=cruise&key={}'.format(key_google)

    places = get_json_places(query)

    for niter, p in enumerate(places['results']):
        print('Place {}'.format(niter))
        print(p)



    #get_gmaps()

    