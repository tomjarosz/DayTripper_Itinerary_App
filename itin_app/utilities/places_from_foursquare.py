from itinerary.models import Place, Place_hours, City
from django import db

from datetime import datetime, time, timedelta, date
from functools import partial
from multiprocessing import Pool

import json
import requests
#from utilities.weather import Weather

with open('./utilities/keys.json', 'r') as f:
    secret_data = json.load(f)

CLIENT_ID = secret_data['ID']
CLIENT_SECRET = secret_data['SECRET']

def get_place_from_place_dict(place_dict, city_id, category):
    city_obj = City.objects.get(pk=city_id)

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
        checkins = checkins)

    #place_obj.save()
    
    detail_query = 'https://api.foursquare.com/v2/venues/{id}/hours?'\
                  '&intent=browse&v=20170202&client_secret={client_secret}'\
                  '&client_id={client_id}'.format(
                id=place_id, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 
    
    detail_query_request = requests.get(detail_query)
    json_detail_data = json.loads(detail_query_request.text)

    if 'timeframes' in json_detail_data['response']['hours']:
        timeframe_list = json_detail_data['response']['hours']['timeframes']
        
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
    elif 'timeframes' in json_detail_data['response']['popular']:
        timeframe_list = json_detail_data['response']['popular']['timeframes']
        
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

    place_obj.save()

    return place_obj


def places_from_foursquare(user_query, user_categories, multi=True):
    city_obj = user_query.city

    user_dow = user_query.arrival_date.weekday() + 1

    list_of_places = []
    nlimit = 10-int(len(user_categories)/6)

    time_start = datetime.now()

    for category in user_categories:
        #check if we have category and city, and add those places to list of places
        if Place.objects.filter(category=category, city=city_obj).exists():
            places_from_db = Place.objects.filter(category=category, city=city_obj)

            for query_place in places_from_db:
                list_of_places.append((query_place.checkins, query_place.id_str))
            continue

        query = 'https://api.foursquare.com/v2/venues/search?'\
                'll={city_lat},{city_lng}&categoryId={category}&limit={nlimit}&'\
                'radius=10000&intent=browse&v=20170202&'\
                'client_secret={client_secret}&client_id={client_id}'.format(
                city_lat=city_obj.city_lat, 
                city_lng=city_obj.city_lng,
                category=category, 
                nlimit=nlimit,
                client_secret=CLIENT_SECRET, client_id=CLIENT_ID)   

        places = requests.get(query)
        json_data = json.loads(places.text)
        list_of_places_dict = json_data['response']['venues']

        #here we do the multiprocessing!
        db.connections.close_all()
        if multi:
            with Pool(processes=4) as pool:
                processed_places = pool.map(
                    partial(get_place_from_place_dict, city_id=city_obj.pk, category=category), 
                    list_of_places_dict)
        else:
            processed_places = []
            for place_dict in list_of_places_dict:
                place_out = get_place_from_place_dict(place_dict, city_obj.pk, category)
                processed_places.append(place_out)

        # for place in processed_places:
        #     place.save()

        list_of_places.extend([(place.checkins, place.id_str) for place in processed_places if place])

    elapsed_time = datetime.now() - time_start
    print(elapsed_time)
    
    final_list = []
    
    for _, place_id_str in sorted(list_of_places, reverse=True):
        place_to_user = Place.objects.get(id_str=place_id_str)

        if place_to_user.is_open_dow(user_dow) and place_to_user not in final_list:
            final_list.append(place_to_user)

    #here we should update description and photos urls, from detailed query
    for place in final_list[:10]:
        detail_query = 'https://api.foursquare.com/v2/venues/{id}/?'\
                  '&intent=browse&v=20170202&client_secret={client_secret}'\
                  '&client_id={client_id}'.format(
                id=place.id_str, client_secret=CLIENT_SECRET, client_id=CLIENT_ID) 

        detail_query_request = requests.get(detail_query)
        json_detail_data = json.loads(detail_query_request.text)
        
        try:
            photo_dict = json_detail_data['response']['venue']['bestPhoto']
            photo_url = photo_dict['prefix']+'120x120'+photo_dict['suffix']
        except:
            photo_url = ''
        
        try:
            description = json_detail_data['response']['venue']['description']
        except:
            description = ''
    
        place.description = description
        place.url = photo_url
        place.save()

    return final_list[:10]

def get_place_info(var_name, place_info):
    if var_name in place_info:
        data = place_info[var_name]
    else:
        data = ''
    return data

