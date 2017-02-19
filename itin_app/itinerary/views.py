from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, time, timedelta
from django.db.models import Count

from geopy.geocoders import Nominatim

from .models import Category, City, Place, Place_hours, UserQuery

import json
import requests
#from foursquare import places_from_dict

def index(request):
    cities = City.objects.order_by('city_name')

    categories_to_display = Category.objects.values('user_category', 'user_cat_id').annotate(dcount=Count('user_category'))

    context = {'cities': cities, 'categories': categories_to_display}
        
    #T1: user accesses application for the first time
    if request.method == 'GET' and 'query_id_from_form' not in request.GET:
        return render(request, 'itinerary/main_form.html', context)
    
    #T2: user sends Main Form to search for places
    if request.method == 'POST':

        post_data = request.POST

        if post_data.get('query_city') == '':
            return render(request, 'itinerary/input_error.html', context)

        proper_query, user_categories = helper_check_query(post_data)
        
        user_dow = datetime.strptime(proper_query.arrival_date, r'%Y-%m-%d').date().weekday() + 1

        places_list_to_user = places_from_dict(proper_query.city, user_categories, user_dow)

        context['lista'] = places_list_to_user
        context['query_id'] = proper_query.id

        return render(request, 'itinerary/preliminary_list.html', context)

    #T3: user sends Second Form to get optimized places
    if request.method == 'GET' and 'query_id_from_form' in request.GET:
        #receive 2nd form and process logans code
        b = request.GET

        query_id = b.get('query_id_from_form')
        
        user_query = UserQuery.objects.get(id=query_id)

        places = []
        for key in b:
            if 'ur_' in key:
                id_place = key[3:]
                places.append(Place.objects.get(id_str='4e5e5155b61cebc23b6e4dca'))

        #final_places_list, transit_exceptions, times  = route_optimization(user_query, places)
        final_places_list = []
        transit_exceptions = []
        times = []

        context['final_places_list'] = final_places_list
        context['transit_exceptions'] = transit_exceptions
        context['times'] = times

        return render(request, 'itinerary/final_results.html', context)

def helper_check_query(post_data):
    post_data = dict(post_data)     #I do this, because "QueryDict is immutable"
        
    requested_city = post_data.get('query_city')

    #get random city if they don't know
    if requested_city[0] == "I don't know":
        proper_city = City.objects.order_by('?')[0]
    else:
        proper_city = helper_check_city(requested_city[0])

    cat_list = []
    for i in range(1,9):
        if 'cat{}'.format(i) in post_data:
            cat_list.append(str(i))

    if len(cat_list) == 0:
        categories = 'all'
        foursquare_categories = Category.objects.all()
        user_categories = [cat['fs_id'] for cat in foursquare_categories.values('fs_id')]
    else:
        user_categories = []
        for cat in cat_list:
            foursquare_categories = Category.objects.filter(user_cat_id=int(cat))
            user_categories.extend([cat['fs_id'] for cat in foursquare_categories.values('fs_id')])
        user_categories = set(user_categories)
        categories = ','.join(cat_list)

    #setting default values if needed
    if post_data['arrival_date'][0] == '':
        post_data['arrival_date'] = [(datetime.today() + timedelta(days=1)).date().strftime('%m/%d/%Y')]
    if post_data['mode_transportation'][0] == '' | post_data['mode_transportation'][0] == 'any':
        post_data['mode_transportation'] = 'driving'

    post_data['time_start'] = post_data['time_frame'][0].split(' - ')[0]
    post_data['time_end'] = post_data['time_frame'][0].split(' - ')[1]

    if post_data['start_location'][0] == '':
        start_lat, start_lng = None, None
    else:
        start_lat, start_lng = helper_check_address(post_data['start_location'][0])

    arrival_date = datetime.strptime(post_data.get('arrival_date')[0], r'%m/%d/%Y').date().strftime('%Y-%m-%d')
    
    user_query = UserQuery(
        query_city = requested_city[0],
        city = proper_city,   
        arrival_date = arrival_date,
        time_start = post_data.get('time_start'),
        time_end = post_data.get('time_end'),
        category_ids = categories,
        mode_transportation = post_data.get('mode_transportation'), 
        starting_location = post_data.get('start_location')[0],
        start_lat = start_lat,
        start_lng = start_lng)

    user_query.save()

    return user_query, user_categories

