import sqlite3

def init_db():
    conn = sqlite3.connect('smart_farm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS farms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS plots 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, farm_id INTEGER, name TEXT, area_sqm REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS crops 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, name TEXT, plant_date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sensors 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, type TEXT, value REAL, timestamp DATETIME DEFAULT (datetime('now','localtime')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS irrigation 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, plot_id INTEGER, mode TEXT, status TEXT, update_time DATETIME DEFAULT (datetime('now','localtime')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS harvest 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, crop_id INTEGER, harvest_date TEXT, yield_kg REAL, revenue REAL)''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
