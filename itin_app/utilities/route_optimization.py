#Route Optimization Algorithm

from datetime import datetime, time, timedelta, date
from math import radians, cos, sin, asin, sqrt
import math 

from utilities.transit_time import helper_transit_time
from utilities.weather import *
import pandas as pd
import random

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

TRANSIT_CONSTANT = {'driving' : 100,
                    'walking' : 300,
                    'bicycling' : 200,
                    'transit' : 150}


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


def get_min_cost(path, user_query, places_dict, seconds_from_epoch, past_transit_times,verbose=False):
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
    optimal = None
    best_time = 999999
    optimized = False
    cycle = 0
    record_of_imperfect_runs = []
    while not optimized:
        list_of_not_open = []
        time = user_query.time_start.hour * 60 + user_query.time_start.minute
        exceptions = []   
        all_open = True
        priority_score = 0
        for i in range(len(path) - 1):
            if verbose: print('time at beginning of first node',time)
            round_exceptions = []
            begin = path[i]
            end = path[i + 1]
            if end == 'starting_location':
                if verbose: print('\nbegin is end?\n')
            time_string = format_time_string(time)
            if begin == 'starting_location':
                pass
            elif places_dict[begin][0].is_open_dow_time(user_query.arrival_date.weekday() + 1, time_string):
                priority_score += .5 * places_dict[begin][0].rating
            else:
                all_open = False 
                list_of_not_open.append(begin)
            if begin != 'starting_location':
                category = places_dict[begin][0].category
                if category in TIME_SPENT.keys():
                    time += TIME_SPENT[category]
                else:
                    time += 45
                if verbose: print('time after time spent is',time)
                time_string = format_time_string(time)
            if begin == 'starting_location':
                pass
            elif places_dict[begin][0].is_open_dow_time(user_query.arrival_date.weekday() + 1, time_string):
                priority_score += .5 * places_dict[begin][0].rating
            else:
                all_open = False
                list_of_not_open.append(begin)
            mode_of_transportation = user_query.mode_transportation
            transit_seconds, past_transit_times = retrieve_transit_time(begin, end,
                                                                        seconds_from_epoch,
                                                                        time, past_transit_times,
                                                                        places_dict,
                                                                        mode_of_transportation)

            #see if more efficient modes of transit exist
            if transit_seconds > 1800 and mode_of_transportation != 'driving':
                round_exceptions = find_exceptions(begin, end, places_dict,
                                                   transit_seconds, epoch_time,
                                                   mode_of_transportation)
                if round_exceptions:
                    exceptions.append(round_exceptions)
            if verbose: print('transit minutes were',transit_seconds / 60)
            time += transit_seconds / 60
        #If everything was open the first time, its easy.
        if all_open:
            return path, time, past_transit_times, exceptions
        #Otherwise, lets randomize the order of the closed places and see if
        #that fixes the issue.
        else:
            if verbose: print('not all open')
            if cycle == 0:
                record_of_imperfect_runs.append((priority_score, [path, time, past_transit_times, exceptions]))
                cycle = 1
                for id_ in list_of_not_open:
                    place = path.pop(path.index(id_))
                    path.insert(random.randint(1,len(path)), place)
                    path, running_distance = branch_bound(user_query, places_dict, path)
            else:
                sorted_record = sorted(record_of_imperfect_runs, key=lambda x: x[0])
                return sorted_record[-1][1]


