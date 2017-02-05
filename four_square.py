import json
import requests
import csv
import os
import sqlite3
import time
import datetime

CLIENT_ID='C1MWPLVELHVOWEQDPZ3FQX2QL31BD5FE44Y0JQBKNRUA1UOA'
CLIENT_SECRET='0FRFY3QUW0LZGA32TMEFOSCUQYIXMUK2YU4RSDHJ1EQLA0AQ'

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
              SELECT place_id, name, address, place_lat, place_lng, postal_code, state, 
              country, categories, rating, mon_open, mon_close, tues_open, tues_close, 
              wed_open, wed_close, thur_open, thur_close, fri_open, fri_close, sat_open, 
              sat_close, sun_open, sun_close FROM places WHERE city_id = ? AND 
              DATE(date_update) > DATE('now','-6days')''', [city])

    data = c.fetchall()
    if data:
        #here we should return data filtered for user_types
        return data

    all_categories = ['4bf58dd8d48988d12d941735','4fceea171983d5d06c3e9823']

    query = 'https://api.foursquare.com/v2/venues/search?near={city}&categoryId={categories}&radius=10000&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
            city=city,categories=','.join(all_categories),client_secret=CLIENT_SECRET, client_id=CLIENT_ID)   

    #print(query)
    places = requests.get(query)
    json_data = json.loads(places.text)

    for place in json_data['response']['venues']:
        place_id = place['id']
        name = place['name']
        address = place['location']['address']
        place_lat = place['location']['lat']
        place_lng = place['location']['lng']
        postal_code = place['location']['postalCode']
        city = place['location']['city']
        state = place['location']['state']
        country = place['location']['country']

        #Query individual locations to get other category classification, rating, hours       
        place_query = 'https://api.foursquare.com/v2/venues/{id}/?&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
        id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 

        places = requests.get(place_query)
        place_json_data = json.loads(places.text)

        categories = []
        category_list = place_json_data['response']['venue']['categories']
        for category in category_list:
            categories.append(category['id'])
        categories = ','.join(categories)

        rating = place_json_data['response']['venue']['rating']

        hours_query = 'https://api.foursquare.com/v2/venues/{id}/hours/?&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
        id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 

        oper_hours = get_hours(hours_query)
        mon_open = oper_hours[0]
        mon_close = oper_hours[1]
        tues_open = oper_hours[2]
        tues_close = oper_hours[3]
        wed_open = oper_hours[4]
        wed_close = oper_hours[5]
        thur_open = oper_hours[6]
        thur_close = oper_hours[7]
        fri_open = oper_hours[8]
        fri_close = oper_hours[9]
        sat_open = oper_hours[10]
        sat_close = oper_hours[11]
        sun_open = oper_hours[12]
        sun_close = oper_hours[13]

        c.execute('''
                  REPLACE INTO places VALUES (date('now'),?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                  ''', 
                  (city, place_id, name, address, place_lat, place_lng, postal_code,state, country, 
                   categories, rating, mon_open, mon_close,tues_open, tues_close, wed_open, wed_close, 
                   thur_open,thur_close, fri_open, fri_close, sat_open, sat_close, sun_open, sun_close))

        sql_db.commit()

            ##match on city-id and type_categoiry input
    c.execute('''
              SELECT place_id, name, address, place_lat, place_lng, postal_code, state, 
              country, categories, rating, mon_open, mon_close, tues_open, tues_close, 
              wed_open, wed_close, thur_open, thur_close, fri_open, fri_close, sat_open, 
              sat_close, sun_open, sun_close FROM places WHERE city_id = ?''', [city])

              # sat_close, sun_open, sun_close FROM places WHERE city_id = ? AND 
              # user_types in )''', [city, categories])
    
    data = c.fetchall()
    
    #here we should return data filtered for user_types

    return data

def get_hours(hours_query):
    place_id = requests.get(hours_query)
    json_data = json.loads(place_id.text)

    #1=Monday....7=Saturday
    hour_list = ['1_open', '1_close', '2_open', '2_close', '3_open', '3_close', 
                 '4_open', '4_close', '5_open', '5_close', '6_open', '6_close', 
                 '7_open', '7_close']

    timeframes = json_data['response']['popular']['timeframes']
    for days in timeframes:
        if len(days['open']) > 0:
            # print(days)
            for day in days['days']:
                current_open = str(day) +'_open'
                current_close = str(day) + '_close'
                current_open_hour = int(days['open'][0]['start'])
                current_close_hour = int(days['open'][0]['end'])

                hour_list = [current_open_hour if x==current_open else x for x in hour_list]
                hour_list = [current_close_hour if x==current_close else x for x in hour_list]

    hour_list = ['' if type(x) != int else x for x in hour_list]
    return hour_list


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
    for i, place_a in enumerate(places_id[0:len(places_id)-1]):
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
    
    time = json_data['routes'][0]['legs'][0]['duration']['value']

    return time


if __name__ == '__main__':

    # User enters parameters and process starts
    param_dict = {'city': 'Washington, DC', 
                  'date': '11/11/2017',
                  'time_start': 1100,
                  'time_end' : 1300,
                  'types': ['4bf58dd8d48988d12d941735','4bf58dd8d48988d12d941735'],
                  'mode_transporation': 'walking'}
    
    # Step 1. Get list of places from given search parameters
    full_list_places = places_from_dict(param_dict)
    print(full_list_places)
