import googlemaps
import json
import requests
import sqlite3
import csv

from datetime import datetime
from geopy.geocoders import Nominatim
from sql_data_manager import data_manager

def get_places_info(city):
    #1. Check if we have info for that city
    c.execute('SELECT place_id, name, address, phone, rating, lat, lon FROM places WHERE city_id = "{}"'.format(city))

    data = c.fetchall()
    if data:
        return data

    city_lat, city_lon = helper_get_city_gps(city, c)
    
    types = ['amusement_park', 'aquarium', 'art_gallery', 'bakery', 'book_store',
        'bowling_alley', 'casino', 'cemetery', 'church', 'city_hall', 'courthouse', 
        'embassy', 'fire_station', 'hindu_temple', 'library', 'local_government_office',
        'lodging', 'mosque', 'museum', 'night_club', 'park', 'place_of_worship',
        'spa', 'stadium', 'synagogue', 'university', 'zoo']
    
    query = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?\
location={lat},{long}&radius=5000&types=({type})&key={key}'.format(
            lat=city_lat, long=city_lon, key=key_google, type='|'.join(types))

    print(query)

    places = requests.get(query)
    
    json_data = json.loads(places.text)
    print(json_data)
    for place in json_data['results']:
        place_id = place['place_id']
        place_name = place['name']
        address, phone, rating, lat, lon = get_place_detail(place_id)
        c.execute('INSERT INTO places VALUES (?,?,?,?,?,?,?,?)', (
            city, place_id, place_name, address, phone, rating, lat, lon))
        sql_db.commit()

    c.execute('SELECT place_id, name, address, phone, rating, lat, lon FROM places WHERE city_id = "{}"'.format(city))
    data = c.fetchall()

    return data

def get_place_detail(place_id):
    query = 'https://maps.googleapis.com/maps/api/place/details/json?placeid={place_id}&key={key}'.format(
            place_id=place_id, key=key_google)

    place_detail = requests.get(query)
    
    json_data = json.loads(place_detail.text)
    address = json_data['result']['formatted_address']
    phone = ''
    if 'international_phone_number' in json_data['result']:
        phone = json_data['result']['international_phone_number']
    rating = 0
    if 'rating' in json_data['result']:
        rating = json_data['result']['rating']
    lat = json_data['result']['geometry']['location']['lat']
    lon = json_data['result']['geometry']['location']['lng']

    return (address, phone, rating, lat, lon)

def helper_get_city_gps(city,c):
    c.execute('SELECT city_id, lat, lon FROM gps_cities WHERE city_id = "{}"'.format(city))
    data = c.fetchone()
    if data:
        return data[1:]

    geolocator = Nominatim()
    location = geolocator.geocode(city)
    c.execute('INSERT INTO gps_cities VALUES (?,?,?)', (city, location.latitude, location.longitude))
    sql_db.commit()

    return (location.latitude, location.longitude)

def get_gmaps(place_id_a, place_id_b):
    '''
    FUNCTION TO GET DIRECTIONS BETWEEN PLACE A AND B

    THIS FUNCTION IS NOT FINISHED
    '''
    query = 'https://maps.googleapis.com/maps/api/directions/json?\
origin=place_id:{p_a}&destination=place_id:{p_b}&key={key}'.format(
        p_a=place_id_a, p_b=place_id_b, key=key_google)

    data_request = requests.get(query)
    
    json_data = json.loads(data_request.text)

    print(json_data['routes'])


if __name__ == '__main__':

    key_google = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'

    #List of Top Cities for autocomplete field
    cities = []
    with open('city_names.csv') as f:
        city_file = csv.reader(f, delimiter=";")
        for c in city_file:
            cities.append(c)

    #User selects city and process starts
    city = 'Washington, DC, US'

    sql_db = sqlite3.connect('app_data.db')
    c = sql_db.cursor()

    redo = False
    data_manager(c, redo)

    places_info = get_places_info(city)

    place_org = places_info[0]
    place_dest = places_info[1]

    get_gmaps(place_org[0], place_dest[0])

    c.close()
    sql_db.close()
