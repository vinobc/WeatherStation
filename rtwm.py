from flask import Flask, request, render_template
import plotly.plotly as py
from plotly.graph_objs import *
import sqlite3
import time
import datetime
import arrow
app = Flask(__name__)
app.debug = True 
@app.route("/")
def hello():
    return "Hello World!@@@@!$"
@app.route("/rtwm")
def rtwm():
	import sys
	import Adafruit_DHT
	hmd, tmpc = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 18)
    	tmpf = tmpc * 1.8 + 32
	if hmd is not None and tmpc is not None and tmpf is not None:
		return render_template("rtwm.html",tc=tmpc,tf=tmpf,h=hmd)
	else:
		return render_template("not_found.html")
@app.route("/analysis", methods=['GET'])
def analysis():
	tmps_c, hmds_p, timezone, frm, to = fetch_records()
	time_adjusted_temperatures = []
	time_adjusted_humidities   = []
	for record in tmps_c:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_temperatures.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])
	for record in hmds_p:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_humidities.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])
	print "rendering analysis.html with: %s, %s, %s" % (timezone, frm, to)
	#return render_template("analysis.html",tc=tmps_c,h=hmds_p)
	#return render_template("analysis.html",tc=tmps_c,h=hmds_p,ti=len(tmps_c),hi= len(hmds_p))
	return render_template("analysis.html",tc=time_adjusted_temperatures,h=time_adjusted_humidities,fd=frm,td=to,ti=len(tmps_c),hi= len(hmds_p),query_string=request.query_string)
def fetch_records():
	frm 	= request.args.get('f',time.strftime("%Y-%m-%d 00:00")) 
 	to 	= request.args.get('t',time.strftime("%Y-%m-%d %H:%M"))
 	timezone 		= request.args.get('timezone','Etc/UTC');
 	radio_range_h	= request.args.get('button_range_h',''); 
	radio_range_h_int 	= "nan" 
	try: 
		radio_range_h_int	= int(radio_range_h)
	except:
		print "button_range_h is not a number"
  
 	if not valid_date(frm):			
		frm 	= time.strftime("%Y-%m-%d 00:00")
	if not valid_date(to):
		to 	= time.strftime("%Y-%m-%d %H:%M")

	from_date_obj       = datetime.datetime.strptime(frm,'%Y-%m-%d %H:%M')
	to_date_obj         = datetime.datetime.strptime(to,'%Y-%m-%d %H:%M')
	if isinstance(radio_range_h_int,int):
		arrow_time_from = arrow.utcnow().replace(hours=-radio_range_h_int)
		arrow_time_to   = arrow.utcnow()
		from_date_utc   = arrow_time_from.strftime("%Y-%m-%d %H:%M")	
		to_date_utc     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
		frm 		    = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
		to 			    = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
	else:
		#Convert datetimes to UTC so we can retrieve the appropriate records from the database
		from_date_utc   = arrow.get(from_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")	
		to_date_utc     = arrow.get(to_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")
		#tfrm 		= datetime.datetime.now() - datetime.timedelta(hours = radio_range_h_int)
		#tt   		= datetime.datetime.now()
		#frm   = tfrm.strftime("%Y-%m-%d %H:%M")
		#to	  = tt.strftime("%Y-%m-%d %H:%M") 
	conn=sqlite3.connect('/var/www/rtwm/rtwm.db')
	curs=conn.cursor()
	#curs.execute("SELECT * FROM tmps")
	#tmps_c = curs.fetchall()
	#curs.execute("SELECT * FROM hmds")
	#hmds_p = curs.fetchall()
	#conn.close()
	curs.execute("SELECT * FROM tmps WHERE gtime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	tmps_c 	= curs.fetchall()
	curs.execute("SELECT * FROM hmds WHERE gtime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	hmds_p 		= curs.fetchall()
	conn.close()
	return [tmps_c, hmds_p, timezone, frm, to]

@app.route("/at_cloud", methods=['GET'])  #This method will send the data to ploty.
def at_cloud():
	tmps_c, hmds_p, timezone, frm, to = fetch_records()
	# Create new record tables so that datetimes are adjusted back to the user browser's time zone.
	time_series_adjusted_tempreratures  = []
	time_series_adjusted_humidities 	= []
	time_series_temprerature_values 	= []
	time_series_humidity_values 		= []
	for record in tmps_c:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_series_adjusted_tempreratures.append(local_timedate.format('YYYY-MM-DD HH:mm'))
		time_series_temprerature_values.append(round(record[2],2))
	for record in hmds_p:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_series_adjusted_humidities.append(local_timedate.format('YYYY-MM-DD HH:mm')) #Best to pass datetime in text
																						  #so that Plotly respects it
		time_series_humidity_values.append(round(record[2],2))
	tmp_s = Scatter(
        		x=time_series_adjusted_tempreratures,
        		y=time_series_temprerature_values,
        		name='Tmp.'
    				)
	hmd_s = Scatter(
        		x=time_series_adjusted_humidities,
        		y=time_series_humidity_values,
        		name='Hmd.',
        		yaxis='y2'
    				)
	data = Data([tmp_s, hmd_s])
	layout = Layout(
					title="Weather Info. @ The Computer Lab - IFIM Bangalore",
				    xaxis=XAxis(
				        title = 'date_time',
					type='date',
				        autorange=True
				    ),
				    yaxis=YAxis(
				    	title='C',
				        type='linear',
				        autorange=True
				    ),
				    yaxis2=YAxis(
				    	title='%',
				        type='linear',
				        autorange=True,
				        overlaying='y',
				        side='right'
				    )
					)
	fig = Figure(data=data, layout=layout)
	url = py.plot(fig, filename='vth')
	return url
def valid_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
