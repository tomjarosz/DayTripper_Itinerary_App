#Route Optimization Algorithm

from datetime import datetime, time, timedelta, date
from math import radians, cos, sin, asin, sqrt
import math 
from utilities.transit_time import helper_transit_time
import pandas as pd
import random
import queue


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
              '4bf58dd8d48988d15a941735' : 120,
              '4bf58dd8d48988d17b941735' : 100
}

TRANSIT_CONSTANT = {'driving' : 100,
                    'walking' : 300,
                    'bicycling' : 200,
                    'transit' : 150}


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculates the circle distance between two points 
    on the earth (specified in decimal degrees). Implementation from PA3.
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


def quick_min_cost(path, query, places_dict, epoch_secs, tr_times):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        path: list of list of strings
        query: custom Django object
        places_dict: dict of place objects
        epoch_secs: integer
        tr_times: dict
    Return: list of strings, integer, int/None, dict
    '''
    DEFAULT_TIME_SPENT = 45

    time = query.time_start.hour * 60 + query.time_start.minute
    exceptions = []   
    all_open = True
    priority = 0
    for i in range(len(path) - 1):
        begin = path[i]
        end = path[i + 1]
        time_string = format_time_string(time)
        if begin != 'starting_location':
            category = places_dict[begin][0].category
            if category in TIME_SPENT.keys():
                time += TIME_SPENT[category]
            else:
                time += DEFAULT_TIME_SPENT
            time_string = format_time_string(time)

        mode_of_transit = query.mode_transportation
        transit_seconds, tr_times = retrieve_transit_time(begin, end,
                                                          epoch_secs,
                                                          time, tr_times,
                                                          places_dict,
                                                          mode_of_transit)

        
        time += transit_seconds / 60

    return time, tr_times
   

def long_min_cost(path, query, places_dict, epoch_secs, 
                  tr_times, final_run=False, verbose=True):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        path: list of list of strings
        query: custom Django object
        places_dict: dict of place objects
        epoch_secs: integer
        tr_times: dict
    Return: list of strings, integer, int/None, dict
    '''
    DEFAULT_TIME_SPENT = 45
    THRESHOLD = 1200
    MISSING = -1

    itinerary = []
    time = query.time_start.hour * 60 + query.time_start.minute
    user_end_time = query.time_end.hour * 60 + query.time_end.minute
    exceptions = {}   
    all_open = True
    priority = 0
    dow = query.arrival_date.weekday() + 1


    for i in range(len(path) - 1):
        mode_of_transit = query.mode_transportation
        round_exceptions = []
        begin = path[i]
        end = path[i + 1]
        if verbose: print('i:{},\n begin: {}, \nend: {}'.format(i, begin, end))
        if i == 0:
            first_transit, tr_times = retrieve_transit_time(begin, end,
                                                            epoch_secs,
                                                            time, tr_times,
                                                            places_dict,
                                                            mode_of_transit)
            if verbose: print('time from start to first:', first_transit / 60)
            time += first_transit / 60

        if verbose: print('time at beginning of first node',time)
        time_string = begin_time = format_time_string(time)
        if begin == 'starting_location':
            pass
        elif places_dict[begin][0].is_open_dow_time(dow, time_string):
            priority += .5 * places_dict[begin][1]
        else:
            all_open = False 
        if begin != 'starting_location':
            category = places_dict[begin][0].category
            if category in TIME_SPENT.keys():
                time += TIME_SPENT[category]
            else:
                time += DEFAULT_TIME_SPENT
            if verbose: print('time after time spent is',time)
            time_string = format_time_string(time)
        if begin == 'starting_location':
            pass
        elif places_dict[begin][0].is_open_dow_time(dow, time_string):
            priority += .5 * places_dict[begin][1]
        else:
            all_open = False
        time_string = end_time = format_time_string(time)
        transit_seconds, tr_times = retrieve_transit_time(begin, end,
                                                          epoch_secs,
                                                          time, tr_times,
                                                          places_dict,
                                                          mode_of_transit)
        itinerary.append((begin, begin_time, end_time))
        last_node_end_time = time
        #do the most thorough search
        if final_run:    
            if transit_seconds == MISSING:
                transit_seconds, tr_times = retrieve_transit_time(begin, end,
                                                                  epoch_secs,
                                                                  time, 
                                                                  tr_times,
                                                                  places_dict,
                                                                  'driving')
                base_string = 'Unable to find directions for {}, \
                so times given are for driving.'
                message = base_string.format(mode_of_transit)
                exceptions[begin] = message
            else:
            #see if more efficient modes of transit exist
                if transit_seconds > THRESHOLD and mode_of_transit != 'driving':
                    round_exceptions = find_exceptions(begin, end, places_dict,
                                                       transit_seconds, 
                                                       epoch_secs,
                                                       mode_of_transit)
                    if round_exceptions:
                        exceptions[round_exceptions[0]] = round_exceptions[1]
            if verbose: print('transit minutes were',transit_seconds / 60)
        time += transit_seconds / 60

    #handle last POI specially
    if time < user_end_time:    
        if verbose: print('adding final location')
        category = places_dict[end][0].category
        if category in TIME_SPENT.keys():
            end_time = time + TIME_SPENT[category]
        else:
            end_time = time + DEFAULT_TIME_SPENT
        time_string = format_time_string(time)
        end_time_string = format_time_string(end_time)
        itinerary.append((end, time_string, end_time_string))
    else:
        end_time = last_node_end_time

    if verbose: print('end time is', end_time)
    if not final_run:
        return end_time, tr_times, priority, all_open
    else:
        return itinerary, exceptions
 

