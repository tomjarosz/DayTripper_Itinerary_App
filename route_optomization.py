import time
from math import radians, cos, sin, asin, sqrt


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
place1 = {'id':'abc', 'lat':-54.87, 'long':112.34, 'priority':3.56}


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

def get_min_cost(times, delimiter = None):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        times: dict
        delimiter: integer (optional)
    Return: list of strings, integer
    '''
    labels = list(times.keys())
    if delimiter:
        labels = labels[:delimiter + 1]
    possibilities = permutations(labels)
    optimal = None
    best_cost = 99999
    
    for choice in possibilities:
        cost = 0
        node = choice[:]
        while len(node) > 1:
            begin = node[0]
            end = node[1]
            cost += times[begin][end]
            del node[0]

        if cost < best_cost:
            optimal = choice
            best_cost = cost
         
    return optimal, best_cost

def optomize(times, max_time, return_delimiter = False):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        times: dict
        max_time: int
        return_delimiter: bool
    Returns: list of strings, integer, (integer)
    '''
    time, delimiter, route = 0, 3, []
    num_nodes = len(times.keys())
    while time <= max_time and delimiter <= num_nodes:
        prev_route, prev_time = route, time
        route, time = get_min_cost(times, delimiter)
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

    print(optomize(times, 21, True))

    end_time = time.clock()
    duration = end_time - begin_time
    print("calculation took {} seconds".format(round(duration, 5)))