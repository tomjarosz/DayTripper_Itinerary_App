from datetime import datetime, time, timedelta, date
from math import radians, cos, sin, asin, sqrt
from transit_time import helper_transit_time
from weather import *

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


def prelim_geo_sort(places_dict, running_order, user_query, accuracy_degree = 3):
    '''
    Provides a preliminary ranking of node routes based on geographic distance.
    Inputs:
        places: dict
        labels: list of list of strings
        accuracy_degree: int (optional, deefaults to 3) 
    Returns: list of list of strings
    '''
    #this is still too slow. have to speed it up

    distance_matrix = {}
    place_ids = places_dict.keys()
    for item_a in place_ids:
        for item_b in place_ids:
            if item_a != item_b and item_b != 'starting_location':
                distance = haversine(places_dict[item_a][0].lng, places_dict[item_a][0].lat,
                                     places_dict[item_b][0].lng, places_dict[item_b][0].lat)
                if item_a in distance_matrix.keys():
                    distance_matrix[item_a][item_b] = distance
                else:
                    distance_matrix[item_a] = {item_b:distance}

    

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
                lon_0 = places_dict[id_0][0].lng
                lat_0 = places_dict[id_0][0].lat
            lon_1 = places_dict[id_1][0].lng
            lat_1 = places_dict[id_1][0].lat
            distance = distance_matrix[id_0][id_1]
            running_distance += distance
        rv.append((distance, element))
    rv = sorted(rv)
    rv = [i[1] for i in rv]
    return rv[:accuracy_degree]


def get_min_cost(ordered_routes, user_query, places_dict, num_included_places, seconds_from_epoch, past_transit_times, exceptions):
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
    #print('called min cost')
    optimal = None
    best_time = 999999
    failed_all_open = []
    time_start = user_query.time_start.hour * 60 + user_query.time_start.minute
    #print('time start is', time_start)
    for choice in ordered_routes:
        choice = choice[:num_included_places + 1]
        all_open = True
        time = time_start
        node = choice[:]
        priority_score = 0
        while len(node) >= 2:
            #print('time is', time,'with', len(node), 'nodes remaining')
            begin = node[0]
            end = node[1]
            if begin == 'starting_location': print('begin is starting location')
            if end == 'starting_location': print('end is starting location')
            #print('node 0 is', begin)
            #print('node 1 is', end)
            #If location isn't open at begining or end of projected time, this route has
            #second class status. Builds priority score, a measure of how many desirable
            #sites are open in this route, based on location ranking.
            time_string = format_time_string(time)
            if places_dict[begin][0].is_open_dow_time(user_query.arrival_date.weekday() + 1, time_string):
                priority_score += .5 * places_dict[begin][0].rating
            else:
                all_open = False 
            time += TIME_SPENT[places_dict[begin][0].category]
            time_string = format_time_string(time)
            if places_dict[begin][0].is_open_dow_time(user_query.arrival_date.weekday() + 1, time_string):
                priority_score += .5 * places_dict[begin][0].rating
            else:
                all_open = False
            mode_of_transportation = user_query.mode_transportation
            transit_seconds, past_transit_times = retrieve_transit_time(begin, end,
                                                                        seconds_from_epoch,
                                                                        time, past_transit_times,
                                                                        places_dict,
                                                                        mode_of_transportation)
            #print('transit time is', transit_seconds)
            #if transit time too long and mode of transit not car, add tag to place_id here
            #this part not finished
            if transit_seconds > 1800 and mode_of_transportation != 'driving':
                #print('trying alternate transit types')
                if mode_of_transportation != 'transit':
                    new_time = helper_transit_time(places_dict[begin_id][0].lat,
                                                     places_dict[begin_id][0].lng,
                                                     places_dict[end_id][0].lat,
                                                     places_dict[end_id][0].lng,
                                                     int(epoch_time),
                                                     'transit')
                else:
                    new_time = transit_seconds
                if new_time > .75 * transit_seconds:
                    new_time = helper_transit_time(places_dict[begin_id][0].lat,
                                                 places_dict[begin_id][0].lng,
                                                 places_dict[end_id][0].lat,
                                                 places_dict[end_id][0].lng,
                                                 int(epoch_time),
                                                 'driving')
                if new_time < .5 * transit_seconds:
                    exceptions.append((begin_id, end_id, (transit_seconds -  new_time) / 60))

            time += transit_seconds / 60
            del node[0]


        if time < best_time and all_open:
            #print('theres a new optimal choice(within get min)')
            optimal = choice
            best_time = time
        else:
            failed_all_open.append((priority_score, choice, time))
      
    #If there is at least one route with all locations open, return route 
    #with best time. Else return route with top priority score.
    if optimal:
        #print('returning best route')
        return optimal, time, past_transit_times, exceptions
    else:
        #print('failed all open')
        failed_all_open = sorted(failed_all_open, key = lambda x: (x[0], x[2]))
        return failed_all_open[0][1], failed_all_open[0][2], past_transit_times, exceptions
        
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


