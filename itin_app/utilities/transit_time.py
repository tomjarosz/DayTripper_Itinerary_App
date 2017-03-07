from datetime import datetime
import json
import requests

KEY = 'AIzaSyBXmwexQtLS4X87d8qFf7XVFH5nnrpvAN8'

def helper_transit_time(place_a_lat, place_a_lng, place_b_lat, place_b_lng, departure_time=None, mode='driving'):
    '''
    FUNCTION TO GET TRANSIT TIME BETWEEN A AND B

    Inputs:
        - place_a_lat:
        - place_a_lng:
        - place_b_lat:
        - place_b_lng:
        - departure_time (optional): time in seconds since 1960
    Returns:
        - time: time in seconds (int)
    '''
    if not departure_time:
        query = 'https://maps.googleapis.com/maps/api/directions/json?mode={mode}&'\
                'origin={lat_a},{lng_a}&destination={lat_b},{lng_b}&key={key}'.format(
                    lat_a=place_a_lat, lng_a=place_a_lng, lat_b=place_b_lat, 
                    lng_b=place_b_lng, key=KEY, mode=mode)
    else:
        query = 'https://maps.googleapis.com/maps/api/directions/json?mode={mode}&'\
                'origin={lat_a},{lng_a}&destination={lat_b},{lng_b}&key={key}&'\
                'departure_time={dtime}'.format(
                    lat_a=place_a_lat, lng_a=place_a_lng, lat_b=place_b_lat, 
                    lng_b=place_b_lng, key=KEY, dtime=departure_time, mode=mode)

    data_request = requests.get(query)
    
    json_data = json.loads(data_request.text)

    #print_dict(json_data)
    
    if json_data['routes']:
        time = json_data['routes'][0]['legs'][0]['duration']['value']
        return time
    print('here')
    return 999

def print_dict(adict, sep=" "):
    if type(adict) == list:
        for l in adict:
            print_dict(l, sep + "   ")
        return None

    if type(adict) != dict:
        print(sep, adict)
        return None

    for k in adict:
        print(sep, "*", k)
        print_dict(adict[k], sep+"   " )

if __name__ == '__main__':
    
    day = '03/06/2017'
    time = '13:00'

    date = datetime.strptime(day+' '+time, r'%m/%d/%Y %H:%M').strftime("%s")

    a = helper_transit_time(41.9211, -87.6340, 41.7923, -87.5804, date)
    print(a)