import json
import requests
import csv
import os
import sqlite3
import time
import datetime
from categories import get_categories

def get_categories(filename):

    yelp_data = []
    for line in open(filename, 'r'):
        yelp_data.append(json.loads(line))

    category_list = []
    for place in yelp_data:
        for category in place['attributes'][0]['categories']:
            if category not in category_list:
                category_list.append(category)

    return category_list

if __name__ == '__main__':

    print(get_categories('/home/student/Desktop/yelp_data.json'))