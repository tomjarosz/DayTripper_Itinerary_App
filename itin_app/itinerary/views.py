from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, time, timedelta
from django.db.models import Count
#from route_optomization import optomize_a

from geopy.geocoders import Nominatim

from .models import Category, City, Place, Place_hours, UserQuery

import json
import requests

from math import radians, cos, sin, asin, sqrt
from transit_time import helper_transit_time
from weather import *
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

        final_places_list, transit_exceptions, times  = optomize(user_query, places)
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



##from here down is the former 'route_optomization file, which has been moved to here. it is a WIP'

TIME_SPENT = {'50aaa49e4b90af0d42d5de11' : 150,
              '4bf58dd8d48988d15d941735' : 45,
              '52e81612bcbc57f1066b7a14' : 150,
              '4bf58dd8d48988d130941735' : 90,
              '4deefb944765f83613cdba6e' : 60,
              '5744ccdfe4b0c0459246b4d9' : 30,
              '4bf58dd8d48988d1e2931735' : 150,
              '56aa371be4b08b9a8d573532' : 60,
              '4bf58dd8d48988d181941735' : 150,
              '507c8c4091d498d9fc8c67a9' : 30,
              '4bf58dd8d48988d166941735' : 40,
              '52e81612bcbc57f1066b7a32' : 60,
              '4bf58dd8d48988d12f941735' : 30,
              '52e81612bcbc57f1066b7a22' : 90,
              '4bf58dd8d48988d163941735' : 110,
              '4bf58dd8d48988d165941735' : 20,
              '5642206c498e4bfca532186c' : 60,
              '4bf58dd8d48988d15c941735' : 50,
              '5310b8e5bcbc57f1066bcbf1' : 120,
              '4e74f6cabd41c4836eac4c31' : 100,
              '4bf58dd8d48988d1e0941735' : 120,
              '4bf58dd8d48988d1e2941735' : 150,
              '4eb1d4d54b900d56c88a45fc' : 120,
              '52e81612bcbc57f1066b7a21' : 180,
              '52e81612bcbc57f1066b7a13' : 170,
              '4bf58dd8d48988d1e9941735' : 300,
              '56aa371be4b08b9a8d573511' : 90,
              '4bf58dd8d48988d15a941735' : 120
}


LAT, LONG, PRIORITY, OPEN, CLOSE, DURATION, TEMP_TIME = 0, 1, 2, 3, 4, 5, 6



def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m 

#consider building a way for user to select where they start (one of the locations)
def permutations(p):
    '''
    Given a list of characters, find every combination.
    Input:
        p: list of strings
    Returns: list of strings
    '''
    if len(p) == 1:
        return [p]
    else:
        rv = []
        for x in p:
            p_minus_x = [i for i in p if i != x]
            perms = permutations(p_minus_x)
            for perm in perms:
                rv.append([x] + perm)
    return rv


def prelim_geo_sort(places_dict, running_order, user_query, accuracy_degree = 2):
    '''
    Provides a preliminary ranking of node routes based on geographic distance.
    Inputs:
        places: dict
        labels: list of list of strings
        accuracy_degree: int (optional, deefaults to 3) 
    '''
    rv = []
    for element in running_order:
        running_distance = 0
        for i in range(len(element) - 1):
            id_0 = element[i]
            id_1 = element[i + 1]
            if id_0 == 'starting_location':
                lon_0 = user_query.start_lng
                lat_0 = user_query.start_lat
            else:    
                lon_0 = places_dict[id_0][LONG]
                lat_0 = places_dict[id_0][LAT]
            lon_1 = places_dict[id_1][LONG]
            lat_1 = places_dict[id_1][LAT]
            distance = haversine(lon_0, lat_0 , lon_1, lat_1)
            running_distance += distance
        rv.append((distance, element))
    rv = sorted(rv)
    rv = [i[1] for i in rv]
    return rv[:accuracy_degree]


