# DayTripper

This directory contains all the relevant files for the APP "DayTripper"

Folder/files descriptions

    ./itin_app --> "base" code for project. Contains settings.py file (main settings file)

    ./itinerary --> code for Itinerary App (the actual APP developed for CS122)
        /templates/itinerary --> includes Django templates for this APP
            main_form.html
            preliminary_list.html
            final_results.html
            input_error1.html
            input_error2.html

        /management/commands --> includes two custom commands to manage the APP
            refresh_db.py
            load_categories.py
            categories.csv
        
        views.py
        models.py
        urls.py
    
    ./utilities --> 
        contains functions to interact with APIs and perform route optimization
        contains README files for each specific function
        
    ./old_or_in_process --> mostly old code for several things we tried. We didn't
        have time to implement a "weather forecast" section on the results page.
        This would have been useful information for the user.


# How to use the Admin Management Tools
1. load_categories.py

    The "load_categories" function is relevant if this project is started with an empty database.
    It loads the categories in "categories.csv" into the DB.

    In the shell, run:
    
    **python3 manage.py load_categories**
        
2. refresh_db.py

    The "refresh_db" tool is NOT meant to be run by the user. Ideally, after setting
    up the application in the server, the user should set up this process as an
    automatic process to be run once each day. Use "cron" or similar service for this.
    