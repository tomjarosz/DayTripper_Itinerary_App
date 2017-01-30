from geopy import geocoders  
import googlemaps
import json
import requests
from geopy.geocoders import Nominatim

import csv
import os
import sqlite3
import time

KEY = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'app_data.db')


def places_from_dict(search_params_ui):
    '''
    First of two functions that interacts with UI

    Gets places information and loads data to SQL. Returns a list of places

    Input:
        - Dictionary with user entered parameters

    Output:
        - list of tuples with places' information
    '''
    city = search_params_ui['city']
    user_types = search_params_ui['types']

    sql_db = sqlite3.connect(DATABASE_FILENAME)
    c = sql_db.cursor()
    
    #1. Check if we have info for that city
    c.execute('''
        SELECT place_id, name, types, address, rating, price_level, location_lat, location_lng  
        FROM places WHERE city_id = ? AND DATE(date_update) > DATE('now','-6 days') ''', [city])

    data = c.fetchall()
    if data:
        #here we should return data filtered for user_types
        return data

    city_lat, city_lon = helper_city_lat_long(city, sql_db)

    all_types = ['amusement_park', 'aquarium', 'art_gallery', 'bakery', 'book_store',
        'bowling_alley', 'casino', 'cemetery', 'church', 'city_hall', 'courthouse', 
        'embassy', 'fire_station', 'hindu_temple', 'library', 'local_government_office',
        'mosque', 'museum', 'park', 'place_of_worship',
        'spa', 'stadium', 'synagogue', 'university', 'zoo']

    query = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?\
location={lat},{long}&radius=10000&types=({type})&rankby=prominence&key={key}'.format(
            lat=city_lat, long=city_lon, key=KEY, type='|'.join(all_types))    

    places = requests.get(query)

    json_data = json.loads(places.text)
    
    has_next = True
    while has_next:

        for place in json_data['results']:
            if 'opening_hours' in place:
                print(place['opening_hours'])

            place_id = place['place_id']
            name = place['name']
            types = ', '.join(place['types'])
            address = place['vicinity']
            rating = helper_check_for_data(place, 'rating')
            price_level = helper_check_for_data(place, 'price_level')
            location_lat = place['geometry']['location']['lat']
            location_lng = place['geometry']['location']['lng']
            if 'photos' in place:
                photo_reference = place['photos'][0]['photo_reference']
            else:
                photo_reference = 'NA'
            
            c.execute('''
                REPLACE INTO places VALUES (date('now'),?,?,?,?,?,?,?,?,?,?)
                ''', (city, place_id, name, types, address, rating, price_level, 
                    location_lat, location_lng, photo_reference))
            
            sql_db.commit()

        if 'next_page_token' in json_data:
            pagetoken = json_data['next_page_token']
    
            newquery = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?\
pagetoken={ptoken}&key={key}'.format(
            ptoken=pagetoken, key=KEY)    
            time.sleep(2)
            places = requests.get(newquery)

            json_data = json.loads(places.text)
        else:
            has_next = False

    c.execute('''
        SELECT place_id, name, types, address, rating, price_level, location_lat, location_lng 
        FROM places WHERE city_id = ?''', [city])
    data = c.fetchall()
    
    #here we should return data filtered for user_types

    return data


def optimized_places(places_from_ui):
    '''
    Second of two functions that interacts with UI. Gets a list of places and
    retrieves transit information from them. Then, it performs optimization
    to find the best itinerary.

    Input: places_from_ui, a list of places' id
    
    Output: a sorted list of places, according to their order
    '''

#    distances_matrix = helper_distances_matrix(places_from_ui)

    #here we might want to filter some places first using distances (clustering some of them?)
    transit_times_matrix = helper_transit_matrix(places_from_ui)

    print(transit_times_matrix)

    #LOGAN SHOULD ADD OPTIMIZATION CODE HERE AND MODIFY OUTPUT ACCORDINGLY
    
    opt_places = list(transit_times_matrix.keys())

    return opt_places


def helper_city_lat_long(city_name, sql_db):
    '''
    Determines the lat/long for any city center entered by user
    '''
    c = sql_db.cursor()

    c.execute('SELECT city_id, lat, lon FROM gps_cities WHERE city_id = "{}"'.format(city_name))
    data = c.fetchone()
    if data:
        return data[1:]

    geolocator = Nominatim()
    location = geolocator.geocode(city_name)
    c.execute('INSERT INTO gps_cities VALUES (?,?,?)', (city_name, location.latitude, location.longitude))
    sql_db.commit()

    c.close()

    return (location.latitude, location.longitude)


def helper_check_for_data(place, attribute):
    '''
    Helper function to check for data in the JSON
    '''

    if attribute in place:
        return place[attribute]
    else:
        return 'NA'

def helper_transit_matrix(places_id):
    transit_matrix = {}
    for i, place_a in enumerate(places_id):
        transit_matrix[place_a] = {}
        for place_b in places_id[i+1:]:
            transit_matrix[place_a][place_b] = helper_transit_time(place_a, place_b)

    return transit_matrix

def helper_transit_time(place_id_a, place_id_b):
    '''
    FUNCTION TO GET TRANSIT TIME BETWEEN A AND B

    THIS FUNCTION IS UNDER DEVELOPMENT
    '''
    query = 'https://maps.googleapis.com/maps/api/directions/json?\
origin=place_id:{p_a}&destination=place_id:{p_b}&key={key}'.format(
        p_a=place_id_a, p_b=place_id_b, key=KEY)

    data_request = requests.get(query)
    
    json_data = json.loads(data_request.text)
    
    #CARLOS NEEDS TO FINISH THIS
    print(len(json_data['routes'][0]['legs']))

    time = 0
    
    return time


if __name__ == '__main__':

    # User enters parameters and process starts
    param_dict = {'city': 'New York, NY', 
                  'time_start': 1100,
                  'time_end' : 1300,
                  'types': ['museum', 'park'],
                  'mode_transporation': 'walking'}
    
    # Step 1. Get list of places from given search parameters
    full_list_places = places_from_dict(param_dict)

    
    # Here there should be Django code to display these places

    # Now, user selects places and optimization begins (I'm selecting the first 
    # 5 places, just to test the function)

    selected_places = []
    for place in full_list_places[:4]:
        place_id = place[0]
        selected_places.append(place_id)
    
    #Optimization includes findind transit time between places
    optimized_places = optimized_places(selected_places)

    #Here there should be more Django stuff to display final info

    #The end.