def get_min_cost(ordered_routes, begin_time, end_time, num_included_places, seconds_from_epoch, past_transit_times, mode_of_transportation):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        ordered_routes: list of list of strings
        begin_time: integer
        end_time: integer
        num_included_places: integer
        seconds_from_epoch: integer
        past_transit_times: dict
    Return: list of strings, integer, int/None, dict
    '''

    #check if the starting location is reasonable
    optimal = None
    best_time = 999999
    failed_all_open = []

    for choice in ordered_routes:
        choice = choice[:num_included_places + 1]
        all_open = True
        time = begin_time
        node = choice[:]
        priority_score = 0
        while len(node) > 2:
            begin = node[0]
            end = node[1]
            #If location isn't open at begining or end of projected time, this route has
            #second class status. Builds priority score, a measure of how many desirable
            #sites are open in this route, based on location ranking.
            
            #call to is open
            #bool = place.is_open_dow_time(dow, time)
            #dow from user_query, time in hh;mm format
            if places_dict[begin][OPEN] > time:
                all_open = False
            else:
                priority_score += .5 * places_dict[begin][PRIORITY]
            time += places_dict[begin][DURATION]
            if places_dict[begin][CLOSE] < time:
                all_open = False
            else:
                priority_score += .5 * places_dict[begin][PRIORITY]
            #This line is currently depracated until Places object is fully implemented
            mode_of_transportation = user_query.mode_transportation
            transit_seconds, past_transit_times = retrieve_transit_time(begin, end,
                                                                        seconds_from_epoch,
                                                                        time, past_transit_times,
                                                                        mode_of_transportation)
            #if transit time too long and mode of transit not car, add tag to place_id here

            time += transit_seconds / 60
            #time += places_dict[begin][TEMP_TIME] #temp, to avoid using google API too much
            del node[0]


        if time < best_time and all_open:
            optimal = choice
            best_time = time
        else:
            failed_all_open.append((priority_score, choice, time))
      
    #If there is at least one route with all locations open, return route 
    #with best time. Else return route with top priority score.
    if optimal != None:
        return optimal, time, None, past_transit_times
    else:
        failed_all_open = sorted(failed_all_open, key = lambda x: (x[0], x[2]))
        return failed_all_open[0][1], failed_all_open[0][2], failed_all_open[0][0], past_transit_times
        

def retrieve_transit_time(begin, end, seconds_from_epoch, time, past_transit_times, mode_of_transportation):
    '''
    Determines if the relevant transit calculation has been performed recently. If so,
    retrieves that. If not, queries Google Transit API.
    Inputs:
        Begin: Place object
        End: Place object
    Returns: int
    '''
    #Hours of the day, in minutes
    FIRST_BIN = 7 * 60
    SECOND_BIN = 10 * 60
    THIRD_BIN = 16 * 60
    FOURTH_BIN = 21 * 60
    
    #determine which bin the current time fits in
    epoch_time = seconds_from_epoch + time * 60
    if time > FIRST_BIN and time <= SECOND_BIN:
        section = 'morning_commute'
    elif time > SECOND_BIN and time <= THIRD_BIN:
        section = 'mid_day'
    elif time > THIRD_BIN and time <= FOURTH_BIN:
        section = 'evening_commute'
    else:
        section = 'non_peak'
    
    begin_id = begin.place_id()
    end_id = end.place_id()

    rv = past_transit_times.get(begin_id).get(end_id).get(section)
    if not rv:
        #this call will be replaced with the relevant place object code as soon as 
        #that is implemented
        rv = helper_transit_time(places_dict[begin][LAT],
                                 places_dict[begin][LONG],
                                 places_dict[end][LAT],
                                 places_dict[end][LONG],
                                 int(epoch_time))
        past_transit_times[begin_id][end_id][section] = rv

    return rv


def optomize(user_query, places_dict, null=None):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        places_dict: dict
        begin_time: int
        end_time: int
        date: tuple of ints (yyyy, mm, dd)
        starting_location: tuple containing long/lat/unique id
    Returns: list of strings, integer, (integer)
    '''
    print('got to optomize',user_query)
    end_time = user_query.time_end
    labels = list(places_dict.keys())
    if starting_location:
        cit_lat = place.city.city_lat
        cit_lon = place.city.city_lng
        start_lat = user_query.start_lat
        start_lon = user_query.start_lng
        distance = haversine(start_lat, start_lon, cit_lat, cit_lon)
        if distance < 10000:
            labels.prepend('starting_location')
    running_order = permutations(labels)
    updated_places = prelim_geo_sort(places_dict, running_order)
    route = []
    time = -1
    past_transit_times = {}
    num_included_places = len(labels)
    epoch_datetime = time.time()
    begin_run_datetime = datetime.datetime(date[0], date[1], date[2])
    seconds_from_epoch = (begin_run_datetime - epoch_datetime).days * 86400


    while time < end_time and num_included_places > 3:
        route, time, priority_score, past_transit_times = get_min_cost(updated_places, 
                                                                       begin_time, 
                                                                       end_time, 
                                                                       num_included_places,
                                                                       seconds_from_epoch,
                                                                       past_transit_times, mode_of_transportation)
        num_included_places -= 1
    
    #remember to strip starting location
    #going to return two lists and an int: ordered places, list of transit exceptions, total transit time in mins
    return 1,2,3