def find_exceptions(begin, end, places_dict, transit_seconds, epoch_secs, 
                    mode_of_transit, verbose=False):
    '''
    Determine if there is a more efficient mode of transport to recommend 
    to the user.
    Inputs:
        begin: string
        end: string
        places_dict: dict of tuples
        transit_seconds: integer
        epoch_secs: integer
        mode_of_transit: string
    Returns: tuple or None
    '''
    REDUCTION_THRESHOLD = .65
    MISSING = -1

    if mode_of_transit != 'transit':
        new_type = 'transit'
        if begin == 'starting_location':
            new_time = helper_transit_time(places_dict[begin]['lat'],
                                             places_dict[begin]['lng'],
                                             places_dict[end][0].lat,
                                             places_dict[end][0].lng,
                                             int(epoch_secs),
                                             'transit')
        else:
            new_time = helper_transit_time(places_dict[begin][0].lat,
                                             places_dict[begin][0].lng,
                                             places_dict[end][0].lat,
                                             places_dict[end][0].lng,
                                             int(epoch_secs),
                                             'transit')
    else:
        new_time = transit_seconds
    if new_time > REDUCTION_THRESHOLD * transit_seconds or new_time == MISSING:
        new_type = 'driving'
        if begin == 'starting_location':
            new_time = helper_transit_time(places_dict[begin]['lat'],
                                         places_dict[begin]['lng'],
                                         places_dict[end][0].lat,
                                         places_dict[end][0].lng,
                                         int(epoch_secs),
                                         'driving')
        else:
            new_time = helper_transit_time(places_dict[begin][0].lat,
                                         places_dict[begin][0].lng,
                                         places_dict[end][0].lat,
                                         places_dict[end][0].lng,
                                         int(epoch_secs),
                                         'driving')
                
    if new_time < REDUCTION_THRESHOLD * transit_seconds:
        if verbose: print('issued a transit exception')
        if new_type == 'transit':
            new_type = 'taking public transportation'
        elif new_type == 'driving':
            new_type = 'driving or taking a taxi'
        time_saved = int((transit_seconds -  new_time) / 60)
        base_message = 'You could save {} minutes by {} instead.'
        message = base_message.format(time_saved, new_type)
        return [begin, message]
    else:
        return None

        
def format_time_string(time):
    '''
    Given an int of the form minutes since midnight, convert to string.
    Inputs:
        time: int
    Returns: string
    '''
    hours = str(int(time / 60))
    minutes = str(int(time % 60))
    if len(hours) == 1:
        hours = '0' + hours
    if len(minutes) == 1:
        minutes = '0' + minutes
    time_string = '{}:{}'.format(hours, minutes)

    return time_string


