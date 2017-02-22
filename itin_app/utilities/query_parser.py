from itinerary.models import Category, City, UserQuery

from datetime import datetime, time, timedelta, date

def parse_query(initial_form_data):
    user_query = dict(initial_form_data)     #I do this, because "QueryDict is immutable"
        
    requested_city = user_query.get('query_city')

    #get random city if they don't know
    if requested_city[0] == "I don't know":
        proper_city = City.objects.order_by('?')[0]
    else:
        proper_city = helper_check_city(requested_city[0])

    cat_list = []
    for i in range(1,9):
        if 'cat{}'.format(i) in user_query:
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
    if user_query['arrival_date'][0] == '':
        user_query['arrival_date'] = [(datetime.today() + timedelta(days=1)).date().strftime('%m/%d/%Y')]
    if user_query['mode_transportation'][0] == '' or user_query['mode_transportation'][0] == 'any':
        user_query['mode_transportation'] = 'driving'

    user_query['time_start'] = user_query['time_frame'][0].split(' - ')[0]
    user_query['time_end'] = user_query['time_frame'][0].split(' - ')[1]

    if user_query['start_location'][0] == '':
        start_lat, start_lng = None, None
    else:
        start_lat, start_lng = helper_check_address(user_query['start_location'][0])

    arrival_date = datetime.strptime(user_query.get('arrival_date')[0], r'%m/%d/%Y').date().strftime('%Y-%m-%d')
    
    user_query_obj = UserQuery(
        query_city = requested_city[0],
        city = proper_city,   
        arrival_date = arrival_date,
        time_start = user_query.get('time_start'),
        time_end = user_query.get('time_end'),
        category_ids = categories,
        mode_transportation = user_query.get('mode_transportation'), 
        starting_location = user_query.get('start_location')[0],
        start_lat = start_lat,
        start_lng = start_lng)

    user_query_obj.save()

    return user_query_obj, user_categories

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
