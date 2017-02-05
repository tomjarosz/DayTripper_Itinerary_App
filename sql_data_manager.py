import os
import sqlite3

DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'app_data.db')

if __name__ == '__main__':
    sql_db = sqlite3.connect(DATABASE_FILENAME)
    
    c = sql_db.cursor()

    c.execute('''DROP TABLE IF EXISTS gps_cities''')
    c.execute('''DROP TABLE IF EXISTS places''')
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS gps_cities
        (city_id VARCHAR(100), 
        lat INT, 
        lon INT, 
        PRIMARY KEY (city_id));''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS places
        (date_update VARCHAR(10),
        city_id VARCHAR(100),
        place_id VARCHAR(50), 
        name VARCHAR(50), 
        address VARCHAR(50), 
        place_lat INT, 
        place_lng INT, 
        postal_code,
        state VARCHAR(50), 
        country VARCHAR(50), 
        categories VARCHAR(50), 
        rating INT, 
        mon_open INT, 
        mon_close INT, 
        tues_open INT, 
        tues_close INT, 
        wed_open INT, 
        wed_close INT, 
        thur_open INT,
        thur_close INT, 
        fri_open INT, 
        fri_close INT, 
        sat_open INT, 
        sat_close INT, 
        sun_open INT,
        sun_close INT,
        PRIMARY KEY (place_id));''')


    c.close()
    sql_db.close()