def retrieve_transit_time(begin_id, end_id, epoch_secs, 
                          time, tr_times, places_dict, 
                          mode_of_transit):
    '''
    Determines if the relevant transit calculation has been performed 
    recently. If so, retrieves that. If not, queries Google Transit API.
    Inputs:
        begin_id: string
        end_id: string
        epoch_secs: int
        time: int
        tr_times: dict
        mode_of_transit: string
    Returns: int, dict
    '''
    #Hours of the day, in minutes
    FIRST_BIN = 7 * 60
    SECOND_BIN = 10 * 60
    THIRD_BIN = 16 * 60
    FOURTH_BIN = 19 * 60
    FIFTH_BIN = 21 * 60
    
    #determine which bin the current time fits in
    epoch_time = epoch_secs + time * 60
    if time > FIRST_BIN and time <= SECOND_BIN:
        section = 'morning_commute'
    elif time > SECOND_BIN and time <= THIRD_BIN:
        section = 'mid_day'
    elif time > THIRD_BIN and time <= FOURTH_BIN:
        section = 'evening_commute'
    elif time > FOURTH_BIN and time <= FIFTH_BIN:
        section = 'evening'
    else:
        section = 'non_peak'

    #first check for stored value
    rv = None
    if begin_id not in tr_times.keys():
        tr_times[begin_id] = {}
    if end_id not in tr_times[begin_id].keys():
        tr_times[begin_id][end_id] = {}
    if section in tr_times[begin_id][end_id].keys():
        rv = tr_times[begin_id][end_id][section]

    #if no stored value, call transit API
    if not rv:
        if begin_id == 'starting_location':
            rv = helper_transit_time(places_dict[begin_id]['lat'],
                                     places_dict[begin_id]['lng'],
                                     places_dict[end_id][0].lat,
                                     places_dict[end_id][0].lng,
                                     int(epoch_time),
                                     mode_of_transit)
        else:
            rv = helper_transit_time(places_dict[begin_id][0].lat,
                                     places_dict[begin_id][0].lng,
                                     places_dict[end_id][0].lat,
                                     places_dict[end_id][0].lng,
                                     int(epoch_time),
                                     mode_of_transit)
        tr_times[begin_id][end_id][section] = rv
    
    return rv, tr_times


