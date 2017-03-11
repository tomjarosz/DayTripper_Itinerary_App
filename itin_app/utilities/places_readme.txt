This is the readme file for places_from_foursquare.py

The goal of places_from_foursquare.py is to collect all functions relevant to obtain Places information

It performs the following tasks:
    1. Take a user query object and check if data is already available for the city/category selected.
    2. Collect places information if data is not available. It makes several calls to Foursquare API to get this
    3. Format and return places objects for given query.


places_from_foursquare.py uses the following APIs:
    - Foursquare API