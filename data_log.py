#!/usr/bin/env python
import sqlite3
import sys
import Adafruit_DHT

def store_data(sid, tc, h):
	conn=sqlite3.connect('/var/www/rtwm/rtwm.db')  
	curs=conn.cursor()
	curs.execute("""INSERT INTO tmps values(datetime('now'),
         (?), (?))""", (sid,tc))
	curs.execute("""INSERT INTO hmds values(datetime('now'),
         (?), (?))""", (sid,h))
	conn.commit()
	conn.close()

hmd, tmpc = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 18)
tmpf = tmpc * 1.8 + 32;
if hmd is not None and tmpc is not None and tmpf is not None:
	store_data("1", tmpc, hmd)	
else:
	store_data("1", -999, -999)
