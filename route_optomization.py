import time
from math import radians, cos, sin, asin, sqrt
from transit_time import helper_transit_time
import datetime


#Example data structure for this file:
#Format of each dict entry- id: lon, lat, rating, open_time, close_time, avg_time, temp_dummy for testing
places_dict = {'ChIJp2E8Hb8sDogR8WK83agX6c4': (41.8789, -87.6359, 2.79, 800, 1500,10, 20), # willis tower
            'ChIJB5o6CWvTD4gR25QC-QbMQAk': (41.9211, -87.6340, 3.56, 900, 1900, 90, 10), #lincoln park zoo
            'ChIJHd8BYAopDogRBuMXc6oszA8': (41.7923, -87.5804, 3.98, 730, 2000, 75, 14), #MSI
            'ChIJ9ZKOJxQsDogRuJBKj2ZPhi8': (41.8299, -87.6338, 4.07, 1300, 2330, 135, 13), #White Sox Field
            'ChIJId-a5bLTD4gRRtbdduE-6hw': (41.9484, -87.6553, 4.93, 1145, 1745, 80, 31)} #Wrigley Field

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


def prelim_geo_sort(places_dict, running_order, accuracy_degree = 2):
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


def get_min_cost(ordered_routes, begin_time, end_time, num_included_places, seconds_from_epoch):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        ordered_routes: list of list of strings
        begin_time: integer
        end_time: integer
        num_included_places: integer
        seconds_from_epoch: integer
    Return: list of strings, integer, int/None
    '''

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
            if places_dict[begin][OPEN] > time:
                all_open = False
            else:
                priority_score += .5 * places_dict[begin][PRIORITY]
            time += places_dict[begin][DURATION]
            if places_dict[begin][CLOSE] < time:
                all_open = False
            else:
                priority_score += .5 * places_dict[begin][PRIORITY]
            #add parameters w/ respect to current time, day 
            epoch_time = seconds_from_epoch + time * 60
            transit_seconds = helper_transit_time(places_dict[begin][LAT],
                                                  places_dict[begin][LONG],
                                                  places_dict[end][LAT],
                                                  places_dict[end][LONG],
                                                  int(epoch_time))

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
        return optimal, time, None
    else:
        failed_all_open = sorted(failed_all_open, key = lambda x: (x[0], x[2]))
        return failed_all_open[0][1], failed_all_open[0][2], failed_all_open[0][0]
        


def optomize(places_dict, begin_time, end_time, date = None):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        places_dict: dict
        begin_time: int
        end_time: int
        date: tuple of ints (yyyy, mm, dd)
    Returns: list of strings, integer, (integer)
    '''
    labels = list(places_dict.keys())
    running_order = permutations(labels)
    updated_places = prelim_geo_sort(places_dict, running_order)
    route = []
    time = 99999999
    num_included_places = len(labels)
    epoch_datetime = datetime.datetime(1960,1,1)
    begin_run_datetime = datetime.datetime(date[0], date[1], date[2])
    seconds_from_epoch = (begin_run_datetime - epoch_datetime).days * 86400

    while time > end_time and num_included_places > 3:
        route, time, priority_score = get_min_cost(updated_places, 
                                                   begin_time, 
                                                   end_time, 
                                                   num_included_places,
                                                   seconds_from_epoch)
        num_included_places -= 1
    

    return route, time

if __name__ == '__main__':
    
    begin_time = time.clock()

    rv = optomize(places_dict, 9*60,20*60, (2017,2,5))
    print(rv)

    end_time = time.clock()
    duration = end_time - begin_time
    print("calculation took {} seconds".format(round(duration, 5)))