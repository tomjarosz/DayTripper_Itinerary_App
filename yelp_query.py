import json
import requests
import csv
import os
import sqlite3
import time
import datetime
from categories import get_categories

DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'app_data.db')

def build_yelp_db(filename):

    sql_db = sqlite3.connect(DATABASE_FILENAME)
    c = sql_db.cursor()

    yelp_data = []
    for line in open(filename, 'r'):
        yelp_data.append(json.loads(line))

    for place in yelp_data:
        place_id = get_place_info('business_id', place)    
        name = get_place_info('name', place)
        address = get_place_info('address', place)
        place_lat = get_place_info('latitude', place)
        place_lng = get_place_info('longitude', place)
        postal_code = get_place_info('postal_code', place)
        city = get_place_info('city', place)
        state = get_place_info('state', place)
        country = get_place_info('country', place)
        categories = ', '.join(get_place_info('categories', place))
        rating = get_place_info('stars', place)

        oper_hours = yelp_get_hours(place['hours'])
        mon_open1 = oper_hours[0]
        mon_close1 = oper_hours[1]
        mon_open2 = oper_hours[2]
        mon_close2 = oper_hours[3]
        tue_open1 = oper_hours[4]
        tue_close1 = oper_hours[5]
        tue_open2 = oper_hours[6]
        tue_close2 = oper_hours[7]
        wed_open1 = oper_hours[8]
        wed_close1 = oper_hours[9]
        wed_open2 = oper_hours[10]
        wed_close2 = oper_hours[11]
        thu_open1 = oper_hours[12]
        thu_close1 = oper_hours[13]
        thu_open2 = oper_hours[14]
        thu_close2 = oper_hours[15]
        fri_open1 = oper_hours[16]
        fri_close1 = oper_hours[17]
        fri_open2 = oper_hours[18]
        fri_close2 = oper_hours[19]
        sat_open1 = oper_hours[20]
        sat_close1 = oper_hours[21]
        sat_open2 = oper_hours[22]
        sat_close2 = oper_hours[23]
        sun_open1 = oper_hours[24]
        sun_close1 = oper_hours[25]
        sun_open2 = oper_hours[26]
        sun_close2 = oper_hours[27]

        # print(city, place_id, name, address, place_lat, place_lng, postal_code, state, country, categories, rating, mon_open1, mon_close1, mon_open2, mon_close2,tue_open1, tue_close1, tue_open2, tue_close2,wed_open1, wed_close1, wed_open2, wed_close2,thu_open1, thu_close1, thu_open2, thu_close2,fri_open1, fri_close1, fri_open2, fri_close2, sat_open1, sat_close1, sat_open2, sat_close2,sun_open1, sun_close1, sun_open2, sun_close2)

        c.execute('''
                  REPLACE INTO places VALUES (date('now'),?,?,?,?,?,?,?,?,?,?,?)
                  ''', 
                  (city, place_id, name, address, place_lat, place_lng, postal_code, state, country, 
                   categories, rating))
        sql_db.commit()

        c.execute('''
                  REPLACE INTO hours VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                  ''', 
                  (place_id, 
                   mon_open1, mon_close1, mon_open2, mon_close2,
                   tue_open1, tue_close1, tue_open2, tue_close2,
                   wed_open1, wed_close1, wed_open2, wed_close2,
                   thu_open1, thu_close1, thu_open2, thu_close2,
                   fri_open1, fri_close1, fri_open2, fri_close2, 
                   sat_open1, sat_close1, sat_open2, sat_close2,
                   sun_open1, sun_close1, sun_open2, sun_close2))
        sql_db.commit()

def get_results(search_params_ui):

    sql_db = sqlite3.connect(DATABASE_FILENAME)
    c = sql_db.cursor()

    search_city = search_params_ui['city']
    search_date = search_params_ui['date']
    search_time_start = search_params_ui['time_start']
    search_time_end = search_params_ui['time_end']
    search_user_categories = search_params_ui['types']
    search_mode_transporation = search_params_ui['mode_transporation']


    day = (time.strftime("%a", time.strptime(search_date, "%m/%d/%Y"))).lower()
    day_time1 = day+'_open1'
    day_time2 = day+'_close1'
    day_time3 = day+'_open2'
    day_time4 = day+'_close2'

    #need to figure out Yelp categories and match on them below

    c.execute('''
              SELECT places.place_id, name, address, place_lat, place_lng, postal_code, state, 
              country, categories, rating, {time1}, {time2}, {time3}, {time4}
                FROM places
                    JOIN hours on places.place_id = hours.place_id
                    WHERE {search_time_start} > {time1} or {search_time_start} > {time3}
                '''.format(time1=day_time1, time2=day_time2, time3=day_time3, time4=day_time4,search_city=search_city, search_time_start=search_time_start,search_time_end=search_time_end) 
              )
              
    data = c.fetchall()
    return data

def get_place_info(var_name, place_info):
    
    if var_name in place_info:
        data = place_info[var_name]
    else:
        data = ''
    return data

def yelp_get_hours(hours_list):

    #["Tuesday 10:0-21:0","Wednesday 10:0-21:0","Thursday 10:0-21:0","Friday 10:0-18:0","Saturday 9:0-16:0"]

    hour_list = ['Monday_open1','Monday_close1','Monday_open2','Monday_close2',  
                 'Tuesday_open1','Tuesday_close1','Tuesday_open2','Tuesday_close2',
                 'Wednesday_open1','Wednesday_close1','Wednesday_open2','Wednesday_close2', 
                 'Thursday_open1','Thursday_close1','Thursday_open2','Thursday_close2', 
                 'Friday_open1','Friday_close1','Friday_open2','Friday_close2', 
                 'Saturday_open1','Saturday_close1','Saturday_open2','Saturday_close2', 
                 'Sunday_open1','Sunday_close1','Sunday_open2','Sunday_close2']

    if hours_list and len(hours_list) > 0:
        for day in hours_list:
            current_open = (day.split(' ',1)[0]) + '_open1'
            current_close = (day.split(' ',1)[0]) + '_close1'
            hours = day.split('y ',1)[1]
            hours = hours.split('-')
            current_open_hour = int((hours[0].replace(':',"")+'0'))
            current_close_hour = int((hours[1].replace(':',"")+'0'))

            hour_list = [current_open_hour if x==current_open else x for x in hour_list]
            hour_list = [current_close_hour if x==current_close else x for x in hour_list]

    hour_list = ['' if type(x) != int else x for x in hour_list]
    return hour_list


def helper_check_for_data(place, attribute):
    '''
    Helper function to check for data in the JSON
    '''

    if attribute in place:
        return place[attribute]
    else:
        return 'NA'


def helper_to_optimize(full_list_places):
    
    places_dict = {}
    for place in full_list_places:
        #places_dict[id] = (lat, lng, rating, open1, close1, open2, close2)
        places_dict[place[0]] = (place[3], place[4], place[-5], place[-4], place[-3], place[-2], place[-1])

    return places_dict



if __name__ == '__main__':

    param_dict = {'city': 'Tempe', 
                  'date': '11/11/2017',
                  'time_start': 1100,
                  'time_end' : 1300,
                  'types': ['Restaurants'],
                  'mode_transporation': 'walking'}
    

    build_yelp_db('yelp_dummy_data.json')
    print(get_results(param_dict))

    # #send top k to the user:
    # full_list_places = places_from_dict(param_dict)

    # #get these back from the user and send them to optimize:
    # to_optimize = helper_to_optimize(full_list_places)

    # print(to_optimize)