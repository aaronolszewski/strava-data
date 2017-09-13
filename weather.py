import os
import json
import requests
import datetime

PATH_TO_CITY_LIST = os.path.dirname(os.path.abspath(__file__)) + '/strava/city.list.json'
API_URL = 'http://api.openweathermap.org/data/2.5/weather?id='
COMPASS_VALUES = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
LONDON_ID = 2643743


class APIException(Exception):
    pass


class Weather(object):

    def __init__(self, city_id=None, use_default=False):

        self.api_key = self.get_api_key()
        self.city_id = LONDON_ID if use_default else city_id
        self.try_counter = 0

    @staticmethod
    def get_api_key():
        api_key = os.environ.get('OPEN_WEATHER_MAP_API_KEY')
        if not api_key:
            api_key = raw_input("Please enter your API KEY:")
        assert api_key is not None
        assert isinstance(api_key, str)
        return api_key

    @staticmethod
    def get_city_name():
        return raw_input("Please enter a City Name (e.g. London, San Francisco, New York): ")

    @staticmethod
    def get_country_code():
        return raw_input("Please enter a 2 Letter Country Code (e.g. GB, US, FR): ")

    def get_city_id(self):
        if self.city_id:
            assert isinstance(self.city_id, int)
            return self.city_id
        with open(PATH_TO_CITY_LIST) as city_file:
            cities = json.load(city_file)
            city_name = self.get_city_name()
            country_code = self.get_country_code()
            city = [x for x in cities if x['name'] == city_name.title() and x['country'] == country_code.upper()]
            if not city:
                print "Could not find City: {city} in Country: {country}. Please try again...".format(city=city_name, country=country_code)
                self.try_counter += 1
                if self.try_counter == 3:
                    return None
                city = self.get_city_id()
        if not city:
            return None
        if len(city) > 1:
            print "There are {results} results for that City / Country choice! First occurrence will be used".format(results=len(city))
        return city[0]['id']

    def build_url(self, unit='metric'):
        """
        Build the URL
        :return: URL string
        """
        return API_URL + str(self.get_city_id()) + '&units=' + unit + '&APPID=' + self.api_key

    def get_weather_data(self):
        response = requests.get(url=self.build_url(), timeout=5)
        if response.ok:
            return response.json()
        raise APIException(
            "Error calling Weather API(Error Code: {code}): {message}".format(code=response.status_code,
                                                                              message=response.json().get('message'))
                           )

    @staticmethod
    def degrees_to_compass(degrees):
        if not degrees:
            return None
        if not isinstance(degrees, int):
            return None
        val = int((degrees / 22.5) + .5)
        return COMPASS_VALUES[(val % 16)]

    @staticmethod
    def meters_per_second_to_mph(mps):
        return mps * 2.236936

    @staticmethod
    def unix_to_timestamp(unix):
        return datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_wind_details(wind_dict):
        if 'deg' not in wind_dict:
            print "Wind direction not available!"
            wind_direction = None
        else:
            wind_direction = wind_dict.get('deg')
        return {'speed': wind_dict.get('speed'),
                'direction': wind_direction}

    def build_weather_dict(self):
        weather_dict = self.get_weather_data()
        wind_details = self.get_wind_details(wind_dict=weather_dict.get('wind'))
        return dict(
            city_name=weather_dict.get('name'),
            cloud_cover_percentage=weather_dict.get('clouds').get('all'),
            visibility_metres=weather_dict.get('visibility'),
            min_temp=weather_dict.get('main').get('temp_min'),
            max_temp=weather_dict.get('main').get('temp_max'),
            pressure=weather_dict.get('main').get('pressure'),
            wind_direction_compass=self.degrees_to_compass(degrees=wind_details.get('direction')),
            wind_speed=self.meters_per_second_to_mph(mps=wind_details.get('speed')),
            forecast_timestamp=self.unix_to_timestamp(unix=weather_dict.get('dt'))
                    )
