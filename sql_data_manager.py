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
        name VARCHAR(100),
        types VARCHAR(100),
        address VARCHAR(100),
        rating INT,
        price_level INT,
        location_lat INT,
        location_lng INT,
        photo_reference VARCHAR(256),
        PRIMARY KEY (place_id));''')

    c.close()
    sql_db.close()