def optimize(query, places_dict, verbose=True):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        query: custom django object
        places_dict: dict of tuples
    Returns: list of place strings, list of exception strings, integer
    '''
    PATHS_TO_TRY = 10

    #Determine which places to include based on user's indicated preferences.
    if verbose: print('{} nodes to check'.format(len(places_dict.keys())))
    max_priority = 0
    priority_place_labels = []
    for key, value in places_dict.items():
        if value[1] == 'mid':
            priority_place_labels.append(key)
            places_dict[key] = [value[0], 1]
            max_priority += 1
        elif value[1] == 'up':
            priority_place_labels.insert(0,key)
            places_dict[key] = [value[0], 3]
            max_priority += 3

    #Find time in formats neccecary for later computation
    epoch_date = date(1970,1,1)
    date_differential = query.arrival_date - epoch_date
    epoch_secs = int((date_differential).total_seconds())
    time_end = query.time_end.hour * 60 + query.time_end.minute
    time_begin = query.time_start.hour * 60 + query.time_start.minute
    time_window = time_end - time_begin
    default_initial_time = TRANSIT_CONSTANT[query.mode_transportation]
    num_included_places = time_window // default_initial_time
    if verbose: print('started with {} places'.format(num_included_places))

    #Return empty if not enough time for a single place
    if num_included_places == 0:
        return [], []

    #Parse and assign starting location
    priority_place_labels.insert(0,'starting_location')
    if query.starting_location:
        if verbose: print('user entered a starting location')
        start_dist = haversine(query.city.city_lng, query.city.city_lat, 
                               query.start_lng, query.start_lat)
        if start_dist < 10000:
            if verbose: 
                base_message = 'users starting location lat{} and lon{}'
                print(base_message.format(query.start_lat, query.start_lng))
            value = {'lat':query.start_lat, 'lng':query.start_lng}
            places_dict['starting_location'] = value
        else:
            if verbose: print('used default starting location')
            value = {'lat':query.start_lat, 'lng':query.start_lng}
            places_dict['starting_location'] = value
    else:
        if verbose: print('user did not enter starting location, used default')
        value = {'lat':query.city.city_lat, 'lng':query.city.city_lng}
        places_dict['starting_location'] = value
    if verbose: 
        base_message = 'window:{}-{}, or {} minutes'
        print(base_message.format(time_begin,time_end,time_window))

    #Main loop, to determine out how many nodes to include.
    tr_times = {}
    optimized = prev_above_time = False
    cycle = 0
    while not optimized:
        cycle += 1
        if verbose: print('cycle',cycle)
        places_to_include = priority_place_labels[:num_included_places]
        path, running_distance = branch_bound(query, places_dict, 
                                              places_to_include)
        time, tr_times = quick_min_cost(path, query, places_dict, epoch_secs,
                                        tr_times)
        if verbose: print('time is:',time)
        if verbose: print('path is now:',path)
        
        #finish if close enough to ending time
        if time >= (time_end - 20) and time <= (time_end + 20):
            if verbose: print('time was within allowance. now optimized.')
            optimized = True
        #add or subtract a node for next cycle
        elif time > time_end:
            num_included_places -= 1
            prev_above_time = True
            if verbose: print('too long: removed one place')
        elif time < time_end:
            if verbose: print('too short: added one place')
            num_included_places += 1
            #finish if switched from over time to under time
            if prev_above_time and cycle > 5:
                if verbose: print('previously above time. now optimized.')
                optimized = True
            elif prev_above_time:
                prev_above_time = False
        #finish if unable to resolve path
        if cycle > 20:
            optimized = True
        #finish if the route can fit all places within the time limit
        if len(path) == len(places_dict.keys()) and time <= time_end:
            optimized = True

    if verbose: print('\ntime at end was: {}'.format(time_end))
    if num_included_places == 0:
        return [], []
    #Run comprehensive route algorithm.Q
    running_queue = comp_sort(places_dict, path)
    best_path = None
    best_path_exceptions = None
    best_time = float('inf')
    best_path_priority = -1
    for i in range(PATHS_TO_TRY):
        if not running_queue.empty():
            if verbose: print('now trying the {} best run'.format(i))
            distance, path = running_queue.get()
            path = path[1:]
            time, tr_times, priority, all_open = long_min_cost(path,query,
                                                              places_dict,
                                                              epoch_secs,
                                                              tr_times)
            if verbose: 
                base_message = 'had priority score {}, out of {} possible'
                print(base_message.format(priority, max_priority))
            if verbose: print('and a time of',time)
            if all_open and time <= best_time:
                if verbose: print('all open')
                best_path = path
                best_time = time
                best_path_priority = priority
            if verbose: print('time is:',time, 'best_time is:', best_time)
            elif priority >= best_path_priority and time < best_time:
                best_path = path
                best_time = time
                best_path_priority = priority
    if verbose: print('last path to algo:',best_path)
    itin, exceptions = long_min_cost(best_path, query,
     places_dict,
                                     epoch_secs, tr_times, True)

    if verbose: 
        base_message = '\npassed on: \npath: {}\nexceptions: {}'
        print(base_message.format(itin, exceptions))
    return itin, exceptions
   

def branch_bound(query, places_dict, places_to_include):
    '''
    Determines the greedy optimal path from starting location to all other
    nodes. Not guarunteed to give minimized cost, so this is used as an 
    initial approximation.
    Inputs:
        query: custom django object
        places_dict: dict of tuples
        places_to_include: list of strings
    Returns: list of strings, integer
    '''
    original_matrix = build_matrix(places_to_include, places_dict, query)

    running_cost, first_matrix = matrix_reduce(original_matrix.copy(deep=True),
                                                                    0,0,True)
    running_path = [0]
    prev_row = 0
    while len(running_path) < original_matrix.shape[0]:
        single_round_tracker = []
        for column in range(original_matrix.shape[0]):
            if column not in running_path:
                cost_of_node = matrix_reduce(first_matrix.copy(deep=True),
                                                               column,prev_row)
                single_round_tracker.append((cost_of_node, column))
        sorted_tracker = sorted(single_round_tracker, key = lambda x: x[0])
        prev_round_best = sorted_tracker[0]
        prev_row = prev_round_best[1]
        running_path.append(prev_row)
        
    final_cost = 0
    final_running_path = []
    for i, node in enumerate(running_path):
        if i != len(running_path) - 1:
            trip_cost = original_matrix[running_path[i + 1]][node]
            final_cost += trip_cost
        final_running_path.append(places_to_include[i])    

    return final_running_path, final_cost
    
    
def matrix_reduce(matrix, i, j, first=False):
    '''
    Performs row and column reduction operations on a matrix for specified
    values of i,j. If first is True, i and j are arbitrary.
    Inputs:
        matrix: datafram
        i, j: integers
        first: bool (optional)
    Returns: int
    '''

    INF = float('inf')
    orig_value = matrix[i][j]
    matrix[j][i] = INF
    if not first:
        for i_ in range(matrix.shape[0]): # column
            matrix[i_][j] = INF
        for j_ in range(matrix.shape[0]): #row
            matrix[i][j_] = INF
    #handle rows
    row_mins = list(matrix.idxmin(axis=1))
    row = 0
    running_sum_a = 0
    for column in row_mins:
        if not math.isnan(column):
            min_value = matrix[column][row]
            for entry in range(matrix.shape[0]):
                matrix[entry][row] -= min_value
            running_sum_a += min_value
        row += 1

    #handle columns
    col_mins = list(matrix.idxmin(axis=0))
    column = 0
    running_sum_b = 0
    for row in col_mins:
        if not math.isnan(row):
            min_value = matrix[column][row]
            for entry in range(matrix.shape[0]):
                matrix[column][entry] -= min_value
            running_sum_b += min_value
        column += 1
    
    minimized_value = running_sum_a + running_sum_b
    if first: return minimized_value, matrix
    minimized_value = orig_value + minimized_value

    return minimized_value


def build_matrix(labels, places_dict, query):
    '''
    Builds a symmetrical nxn dataframe (where n = num places) of the
    geographic distance between locations.
    Inputs:
        labels: list of strings
        places_dict: dict of tuples
        query: django custom object
    Returns: nxn dataframe
    '''
    INF = float('inf')
    dimension = len(labels)
    df_rows = []
    for row in labels:
        single_row = []
        for column in labels:
            if row == column:
                single_row.append(INF)
            
            elif row == 'starting_location':
                place_b = places_dict[column][0]
                cit_lat = query.city.city_lat
                cit_lon = query.city.city_lng
                distance = round(haversine(cit_lon, cit_lat, 
                                           place_b.lng, place_b.lat), 1)
                single_row.append(distance)
            
            elif column == 'starting_location':
                place_a = places_dict[row][0]
                cit_lat = query.city.city_lat
                cit_lon = query.city.city_lng
                distance = round(haversine(place_a.lng, place_a.lat, 
                                           cit_lon, cit_lat),1)
                single_row.append(distance)
            
            else:
                place_a = places_dict[row][0]
                place_b = places_dict[column][0]
                distance = round(haversine(place_a.lng, place_a.lat, 
                                           place_b.lng, place_b.lat),1)
                single_row.append(distance)
        
        df_rows.append(single_row)
    matrix = pd.DataFrame(df_rows)

    return matrix


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


def comp_sort(places_dict, running_order, verbose=False):
    '''
    Provides a preliminary ranking of node routes based on geographic distance.
    Inputs:
        places: dict
        labels: list of list of strings
    Returns: list of list of strings
    '''

    distance_matrix = {}
    order_len = len(running_order) - 1
    for item_a in running_order:
        for item_b in running_order:
            if item_a != item_b and item_b != 'starting_location':
                if item_a == 'starting_location':
                    a_lng = places_dict['starting_location']['lng']
                    a_lat = places_dict['starting_location']['lat']
                else:
                    a_lng = places_dict[item_a][0].lng
                    a_lat = places_dict[item_a][0].lat
                b_lng = places_dict[item_b][0].lng
                b_lat = places_dict[item_b][0].lat
                distance = haversine(a_lng, a_lat, b_lng, b_lat)
                if item_a in distance_matrix.keys():
                    distance_matrix[item_a][item_b] = distance
                else:
                    distance_matrix[item_a] = {item_b:distance}
    pairs = []
    for primary_key in distance_matrix.keys():
        for secondary_key, value in distance_matrix[primary_key].items():
            if secondary_key != 'starting_location':
                pairs.append((primary_key, secondary_key, value))

    #heuristic for trimming down set
    DISCOUNT_FACTOR = .1
    num_to_discount = int((order_len ** 2) * DISCOUNT_FACTOR)
    if verbose: print('num to discount', num_to_discount)
    sorted_pairs = sorted(pairs, key=lambda x: x[2])
    ignore = set()
    for i in range(num_to_discount):
        id_0 = sorted_pairs[-(i + 1)][0]
        id_1 = sorted_pairs[-(i + 1)][1]
        ignore.add((id_0, id_1))
    if verbose: print('ignore:', ignore)

    if running_order[0] == 'starting_location':
        running_order = running_order[1:]
        running_order = permutations(running_order)
        for element in running_order:
            element.insert(0,'starting_location')
    else:
        running_order = permutations(running_order)

    #resolve remaining tours into min cost queue
    best_cost = float('inf')
    best_path = []
    rv = []
    running_queue = queue.PriorityQueue()
    count = 0
    for element in running_order:
        running_distance = 0
        for i in range(order_len):
            id_0 = element[i]
            id_1 = element[i + 1]
            if running_distance < best_cost and (id_1, id_1) not in ignore:
                count += 1 
                distance = distance_matrix[id_0][id_1]
                running_distance += distance
                if i == order_len - 1:
                    running_queue.put((distance,element))
                    if running_distance < best_cost:
                        best_cost = running_distance
                        best_path = element
            else:
                break
    total_segments = math.factorial(len(element)) * (len(element) - 1)
    if verbose: 
        base_message = 'processed {} % of all segments'
        print(base_message.format(round((count / total_segments) * 100), 4))

    return running_queue