def find_exceptions(begin, end, places_dict, transit_seconds, epoch_time, mode_of_transportation,verbose=False):
    '''
    Determine if there is a more efficient mode of transport to recommend 
    to the user.
    Inputs:
        begin: string
        end: string
        places_dict: dict of tuples
        transit_seconds: integer
        epoch_time: integer
        mode_of_transportation: string
    Returns: tuple or None
    '''
    if verbose: print('\n::::triggered exceptions:::::\n')
    REDUCTION_THRESHOLD = .5

    if mode_of_transportation != 'transit':
        new_type = 'transit'
        if begin == 'starting_location':
            new_time = helper_transit_time(places_dict[begin]['lat'],
                                             places_dict[begin]['lng'],
                                             places_dict[end][0].lat,
                                             places_dict[end][0].lng,
                                             int(epoch_time),
                                             'transit')
        else:
            new_time = helper_transit_time(places_dict[begin][0].lat,
                                             places_dict[begin][0].lng,
                                             places_dict[end][0].lat,
                                             places_dict[end][0].lng,
                                             int(epoch_time),
                                             'transit')
    else:
        new_time = transit_seconds
    if new_time > REDUCTION_THRESHOLD * transit_seconds:
        new_type = 'driving'
        if begin == 'starting_location':
            new_time = helper_transit_time(places_dict[begin]['lat'],
                                         places_dict[begin]['lng'],
                                         places_dict[end][0].lat,
                                         places_dict[end][0].lng,
                                         int(epoch_time),
                                         'driving')
        else:
            new_time = helper_transit_time(places_dict[begin][0].lat,
                                         places_dict[begin][0].lng,
                                         places_dict[end][0].lat,
                                         places_dict[end][0].lng,
                                         int(epoch_time),
                                         'driving')
                
    if new_time < REDUCTION_THRESHOLD * transit_seconds:
        if verbose: print('\n:::issued a transit exception:::\n')
        return (begin, end, new_type, (transit_seconds -  new_time) / 60)
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
    minutes = str(time % 60)
    if len(hours) == 1:
        hours = '0' + hours
    if len(minutes) == 1:
        minutes = '0' + minutes
    time_string = '{}:{}'.format(hours, minutes)

    return time_string


def retrieve_transit_time(begin_id, end_id, seconds_from_epoch, 
                          time, past_transit_times, places_dict, 
                          mode_of_transportation):
    '''
    Determines if the relevant transit calculation has been performed recently. If so,
    retrieves that. If not, queries Google Transit API.
    Inputs:
        begin_id: string
        end_id: string
        seconds_from_epoch: int
        time: int
        past_transit_times: dict
        mode_of_transportation: string
    Returns: int, dict
    '''
    #Hours of the day, in minutes
    FIRST_BIN = 7 * 60
    SECOND_BIN = 10 * 60
    THIRD_BIN = 16 * 60
    FOURTH_BIN = 19 * 60
    FIFTH_BIN = 21 * 60
    
    #determine which bin the current time fits in
    epoch_time = seconds_from_epoch + time * 60
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


    rv = None
    if begin_id not in past_transit_times.keys():
        past_transit_times[begin_id] = {}
    if end_id not in past_transit_times[begin_id].keys():
        past_transit_times[begin_id][end_id] = {}
    if section in past_transit_times[begin_id][end_id].keys():
        rv = past_transit_times[begin_id][end_id][section]

    if not rv:
        if begin_id == 'starting_location':
            rv = helper_transit_time(places_dict[begin_id]['lat'],
                                     places_dict[begin_id]['lng'],
                                     places_dict[end_id][0].lat,
                                     places_dict[end_id][0].lng,
                                     int(epoch_time),
                                     mode_of_transportation)
        else:
            #somehow 'starting_location is getting into here and clogging up the gears'
            rv = helper_transit_time(places_dict[begin_id][0].lat,
                                     places_dict[begin_id][0].lng,
                                     places_dict[end_id][0].lat,
                                     places_dict[end_id][0].lng,
                                     int(epoch_time),
                                     mode_of_transportation)
        past_transit_times[begin_id][end_id][section] = rv
    return rv, past_transit_times


