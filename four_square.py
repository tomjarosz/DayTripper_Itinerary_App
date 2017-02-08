import json
import requests
import csv
import os
import sqlite3
import time
import datetime
from categories import get_categories

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
    # c.execute('''
    #           SELECT place_id, name, address, place_lat, place_lng, postal_code, state, 
    #           country, categories, rating, 
              #   mon_open1, mon_close1, mon_open2, mon_close_2,
              # tues_open1, tues_close1, tues_open2, tues_close2,
              # wed_open1, wed_close1, wed_open2, wed_close2,
              # thur_open1, thur_close1, thur_open2, thur_close2,
              # fri_open1, fri_close1, fri_open2, fri_close2, 
              # sat_open1, sat_close1, sat_open2, sat_close2,
              # sun_open1, sun_close1, sun_open2, sun_close_2
                # FROM places WHERE city_id = ? AND 
                # DATE(date_update) > DATE('now','-6days')''', [city])

    # data = c.fetchall()
    # if data:
    #     #here we should return data filtered for user_types
    #     return data

    all_categories = get_categories()
    for category in all_categories:
        query = 'https://api.foursquare.com/v2/venues/search?near={city}&categoryId={category}&limit=50&radius=10000&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
                city=city,category=category,client_secret=CLIENT_SECRET, client_id=CLIENT_ID)   

        # print(query)
        # break 
        places = requests.get(query)
        json_data = json.loads(places.text)

        for place in json_data['response']['venues']:
            place_id = get_place_info('id', place)    
            name = get_place_info('name', place)
            address = get_place_info('address', place['location'])
            place_lat = get_place_info('lat', place['location'])
            place_lng = get_place_info('lng', place['location'])
            postal_code = get_place_info('postalCode', place['location'])
            city = get_place_info('city', place['location'])
            state = get_place_info('state', place['location'])
            country = get_place_info('country', place['location'])

            #return place_id, name, address, place_lat, place_lng, postal_code, state, country
            
            #Query individual locations to get other category classification, rating, hours       
            place_query = 'https://api.foursquare.com/v2/venues/{id}/?&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
            id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID)
            #return place_query 

            places = requests.get(place_query)
            place_json_data = json.loads(places.text)

            categories = []
            category_list = place_json_data['response']['venue']['categories']
            for category in category_list:
                categories.append(category['id'])
            categories = ','.join(categories)

            rating = place_json_data['response']['venue']['rating']

            # return categories, rating

            hours_query = 'https://api.foursquare.com/v2/venues/{id}/hours/?&intent=browse&v=20170202&client_secret={client_secret}&client_id={client_id}'.format(
            id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 

            # return hours_query 

            oper_hours = get_hours(hours_query)
            mon_open_1 = oper_hours[0]
            mon_close_1 = oper_hours[1]
            mon_open_2 = oper_hours[2]
            mon_close_2 = oper_hours[3]
            tues_open_1 = oper_hours[4]
            tues_close_1 = oper_hours[5]
            tues_open_2 = oper_hours[6]
            tues_close_2 = oper_hours[7]
            wed_open_1 = oper_hours[8]
            wed_close_1 = oper_hours[9]
            wed_open_2 = oper_hours[10]
            wed_close_2 = oper_hours[11]
            thur_open_1 = oper_hours[12]
            thur_close_1 = oper_hours[13]
            thur_open_2 = oper_hours[14]
            thur_close_2 = oper_hours[15]
            fri_open_1 = oper_hours[16]
            fri_close_1 = oper_hours[17]
            fri_open_2 = oper_hours[18]
            fri_close_2 = oper_hours[19]
            sat_open_1 = oper_hours[20]
            sat_close_1 = oper_hours[21]
            sat_open_2 = oper_hours[22]
            sat_close_2 = oper_hours[23]
            sun_open_1 = oper_hours[24]
            sun_close_1 = oper_hours[25]
            sun_open_2 = oper_hours[26]
            sun_close_2 = oper_hours[27]

            #return mon_open_1
            return thur_open_2
            # return mon_open

            c.execute('''
                      REPLACE INTO places VALUES (date('now'),?,?,?,?,?,?,?,?,?,?,?)
                      ''', 
                      (city, place_id, name, address, place_lat, place_lng, postal_code, state, country, 
                       categories, rating))
            sql_db.commit()

            c.execute('''
                      REPLACE INTO hours VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                      ''', 
                      (place_id, 
                       mon_open1, mon_close1, mon_open2, mon_close_2,
                       tues_open1, tues_close1, tues_open2, tues_close2,
                       wed_open1, wed_close1, wed_open2, wed_close2,
                       thur_open1, thur_close1, thur_open2, thur_close2,
                       fri_open1, fri_close1, fri_open2, fri_close2, 
                       sat_open1, sat_close1, sat_open2, sat_close2,
                       sun_open1, sun_close1, sun_open2, sun_close_2))
            sql_db.commit()

    num_user_categories = len(search_params_ui['types'])
    num_categories = ','.join(['?']*len(search_params_ui['types']))
    return num_categories
            ##match on city-id and type_categoiry input
    c.execute('''
              SELECT place_id, name, address, place_lat, place_lng, postal_code, state, 
              country, categories, rating, 
              mon_open1, mon_close1, mon_open2, mon_close_2,
              tues_open1, tues_close1, tues_open2, tues_close2,
              wed_open1, wed_close1, wed_open2, wed_close2,
              thur_open1, thur_close1, thur_open2, thur_close2,
              fri_open1, fri_close1, fri_open2, fri_close2, 
              sat_open1, sat_close1, sat_open2, sat_close2,
              sun_open1, sun_close1, sun_open2, sun_close_2 
                FROM places 
                WHERE city_id = ?
                AND categories in ({})'''.format(num_categories)
                , (search_params_ui, [city]))


    data = c.fetchall()
    
    #here we should return data filtered for user_types

    return data

def get_place_info(var_name, place_info):
    if var_name in place_info:
        data = place_info[var_name]
    else:
        data = ''
    return data

def get_hours(hours_query):
    place_id = requests.get(hours_query)
    json_data = json.loads(place_id.text)

    hour_list = ['1_open1','1_close1','1_open2','1_close2',  
                 '2_open1','2_close1','2_open2','2_close2',
                 '3_open1','3_close1','3_open2','3_close2', 
                 '4_open1','4_close1','4_open2','4_close2', 
                 '5_open1','5_close1','5_open2','5_close2', 
                 '6_open1','6_close1','6_open2','6_close2', 
                 '7_open1','7_close1','7_open2','7_close2']

    timeframe = json_data['response']['popular']['timeframes']
    for days in timeframe:
        if len(days['open']) > 0:
            if len(days['open']) == 1:
                for day in days['days']:
                    current_open = str(day) +'_open1'
                    current_close = str(day) + '_close1'
                    current_open_hour = int(days['open'][0]['start'])
                    current_close_hour = int(days['open'][0]['end'])

                    hour_list = [current_open_hour if x==current_open else x for x in hour_list]
                    hour_list = [current_close_hour if x==current_close else x for x in hour_list]

            if len(days['open']) == 2:
                for day in days['days']:
                    counter = 1
                    for hour in days['open']:
                        current_open = str(day) +'_open' + str(counter)
                        current_close = str(day) + '_close' + str(counter)
                        current_open_hour = int(hour['start'])
                        current_close_hour = int(hour['end'])
                        counter += 1
                        
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
    param_dict = {'city': 'memphis', 
                  'date': '11/11/2017',
                  'time_start': 1100,
                  'time_end' : 1300,
                  'types': ['4bf58dd8d48988d12d941735','4bf58dd8d48988d12d941735'],
                  'mode_transporation': 'walking'}
    
    # Step 1. Get list of places from given search parameters
    full_list_places = places_from_dict(param_dict)
    print(full_list_places)
