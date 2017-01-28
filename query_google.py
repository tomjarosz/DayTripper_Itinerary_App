from geopy import geocoders  
import googlemaps
import json
import requests
from datetime import datetime
import csv

def get_city_lat_long(city_name):
    '''
    Determines the lat/long for any city center entered by user
    '''

    link = 'https://maps.googleapis.com/maps/api/geocode/json?address=___'
    link = link.replace('___', city_name)
    response = requests.get(link)
    city_json = response.json()
    lat_long = city_json['results'][0]['geometry']['location']
    
    lat_lng = []
    lat_lng.append(str(lat_long['lat']))
    lat_lng.append(str(lat_long['lng']))
    return ",".join(lat_lng)


def make_request_from_params(param_dict, query, type_var, key_google):
    '''
    Formats the correct API URL request given user's parameters for one category
    '''

    lat_lng = get_city_lat_long(param_dict['city'])
    radius_dist = 25000
    query = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat_lng}&radius={radius_dist}&types={type_cat}&key={key_google}'.format(lat_lng=lat_lng, radius_dist=radius_dist, type_cat=type_var, key_google=key_google)
    return query


def get_json_places(query):
    '''
    Retrieves all location information from Google API
    '''

    places = requests.get(query)
    return json.loads(places.text)


def get_loc_attributes(places, category, csv_file):
    '''
    Retrieves location attributes from the API JSON and stores them in a csv file
    '''    

    with open(csv_file, 'a') as f:
        writer = csv.writer(f)

        for place in places['results']:
            place_dict = place

            place_id = place['place_id']
            name = place['name']
            address = place['vicinity']
            location_lat = place['geometry']['location']['lat']
            location_lng = place['geometry']['location']['lng']
            rating = helper_check_for_data(place, 'rating')
            price_level = helper_check_for_data(place, 'price_level')

            location_info = [category, place_id, name, address, location_lat, location_lng, rating, price_level]
            writer.writerow(location_info)

    return csv_file


def helper_check_for_data(place, attribute):
    '''
    Helper function to check for data in the JSON
    '''

    if attribute in place:
        return place[attribute]
    else:
        return 'NA'



if __name__ == '__main__':

    csv_file = 'query_results.csv'
    key_google = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'

    param_dict = {'city': 'Chicago', 
                  'time_start': 1100,
                  'time_end' : 1300,
                  'categories': ['museum', 'park'],
                  'mode_transporation': 'walking'}

    for type_var in param_dict['categories']:
        base_query = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat_lng}&radius={radius_dist}&types={type_cat}&key={key_google}'
        query = make_request_from_params(param_dict, base_query, type_var, key_google)
        places = get_json_places(query)

        get_loc_attributes(places, type_var, csv_file)