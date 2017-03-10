route_optimization.py README---Explains how the algorithm runs.

Step 1: Determine which nodes (POIs) to prioritize
We first include POIs which the user has ranked highest into the potential tour, 
followed by POIs the user is ‘indifferent’ about, and discount POIs which the user 
is uninterested in.
Then, we validate the user’s starting location, as being a reasonable distance 
from the city in question. If the entered location is invalid, the algorithm 
chooses the geographic center of the city.

Step 2: Determine how many nodes to include
Next, we estimate how many nodes to use to begin the tour (num nodes = n), 
based on the user’s selected transit type and available visit time. For instance, 
if a user selected 9-6pm with type =‘driving’, the algorithm might try to start 
with 6 nodes, whereas it might start with only 3 nodes if the type = ‘bicycling’. 
Then, we build a matrix of the transit times between each node, and run a branch
and bound algorithm on the set of potential POIs with length n. This calculates
the approximate time to complete a tour. This will repeat until the ending time
is within a certain tolerance, and we discover that the final tour can include
n* nodes (taking into account that the user will be coming from the starting 
location previously determined).
In this step, when we determine the transit time between two given nodes in one 
of 6 time categories (e.g., time between node 3 and 4 during the ‘morning commute’
 phase), we save that value for later use to avoid redundant API calls.

Step 3: Determine final route and exceptions
This part of the routing algorithm iterates through each potential route to find 
the time minimizing route, but will also take the operating hours of POIs into
 consideration. For instance, if the fastest potential tour conflicts with the 
 operating hours of one or more POI, we’ll try the second best, and so on. We 
 try to balance time minimization with ensuring compliance with operating hours.
We utilize some heuristics to narrow the set of tours to search; discounting
 tours which include the most distant nodes from consideration.
We also calculate transit exceptions in this phase. There are two types of 
exceptions. In some cases, there are no directions available for the user’s 
specified mode of transportation, so we get the transit time for driving 
instead and include an explanation of the problem which is later presented 
to the user. The other type of exception occurs if the user has selected a 
mode of transit other than driving; we determine if there is another mode 
of transit that will save a large amount of time (e.g., if the user has 
selected their mode of transit = ‘walking’ and the algorithm determines it 
would take 45 minutes to walk but only 13 minutes by public transportation, 
we make note of this and will display to the user later “You could save 32 
minutes by taking public transportation instead of walking between these two 
points”)
