import os
import sqlite3

DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'app_data.db')

if __name__ == '__main__':
    sql_db = sqlite3.connect(DATABASE_FILENAME)
    
    c = sql_db.cursor()

    c.execute('''DROP TABLE IF EXISTS gps_cities''')
    c.execute('''DROP TABLE IF EXISTS places''')
    c.execute('''DROP TABLE IF EXISTS hours''')
        
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
        postal_code INT,
        state VARCHAR(50), 
        country VARCHAR(50), 
        categories VARCHAR(50), 
        rating INT, 
        PRIMARY KEY (place_id));''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS hours
        (place_id VARCHAR(50),
        mon_open1 INT, 
        mon_close1 INT, 
        mon_open2 INT, 
        mon_close_2 INT,
        tues_open1 INT,
        tues_close1 INT,
        tues_open2 INT,
        tues_close2 INT,
        wed_open1 INT,
        wed_close1 INT,
        wed_open2 INT,
        wed_close2 INT,
        thur_open1 INT,
        thur_close1 INT,
        thur_open2 INT,
        thur_close2 INT,
        fri_open1 INT,
        fri_close1 INT,
        fri_open2 INT,
        fri_close2 INT,
        sat_open1 INT,
        sat_close1 INT,
        sat_open2 INT,
        sat_close2 INT,
        sun_open1 INT,
        sun_close1 INT,
        sun_open2 INT,
        sun_close_2 INT,
        PRIMARY KEY (place_id));''')

    c.close()
    sql_db.close()
