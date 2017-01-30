import pyowm

owm_api_key = '5e799fec4bb736c4d14b540b53095184'

owm = pyowm.OWM(owm_api_key)  # You MUST provide a valid API key


obs = owm.weather_at_coords(-0.107331,51.503614)
w = obs.get_weather()
print(w)


fc = owm.daily_forecast('London,uk')
f = fc.get_forecast()
for weather in f:
    print(weather)
