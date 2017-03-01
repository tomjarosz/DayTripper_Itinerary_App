import json
import urllib.request
import requests
import time
import math
import base64


def get_weather(time, lon, lat):
	'''
	Get dict containing info on temp, precip, etc.
	Inputs:
		time: unix time
		lon: float
		lat: float
	'''
	if not time: time = int(time.time())
	api_key = 'ed3caae2cf05f6088ec1bd57afb153a8'
	encoded_key = b'ZWQzY2FhZTJjZjA1ZjYwODhlYzFiZDU3YWZiMTUzYTg='
	api_key = str(base64.standard_b64decode(encoded_key))

	base_url = 'https://api.darksky.net/forecast/'
	
	url = base_url + api_key + '/' + str(lat) + ',' + str(lon) + ',' + str(time) + '?exclude=currently,minutely,hourly,alerts,flags'
	r = requests.get(url=url)
	data =  r.json()
	

	temp_hi = data['daily']['data'][0]['apparentTemperatureMax']
	temp_low = data['daily']['data'][0]['apparentTemperatureMin']
	precip_chance = data['daily']['data'][0]['precipProbability']
	summary = data['daily']['data'][0]['summary']

	tag = None
	if temp_low < 40: tag = 1
	if temp_hi > 70: tag = 2
	if precip_chance > .3: tag = 3

	return [temp_hi, temp_low, precip_chance, summary, tag]


if __name__ == '__main__':
	lat = 41.8781
	lon = -87.6298

	time = int(time.time()) + 24 * 3600 * 6
	print('time',time)
	response = get_weather(time, lon, lat)
	