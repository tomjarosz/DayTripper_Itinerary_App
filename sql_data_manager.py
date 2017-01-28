def data_manager(c, redo):
    #run this to start all over
    if redo:
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
        (city_id VARCHAR(100),
        place_id VARCHAR(50),
        name VARCHAR(100),
        address VARCHAR(100),
        phone VARCHAR(20),
        rating INT,
        lat INT,
        lon INT,
        PRIMARY KEY (place_id));''')
