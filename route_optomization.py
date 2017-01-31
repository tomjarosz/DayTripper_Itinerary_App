import time
from math import radians, cos, sin, asin, sqrt
from query_google import helper_transit_time


#Currently this system is 'static' in the sense that there is 
#only one transit time between any two points A and B no matter the
#time of day(using the dictionary data structure directly below. 
#As was pointed out during our presentation, that's not
#the most accurate way to do it, so we could improve by using a function
#which takes the unique string of place A, unique string of place B and time
#of day, and returns transit time.

#Data structure needed for this file: objects containing unique ID for each place,
#along with lat/long, and a priority
#
#Example:
places_dict = {'a': (-54.87, 112.12, 2.79),
            'b': (-55.37, 112.89, 3.56),
            'c': (-58.62, 112.45, 3.98),
            'd': (-52.39, 112.08, 4.07),
            'e': (-50.99, 112.21, 4.93)}
LAT = 0
LON = 1
PRIORITY = 2


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

#intermediate step before running get_min_cost: run through all permutations,
#narrow down to top (10?) possible routes which minimize geographic distance,
#then run through get min cost


def prelim_sort(places, labels, accuracy_degree = 3):
    '''
    Provides a preliminary ranking of node routes based on geographic distance.
    Inputs:
        places: dict
        labels: list of string
        accuracy_degree: int (optional, deefaults to 3) 
    '''
    labels = list(places.keys())
    running_order = permutations(labels)
    rv = []
    for element in running_order:
        running_distance = 0
        for i in range(len(element) - 1):
            id_0 = element[i]
            id_1 = element[i + 1]
            lon_0 = places[id_0][LON]
            lat_0 = places[id_0][LAT]
            lon_1 = places[id_1][LON]
            lat_1 = places[id_1][LAT]
            distance = haversine(lon_0, lat_0 , lon_1, lat_1)
            running_distance += distance
        rv.append((distance, element))
    rv = sorted(rv)
    rv = [i[1] for i in rv]
    return rv[:accuracy_degree]

def get_min_cost(ordered_routes, delimiter = None):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        times: dict
        delimiter: integer (optional)
    Return: list of strings, integer
    '''
    
    if delimiter:
        ordered_routes = ordered_routes[:delimiter + 1]
    optimal = None
    best_cost = 99999
    
    for choice in ordered_routes:
        cost = 0
        node = choice[:]
        while len(node) > 1:
            begin = node[0]
            end = node[1]
            #implement call to get transit times here
            #cost += places[begin][end]
            del node[0]

        if cost < best_cost:
            optimal = choice
            best_cost = cost
         
    return optimal, best_cost


def optomize(places, max_cost, return_delimiter = False):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        places: dict
        max_time: int
        return_delimiter: bool
    Returns: list of strings, integer, (integer)
    '''
    labels = list(places.keys())
    running_order = permutations(labels)
    places = prelim_sort(places, running_order)
    time, delimiter, route = 0, 3, []
    num_nodes = len(places)
    while time <= max_cost and delimiter <= num_nodes:
        prev_route, prev_time = route, time
        route, time = get_min_cost(places, delimiter)
        delimiter += 1
    
    if prev_route == []: return False
    delimiter -= 1
    if return_delimiter:
        rv = prev_route, prev_time, delimiter
    else:
        rv = prev_route, prev_time
    return rv

if __name__ == '__main__':
    
    begin_time = time.clock()

    #print(optomize(times, 21, True))

    end_time = time.clock()
    duration = end_time - begin_time
    print("calculation took {} seconds".format(round(duration, 5)))