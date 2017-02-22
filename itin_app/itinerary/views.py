from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, time, timedelta, date
from django.db.models import Count
from utilities.route_optimization import optomize
from utilities.places_from_foursquare import places_from_foursquare
from geopy.geocoders import Nominatim

from .models import Category, City, Place, Place_hours, UserQuery

import json
import requests
import pandas as pd


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

        places_list_to_user = places_from_foursquare(proper_query.city, user_categories, user_dow)

        context['lista'] = places_list_to_user
        context['query_id'] = proper_query.id

        return render(request, 'itinerary/preliminary_list.html', context)

    #T3: user sends Second Form to get optimized places
    if request.method == 'GET' and 'query_id_from_form' in request.GET:
        #receive 2nd form and process logans code
        b = request.GET

        query_id = b.get('query_id_from_form')
        
        user_query = UserQuery.objects.get(id=query_id)

        #modified places to be a dict. correct implementation?
        places = {}
        limit, current_nodes = 5 , 0#for testing, temporary

        for key in b:
            if 'ur_' in key and current_nodes <= limit:
                id_place = key[3:]
                places[id_place] = [Place.objects.get(id_str=id_place), b[key]]
                current_nodes += 1

        final_places_list, transit_exceptions, times  = optomize(user_query, places)
        
        final_places_list = [Place.objects.get(id_str=id_place) for id_place in final_places_list]
        print(final_places_list)

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
    if post_data['mode_transportation'][0] == '' or post_data['mode_transportation'][0] == 'any':
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
