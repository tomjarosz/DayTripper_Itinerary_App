import json
import urllib.request
import requests
import time
import math
import base64


class Weather():
	def __init__(self, time, lon, lat):
		'''
		Retrieve summary weather data given time and coordinates.
		'''
		api_key = 'ed3caae2cf05f6088ec1bd57afb153a8'
		base_url = 'https://api.darksky.net/forecast/'
		if not time: time = int(time.time())
		url = base_url + api_key + '/' + str(lat) + ',' + str(lon) + ',' + str(time) + '?exclude=currently,minutely,hourly,alerts,flags'
		r = requests.get(url=url)
		data =  r.json()
		self.temp_hi = data['daily']['data'][0]['apparentTemperatureMax']
		self.temp_low = data['daily']['data'][0]['apparentTemperatureMin']
		self.precip_chance = data['daily']['data'][0]['precipProbability']
		self.summary = data['daily']['data'][0]['summary']

if __name__ == '__main__':
	lat = 41.8781
	lon = -87.6298

	time = int(time.time()) + 24 * 3600 * 6

	weather = Weather(time, lon, lat)
	