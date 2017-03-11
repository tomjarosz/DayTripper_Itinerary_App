from itinerary.models import Category, City, UserQuery

from datetime import datetime, time, timedelta, date
from geopy.geocoders import Nominatim

def parse_query(initial_form_data, proper_city):
    '''
    Function to parse the initial form data. It sets some default values if user's
    query had missing information

    Inputs: - initial_form_data (QuerySet object)
            - proper_city (City object)

    Returns: - user_query_obj: Django object for the user's query
             - user_categories: list of user selected categories
    '''
    user_query = dict(initial_form_data)
    
    #Read user's selected categories, if any
    cat_list = []
    for i in range(1,9):
        if 'cat{}'.format(i) in user_query:
            cat_list.append(str(i))

    #If user didn't make a explicit selection, then assume he wants all 
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
    if user_query['arrival_date'][0] == '':
        user_query['arrival_date'] = [(datetime.today() + timedelta(days=1)).date().strftime('%m/%d/%Y')]
    if user_query['mode_transportation'][0] == '' or user_query['mode_transportation'][0] == 'any':
        user_query['mode_transportation'][0] = 'driving'

    user_query['time_start'] = user_query['time_frame'][0].split(' - ')[0]
    user_query['time_end'] = user_query['time_frame'][0].split(' - ')[1]

    if user_query['start_location'][0] == '':
        start_lat, start_lng = None, None
    else:
        start_lat, start_lng = helper_check_address(user_query['start_location'][0])

    arrival_date = datetime.strptime(user_query.get('arrival_date')[0], r'%m/%d/%Y').date()
    
    user_query_obj = UserQuery(
        query_city = user_query.get('query_city')[0],
        city = proper_city,   
        arrival_date = arrival_date,
        time_start = user_query.get('time_start'),
        time_end = user_query.get('time_end'),
        category_ids = categories,
        mode_transportation = user_query.get('mode_transportation')[0], 
        starting_location = user_query.get('start_location')[0],
        start_lat = start_lat,
        start_lng = start_lng)

    user_query_obj.save()

    return user_query_obj, user_categories

def parse_city(query_city):
    '''
    Function to parse a query_city and get the correct City information
    
    Input: a string with a city name (country name optional)
    Returns: a City object with the appropriate data
    '''

    #get random city if they don't know
    if query_city == "I don't know":
        return City.objects.order_by('?')[0]

    #Case 1: user most likely clicked in one of the options
    split_query_city = query_city.split(", ")
    if len(split_query_city) == 2:
        city_name, country_name = split_query_city

        if City.objects.filter(city_name=city_name, country_name=country_name).exists():
            city = City.objects.get(city_name=city_name, country_name=country_name)
            return city
    elif len(split_query_city) == 3:
        city_name, state, country_name = split_query_city

        if City.objects.filter(city_name=city_name, state=state, country_name=country_name).exists():
            city = City.objects.get(city_name=city_name, state=state, country_name=country_name)
            return city

    #Case 2. Up to this point, we couldn't match user info with data. Now find the new city!
    geolocator = Nominatim()
    location = geolocator.geocode(query_city)
    
    #Case 3. City name is not found
    if not location:
        return None

    reverse_location = geolocator.reverse('{}, {}'.format(location.latitude, location.longitude))
    address = reverse_location.raw['address']
  
    if 'city' in address:
        if 'state' not in address:
            state = ''
        else:
            state = address['state']

        print(address.items())
        #We do this, just in case we do have the data
        if City.objects.filter(city_name=address['city'], state=state, country_name=address['country']).exists():
            city = City.objects.get(city_name=address['city'], state=state, country_name=address['country'])
            return city
        
        #Now we store the new city
        city = City(
            city_name=address['city'], 
            state=state,
            country_name=address['country'],
            city_lat = location.latitude,
            city_lng = location.longitude)
        city.save()

        return city
    
    #Case 4. Reverse match of city failed
    return None


def helper_check_address(address_str):
    '''
    Function to parse a "address string" and get the correct latitude and longitude information
    
    Input: a string with a city name (country name optional)
    
    Returns: lat and lng for given address string. If not found, returns None, None
    '''
        
    geolocator = Nominatim()
    location = geolocator.geocode(address_str)
    if location:
        return location.latitude, location.longitude

    return None, None

#######
