from itinerary.models import Place, Place_hours

from datetime import datetime, time, timedelta, date
from functools import partial
from multiprocessing import Pool

import json
import requests

CLIENT_ID='C1MWPLVELHVOWEQDPZ3FQX2QL31BD5FE44Y0JQBKNRUA1UOA'
CLIENT_SECRET='0FRFY3QUW0LZGA32TMEFOSCUQYIXMUK2YU4RSDHJ1EQLA0AQ'

def get_place_from_place_dict(place_dict, city_obj, category):
    if 'id' not in place_dict:
        return None

    place_id = place_dict['id']

    print('getting place {}'.format(place_id))
    
    if Place.objects.filter(id_str=place_id).exists():
        return Place.objects.get(id_str=place_id)


    name = get_place_info('name', place_dict)
    address = get_place_info('address', place_dict['location'])
    place_lat = get_place_info('lat', place_dict['location'])
    place_lng = get_place_info('lng', place_dict['location'])
    postal_code = get_place_info('postalCode', place_dict['location'])
    city = get_place_info('city', place_dict['location'])
    state = get_place_info('state', place_dict['location'])
    country = get_place_info('country', place_dict['location'])
    checkins = place_dict['stats']['checkinsCount']
    if 'description' in place_dict:
        description = place_dict['description'][:100]+'...'
    else:
        description = ''

    place_obj = Place(
        id_str = place_id,
        name = name,
        address = address,
        lat =  place_lat,
        lng = place_lng,
        city = city_obj, 
        postal_code = postal_code,
        category = category,
        rating = 0,
        checkins = checkins,
        description = description)

    place_obj.save()
    
    hours_query = 'https://api.foursquare.com/v2/venues/{id}/hours/?'\
                  '&intent=browse&v=20170202&client_secret={client_secret}'\
                  '&client_id={client_id}'.format(
                id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 
    
    hours_query_request = requests.get(hours_query)
    json_data_for_hours = json.loads(hours_query_request.text)

    if 'timeframes' in json_data_for_hours['response']['hours']:
        timeframe_list = json_data_for_hours['response']['hours']['timeframes']
        
        for timeframe in timeframe_list:
            days = timeframe['days']
            open_times = timeframe['open']
            for d in days:
                for t in open_times:
                    open_time = t['start'].replace('0000','0001')
                    close_time = t['end']
                    if "+" in close_time:
                        close_time = '2359'

                    open_time = open_time[:2]+':'+open_time[2:]
                    close_time = close_time[:2]+':'+close_time[2:]
                    
                    place_hour = Place_hours(
                        place_id = place_obj,
                        d_of_w_open = d,
                        open_time = open_time,
                        close_time = close_time)
                    place_hour.save()
    elif 'timeframes' in json_data_for_hours['response']['popular']:
        timeframe_list = json_data_for_hours['response']['popular']['timeframes']
        
        for timeframe in timeframe_list:
            days = timeframe['days']
            open_times = timeframe['open']
            for d in days:
                for t in open_times:
                    open_time = t['start'].replace('0000','0001')
                    close_time = t['end']
                    if "+" in close_time:
                        close_time = '2359'

                    open_time = open_time[:2]+':'+open_time[2:]
                    close_time = close_time[:2]+':'+close_time[2:]
                    
                    place_hour = Place_hours(
                        place_id = place_obj,
                        d_of_w_open = d,
                        open_time = open_time,
                        close_time = close_time)
                    place_hour.save()

    return place_obj


def places_from_foursquare(user_query, user_categories):
    city_obj = user_query.city

    user_dow = datetime.strptime(user_query.arrival_date, r'%Y-%m-%d').date().weekday() + 1

    list_of_places = []
    for category in user_categories:
        #check if we have category and city, and add those places to list of places
        if Place.objects.filter(category=category, city=city_obj).exists():
            places_from_db = Place.objects.filter(category=category, city=city_obj)

            for query_place in places_from_db:
                list_of_places.append((query_place.checkins, query_place.id_str))
            continue

        query = 'https://api.foursquare.com/v2/venues/search?'\
                'll={city_lat},{city_lng}&categoryId={category}&limit=50&'\
                'radius=10000&intent=browse&v=20170202&'\
                'client_secret={client_secret}&client_id={client_id}'.format(
                city_lat=city_obj.city_lat, city_lng=city_obj.city_lng ,category=category, client_secret=CLIENT_SECRET, client_id=CLIENT_ID)   

        places = requests.get(query)
        json_data = json.loads(places.text)
        list_of_places_dict = json_data['response']['venues']

        with Pool() as pool:
            processed_places = pool.map(
                partial(get_place_from_place_dict, city_obj=city_obj, category=category), 
                list_of_places_dict)
        
        list_of_places.extend([(place.checkins, place.id_str) for place in processed_places if place])


    final_list = []
    for c, place_id_str in sorted(list_of_places, reverse=True):
        place_to_user = Place.objects.get(id_str=place_id_str)

        if place_to_user.is_open_dow(user_dow) and place_to_user not in final_list:
            final_list.append(place_to_user)

    return final_list[:10]

def get_place_info(var_name, place_info):
    if var_name in place_info:
        data = place_info[var_name]
    else:
        data = ''
    return data

