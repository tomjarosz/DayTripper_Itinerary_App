import time

#We'll need a dictionary like this, mapping the time
#from each node to every other. Labels are unique identifiers
#for destinations.
times = {'a':{'b':10,'c':2,'d':3},
             'b':{'a':13,'c':25,'d':6},
             'c':{'b':14,'a':8,'d':7},
             'd':{'b':16,'c':12,'a':13}}


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

def get_min_cost(times, delimiter = None):
    '''
    Calculates the minimum cost to pass through each node in a set
    in any order.
    Input:
        times: dict
        delimiter: integer (optional)
    Return: list of strings, integer
    '''
    #This will have to be changed to reflect the priority of each site,
    #with higher priority sites coming first
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