from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count
from .models import Category, City, Place, UserQuery

from utilities.query_parser import parse_city, parse_query
from utilities.route_optimization import optimize
from utilities.places_from_foursquare import places_from_foursquare

import json
import requests
import pandas as pd


def index(request):
    cities = City.objects.order_by('city_name')

    categories_to_display = Category.objects.values('user_category', 'user_cat_id').annotate(dcount=Count('user_category')).order_by('user_category')
    print(categories_to_display)
    context = {'cities': cities, 'categories': categories_to_display}
        
    #T1: user accesses application for the first time
    if request.method == 'GET' and 'query_id_from_form' not in request.GET:
        return render(request, 'itinerary/main_form.html', context)
    
    #T2: user sends Main Form to search for places
    if request.method == 'POST':

        initial_form_data = request.POST

        #show error page if form is empty
        if initial_form_data.get('query_city') == '':
            return render(request, 'itinerary/input_error1.html', context)

        proper_city = parse_city(initial_form_data.get('query_city'))
        
        if proper_city == None:
            return render(request, 'itinerary/input_error2.html', context)

        proper_query_obj, user_categories = parse_query(initial_form_data, proper_city)
        
        places_list_to_user = places_from_foursquare(proper_query_obj, user_categories)

        context['lista'] = places_list_to_user
        context['query_id'] = proper_query_obj.id

        return render(request, 'itinerary/preliminary_list.html', context)

    #T3: user sends Second Form to get optimized places
    if request.method == 'GET' and 'query_id_from_form' in request.GET:
        #receive 2nd form and process logans code
        second_form_data = request.GET

        query_id = second_form_data.get('query_id_from_form')
        
        user_query = UserQuery.objects.get(id=query_id)

        #modified places to be a dict. correct implementation?
        places_preferences = {}

        limit = 5
        counter = 0
        for key in second_form_data:
            if 'ur_' in key and counter < limit:
                id_place = key[3:]
                places_preferences[id_place] = [Place.objects.get(id_str=id_place), second_form_data[key]]
                counter += 1

        optimal_places_order, transit_exceptions, times  = optimize(user_query, places_preferences)

        final_places_list = [Place.objects.get(id_str=id_place) for id_place in optimal_places_order]

        context['final_places_list'] = final_places_list
        context['transit_exceptions'] = transit_exceptions
        context['times'] = times

        return render(request, 'itinerary/final_results.html', context)