def optimize(user_query, places_dict,verbose=False):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        user_query: custom django object
        places_dict: dict of tuples
    Returns: list of place strings, list of exception strings, integer
    '''
    #Determine which places to include based on user's indicated preferences.
    priority_place_labels = []
    for key, value in places_dict.items():
        if value[1] == 'mid':
            priority_place_labels.append(key)
        elif value[1] == 'up':
            priority_place_labels.insert(0,key)

    epoch_date = date(1970,1,1)
    seconds_from_epoch = int((user_query.arrival_date - epoch_date).total_seconds())
    time_end = user_query.time_end.hour * 60 + user_query.time_end.minute
    time_begin = user_query.time_start.hour * 60 + user_query.time_start.minute
    time_window = time_end - time_begin
    if verbose: print('mode of transportation',user_query.mode_transportation)
    num_included_places = time_window // TRANSIT_CONSTANT[user_query.mode_transportation]
    priority_place_labels.insert(0,'starting_location')

    past_transit_times = {}
    optimized = False

    #Parse and assign starting location
    if user_query.starting_location:
        start_dist = haversine(user_query.city.city_lng, user_query.city.city_lat, user_query.start_lng, user_query.start_lat)
        if start_distance < 10000:
            places_dict['starting_location'] = {'lat':user_query.start_lat, 'lng':user_query.start_lng}
        else:
            places_dict['starting_location'] = {'lat':user_query.start_lat, 'lng':user_query.start_lng}
    else:
        places_dict['starting_location'] = {'lat':user_query.city.city_lat, 'lng':user_query.city.city_lng}

    prev_above_time = False
    cycle = 0
    if verbose: print('time window is:',time_window)
    #main loop
    while not optimized:
        cycle += 1
        if verbose: print('cycle',cycle)
        places_to_include = priority_place_labels[:num_included_places]
        if verbose: print('places to include',places_to_include)
        #temp
        #return places_to_include, [], []
        path, running_distance = branch_bound(user_query, places_dict, places_to_include)
        if verbose: print('path from branch bound',path)

        #still need to figure out how to reconcile path_from_run with places_to_include
        path_from_run, time, past_transit_times, exceptions = get_min_cost(path,
                                                                       user_query,
                                                                       places_dict,
                                                                       seconds_from_epoch,
                                                                       past_transit_times)
        if verbose: print('time is',time)
        if verbose: print('path from get min cost is:',path_from_run)
        if time > time_end:
            num_included_places -= 1
            prev_above_time = False
            if verbose: print('too long :removed one place')
        elif time < time_end:
            if verbose: print('too short: added one place')
            num_included_places += 1
            if prev_above_time:
                if verbose: print('set optomized to true!')
                optimized = True
        elif time >= (time_end - 60) or time <= (time_end + 60):
            optimized = True
        if cycle > 20 or len(path_from_run) < 3:
            optimized = True
    path_from_run = path_from_run[1:]
    print('\npassed on: \npath from run: {}\nexceptions: {}\n time: {}\n'.format(path_from_run, exceptions, time))
    return path_from_run, exceptions, time


def branch_bound(user_query, places_dict, places_to_include):
    '''
    Determines the greedy optimal path from starting location to all other
    nodes.
    Inputs:
        user_query: custom django object
        places_dict: dict of tuples
        places_to_include: list of strings
    Returns: list of strings, integer
    '''
    original_matrix = build_matrix(places_to_include, places_dict, user_query)

    running_cost, first_matrix = matrix_reduce(original_matrix.copy(deep=True),0,0,True)
    running_path = [0]
    prev_row = 0
    while len(running_path) < original_matrix.shape[0]:
        single_round_tracker = []
        for column in range(original_matrix.shape[0]):
            if column not in running_path:
                cost_of_node = matrix_reduce(first_matrix.copy(deep=True),column,prev_row)
                single_round_tracker.append((cost_of_node, column))
        sorted_single_round_tracker = sorted(single_round_tracker, key = lambda x: x[0])
        prev_round_best = sorted_single_round_tracker[0]
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


def build_matrix(labels, places_dict, user_query):
    '''
    Builds a symmetrical nxn dataframe (where n = num places) of the
    geographic distance between locations.
    Inputs:
        labels: list of strings
        places_dict: dict of tuples
        user_query: django custom object
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
                cit_lat = user_query.city.city_lat
                cit_lon = user_query.city.city_lng
                distance = round(haversine(cit_lon, cit_lat, 
                                           place_b.lng, place_b.lat), 1)
                single_row.append(distance)
            
            elif column == 'starting_location':
                place_a = places_dict[row][0]
                cit_lat = user_query.city.city_lat
                cit_lon = user_query.city.city_lng
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



