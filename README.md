# DayTripper

DayTipper is a software product that builds a custom one-day itinerary of popular sites/attractions in a city. It yields a route-optimized list of attractions based on the user’s schedule, preferences and mode of transportation as well as attractions’ locations throughout the city.

DayTripper is a Django app and utilizes a SQLite database. 

# General Software Overview

1. User inputs preferences (city and categories of interest, time constraints, etc.). The system collects the relevant places and attributes given the city and categories chosen (either from (a) the database or (b) from FourSquare if they have not been queried before). Multiprocessing is used to expedite the query process from the APIs.

2. The user is presented with the top ten locations (based on popularity) that meet his/her search criteria and asked to rank them- 'Like it', 'Indifferent', 'Don't like it'.

3. Based on the user's ranking, locations within the city, operating hours, time constraints, mode of transportation, and other factors, the optimization algorithm is invoked to determine the best locations to visit and appropriate order to visit.

4. The ordered list of locations is returned to the user with selected attributes and map. 

# APIs and Dependencies
Foursquare API (API key needed)

GoogleMaps API (API key needed)

Geopy API

Django

Python Libraries: Datetime, Pandas, Queue, Math, Random, JSON, Requests, Base64, Functools, Multiprocessing 

Front-end: CSS, HTML, jQuery, Javascript

# Attributions/Acknowledgments
User Form functionalities (JQuery): https://jqueryui.com/ and http://marcneuwirth.com/blog/2010/02/21/using-a-jquery-ui-slider-to-select-a-time-range/

Mapping functionality: https://developers.google.com/maps/documentation/javascript/markers

Styling and front-end: https://www.w3schools.com/html/html_css.asp

# Contributors

Logan Noel

Carlos Alvarado

Tom Jarosz

DayTripper was developed as a project for University of Chicago CS122 class (Winter 2017).