def helper_check_city(query_city):
    '''
    Function to parse a query_city and get the correct City information
    
    Input: a string with a city name (country name optional)
    Returns: a City object with the appropriate data
    '''
    #Case 1: user most likely clicked in one of the options
    if ", " in query_city:
        city_name, country_name = query_city.split(", ")

        if City.objects.filter(city_name=city_name, country_name=country_name).exists():
            city = City.objects.get(city_name=city_name, country_name=country_name)
            return city
        
    geolocator = Nominatim()
    location = geolocator.geocode(query_city)
    reverse_location = geolocator.reverse('{}, {}'.format(location.latitude, location.longitude))
    address = reverse_location.raw['address']
  
    if 'city' in address:
        #Case 2. user enters the string, despite of us already having it in our data
        if City.objects.filter(city_name=address['city'], country_name=address['country']).exists():
            city = City.objects.get(city_name=address['city'], country_name=address['country'])
            return city
        
        #Case 3. new city
        city = City(
            city_name=address['city'], 
            country_name=address['country'],
            city_lat = location.latitude,
            city_lng = location.longitude)
        city.save()

        return city
    
    #Case 4. the string does not match a city name
    city = None
    
    return city


def helper_check_address(address_str):
    '''
    Function to parse a query_city and get the correct City information
    
    Input: a string with a city name (country name optional)
    Returns: a City object with the appropriate data
    '''
        
    geolocator = Nominatim()
    location = geolocator.geocode(address_str)
    print(location.latitude, location.longitude)
    return location.latitude, location.longitude

#######

CLIENT_ID='C1MWPLVELHVOWEQDPZ3FQX2QL31BD5FE44Y0JQBKNRUA1UOA'
CLIENT_SECRET='0FRFY3QUW0LZGA32TMEFOSCUQYIXMUK2YU4RSDHJ1EQLA0AQ'


def places_from_dict(city_obj, user_categories, d_of_w_query):
    list_of_places = []
    for category in user_categories:
        query = 'https://api.foursquare.com/v2/venues/search?'\
                'll={city_lat},{city_lng}&categoryId={category}&limit=50&'\
                'radius=10000&intent=browse&v=20170202&'\
                'client_secret={client_secret}&client_id={client_id}'.format(
                city_lat=city_obj.city_lat, city_lng=city_obj.city_lng ,category=category, client_secret=CLIENT_SECRET, client_id=CLIENT_ID)   

        places = requests.get(query)
        json_data = json.loads(places.text)

        for place in json_data['response']['venues']:
            place_id = get_place_info('id', place)
            if Place.objects.filter(id_str=place_id).exists():
                place_from_db = Place.objects.get(id_str=place_id)
                list_of_places.append((place_from_db.checkins, place_from_db.id_str))
                continue
            name = get_place_info('name', place)
            address = get_place_info('address', place['location'])
            place_lat = get_place_info('lat', place['location'])
            place_lng = get_place_info('lng', place['location'])
            postal_code = get_place_info('postalCode', place['location'])
            city = get_place_info('city', place['location'])
            state = get_place_info('state', place['location'])
            country = get_place_info('country', place['location'])
            checkins = place['stats']['checkinsCount']

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
            
            place_obj.save()

            list_of_places.append((checkins, place_obj.id_str))
    

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

    final_list = []
    for c, place_id_str in sorted(list_of_places, reverse=True):
        place_to_user = Place.objects.get(id_str=place_id_str)

        if place_to_user.is_open_dow(d_of_w_query) and place_to_user not in final_list:
            final_list.append(place_to_user)

    return final_list[:10]

def get_place_info(var_name, place_info):
    if var_name in place_info:
        data = place_info[var_name]
    else:
        data = ''
    return data