def retrieve_transit_time(begin_id, end_id, seconds_from_epoch, time, past_transit_times, places_dict,mode_of_transportation):
    '''
    Determines if the relevant transit calculation has been performed recently. If so,
    retrieves that. If not, queries Google Transit API.
    Inputs:
        begin_id: string
        end_id: string
        seconds_from_epoch: int
        time: int
        past_transit_times: dict
        mode_od_transportation: string
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
    #this code needs to be fixed. manualy insert a dict at every step

    rv = None
    if begin_id not in past_transit_times.keys():
        past_transit_times[begin_id] = {}
    if end_id not in past_transit_times[begin_id].keys():
        past_transit_times[begin_id][end_id] = {}
    if section in past_transit_times[begin_id][end_id].keys():
        rv = past_transit_times[begin_id][end_id][section]

    if not rv:
        #this call will be replaced with the relevant place object code as soon as 
        #that is implemented
        rv = helper_transit_time(places_dict[begin_id][0].lat,
                                 places_dict[begin_id][0].lng,
                                 places_dict[end_id][0].lat,
                                 places_dict[end_id][0].lng,
                                 int(epoch_time),
                                 mode_of_transportation)
        past_transit_times[begin_id][end_id][section] = rv
    return rv, past_transit_times


def optomize(user_query, places_dict):
    '''
    Determines how many nodes can be visited given upper cost
    constraint.
    Inputs:
        user_query: obj
        places_dict: dict containing place objects, user ratings keyed by place id
    Returns: list of places, list of exceptions, integer
    '''
    exceptions = []
    labels = list(places_dict.keys())
    #print('there are {} places to fit in'.format(len(labels)))
    running_order = permutations(labels)
    if user_query.starting_location:
        cit_lat = user_query.city.city_lat
        cit_lon = user_query.city.city_lng
        start_lat = user_query.start_lat
        start_lon = user_query.start_lng
        distance = haversine(start_lat, start_lon, cit_lat, cit_lon)
        if distance < 10000:
            pass
            #temporarily disabled
            #running_order.insert(0,'starting_location')
            #print('included  starting_location')
    updated_places = prelim_geo_sort(places_dict, running_order, user_query)
    route = []
    time = -1
    past_transit_times = {}
    epoch_date = date(1970,1,1)
    seconds_from_epoch = int((user_query.arrival_date - epoch_date).total_seconds())
    time_end = user_query.time_end.hour * 60 + user_query.time_end.minute
    num_included_places = 2
    while time < time_end and num_included_places <= len(labels):
        #print('optomize time', time)
        last_route, last_time, last_exceptions = route, time, exceptions
        route, time, past_transit_times, exceptions = get_min_cost(updated_places,
                                                       user_query,
                                                       places_dict, 
                                                       num_included_places,
                                                       seconds_from_epoch,
                                                       past_transit_times, exceptions)
        num_included_places += 1
    
    #remember to strip starting location
    #going to return two lists and an int: ordered places, list of transit exceptions, total transit time in mins
    #print('return value is:', last_route, last_exceptions, last_time)
    if user_query.starting_location:
        route = route[1:]
    
    return last_route, last_exceptions, last_time

#####CODE FROM HERE DOWN IS WIP######
def buiild_matrix(places_dict):
    '''
    To be implemented.
    '''
    return []

def matrix_reduce(matrix):
    #handle rows
    row_mins = list(matrix.idxmin(axis=1))
    for i, j in enumerate(row_mins):
        min_value = matrix.iloc[i].loc[j]
        for entry in range(matrix.shape[0]):
            matrix.iloc[i].iloc[entry] -= min_value
    #handle columns
    col_mins = list(matrix.idxmin(axis=0))
    for j, i in enumerate(col_mins):
        min_value = matrix.loc[i].iloc[j]
        for entry in range(matrix.shape[0]):
            matrix.iloc[entry].iloc[j] -= min_value
    return matrix
    
def tsp(matrix):
    path = []
    original_matrix = matrix.copy(deep=True)
    while matrix.shape[0] > 1:
        print(matrix)   
        matrix = matrix_reduce(matrix)
        penalties = []
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[0]):
                if matrix.iloc[i,j] == 0:
                    row = list(matrix.iloc[i])
                    zero_index = row.index(0)
                    del row[zero_index]
                    col = list(matrix.iloc[:,j])
                    zero_index = col.index(0)
                    del col[zero_index]
                    row_min = min(row)
                    col_min = min(col)
                    total = row_min + col_min
                    
                    penalties.append((total, i, j))
        penalties = sorted(penalties, key = lambda x: x[0])
        biggest_penalty = penalties[-1]
        drop_i, drop_j = biggest_penalty[1], biggest_penalty[2]
        #get index of drop_i, drop_j
        drop_i_label = matrix.index[drop_j]
        drop_j_label = matrix.columns[drop_i]
        matrix.iloc[drop_i, drop_j] = INF
        matrix.drop(matrix.columns[drop_i],axis=1,inplace=True)

        matrix.drop(matrix.index[drop_j],inplace=True)
        path.append((drop_i_label,drop_j_label))
    running_distance = 0
    for element in path:
        dist = original_matrix.loc[element[0], element[1]]
        running_distance += dist
    return path, running_distance
