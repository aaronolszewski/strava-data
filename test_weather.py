import pytest
import mock
import weather

MOCKED_API_KEY = 'abc123'
MOCKED_ENV_VARS = {'OPEN_WEATHER_MAP_API_KEY': MOCKED_API_KEY}
MOCKED_CITY_LIST_JSON = [{'name': 'London', 'country': 'GB', 'id': 100}]
MOCKED_JSON_RESPONSE = {'clouds': {'all': 75},
                        'name': 'London',
                        'visibility': 10000,
                        'sys': {'country': 'GB', 'sunset': 1504809058, 'message': 0.187, 'type': 1, 'id': 5091, 'sunrise': 1504761858},
                        'weather': [{'main': 'Drizzle', 'description': 'light intensity drizzle rain', 'icon': '09n', 'id': 310}],
                        'coord': {'lat': 51.51, 'lon': -0.13},
                        'base': 'stations', 'dt': 1504821000,
                        'main': {'pressure': 1007, 'temp_min': 15, 'temp_max': 17, 'temp': 15.88, 'humidity': 77},
                        'id': 100,
                        'wind': {'speed': 5.1, 'deg': 220},
                        'cod': 200}


@pytest.fixture
@mock.patch('weather.Weather.get_api_key')
def weather_obj_with_default_city(api_key_mocker):
    api_key_mocker.return_value = MOCKED_API_KEY
    return weather.Weather(use_default=True)


@pytest.fixture
def weather_obj():
    return weather.Weather


def test_default_city(weather_obj_with_default_city):
    assert weather_obj_with_default_city.city_id == weather.LONDON_ID


def test_weather_obj_api_key(weather_obj_with_default_city):
    assert weather_obj_with_default_city.api_key == MOCKED_API_KEY


@mock.patch("os.environ", MOCKED_ENV_VARS)
def test_get_api_key(weather_obj):
    assert weather_obj.get_api_key() == MOCKED_ENV_VARS.get('OPEN_WEATHER_MAP_API_KEY')


@mock.patch("os.environ", {})
def test_get_api_key_with_raw_input(weather_obj, API_KEY='Manually Entered API KEY'):
    with mock.patch('__builtin__.raw_input', side_effect=[API_KEY]):
        assert weather_obj.get_api_key() == API_KEY


@mock.patch("os.environ", {})
def test_get_api_key_with_empty_raw_input(weather_obj):
    with mock.patch('__builtin__.raw_input', side_effect=[None]):
        with pytest.raises(Exception):
            weather_obj.get_api_key()


def test_get_city_id_with_default(weather_obj_with_default_city):
    assert weather_obj_with_default_city.get_city_id() == weather.LONDON_ID


def test_get_city_id_with_id_as_string(weather_obj):
    with pytest.raises(Exception):
        weather_obj(city_id='12345').get_city_id()


@mock.patch('weather.Weather.get_country_code')
@mock.patch('weather.Weather.get_city_name')
@mock.patch('weather.json.load')
@mock.patch('weather.Weather.get_api_key')
def test_get_city_id(api_key_mocker, json_obj_mocker, city_name_mocker, country_code_mocker, weather_obj):
    api_key_mocker.return_value = MOCKED_API_KEY
    json_obj_mocker.return_value = MOCKED_CITY_LIST_JSON
    mocked_open = mock.mock_open()
    with mock.patch('weather.open', mocked_open, create=True):
        city_name_mocker.return_value = 'London'
        country_code_mocker.return_value = 'GB'
        assert weather_obj().get_city_id() == MOCKED_CITY_LIST_JSON[0].get('id')


@mock.patch('weather.Weather.get_country_code')
@mock.patch('weather.Weather.get_city_name')
@mock.patch('weather.json.load')
@mock.patch('weather.Weather.get_api_key')
def test_get_city_id_with_empty_input_values( api_key_mocker, json_obj_mocker, city_name_mocker, country_code_mocker, weather_obj):
    api_key_mocker.return_value = MOCKED_API_KEY
    json_obj_mocker.return_value = MOCKED_CITY_LIST_JSON
    mocked_open = mock.mock_open()
    with mock.patch('weather.open', mocked_open, create=True):
        city_name_mocker.return_value = ''
        country_code_mocker.return_value = ''
        assert not weather_obj().get_city_id()
        assert city_name_mocker.call_count == 3
        assert country_code_mocker.call_count == 3


@mock.patch('weather.Weather.get_api_key')
@mock.patch('weather.Weather.get_city_id')
def test_build_url(city_id_mocker, api_key_mocker, weather_obj, city_id = 100):
    api_key_mocker.return_value = MOCKED_API_KEY
    city_id_mocker.return_value = city_id
    expected_url = weather.API_URL + str(city_id) + '&units=' + 'metric' + '&APPID=' + MOCKED_API_KEY
    assert weather_obj().build_url()  == expected_url


@mock.patch('weather.Weather.build_url')
@mock.patch('weather.requests.get')
def test_get_weather_data(response_mocker, url_mocker, weather_obj_with_default_city):
    url_mocker.return_value = 'http://mockurl'
    response_mocker.return_value = mock.MagicMock(ok=True)
    response_mocker.return_value.json.return_value = MOCKED_JSON_RESPONSE
    assert weather_obj_with_default_city.get_weather_data() == MOCKED_JSON_RESPONSE


@mock.patch('weather.Weather.build_url')
@mock.patch('weather.requests.get')
def test_get_weather_data_with_failed_response(response_mocker, url_mocker, weather_obj_with_default_city):
    url_mocker.return_value = 'http://mockurl'
    response_mocker.return_value = mock.MagicMock(ok=False)
    with pytest.raises(weather.APIException):
        assert weather_obj_with_default_city.get_weather_data()


def test_degrees_to_compass(weather_obj):
    assert weather_obj.degrees_to_compass(degrees=10) == "N"


@mock.patch('weather.Weather.get_api_key')
def test_get_wind_details(api_mocker, weather_obj):
    assert weather_obj().get_wind_details(wind_dict=MOCKED_JSON_RESPONSE.get('wind')) == {'speed': 5.1, 'direction': 220}


@mock.patch('weather.Weather.get_api_key')
def test_get_wind_details_no_wind_direction(api_mocker, weather_obj):
    wind_details = MOCKED_JSON_RESPONSE.get('wind')
    wind_details['deg'] = None
    assert weather_obj().get_wind_details(wind_dict=wind_details) == {'speed': 5.1, 'direction': None}


@mock.patch('weather.Weather.unix_to_timestamp')
@mock.patch('weather.Weather.meters_per_second_to_mph')
@mock.patch('weather.Weather.degrees_to_compass')
@mock.patch('weather.Weather.get_wind_details')
@mock.patch('weather.Weather.get_weather_data')
def test_build_weather_dict(weather_data_mocker, wind_mocker, compass_mocker, wind_speed_mocker, timestamp_mocker, weather_obj_with_default_city):
    weather_data_mocker.return_value = MOCKED_JSON_RESPONSE
    compass_mocker.return_value = "N"
    wind_speed_mocker.return_value = 20
    timestamp_mocker.return_value = "2010-01-01"

    expected = {'city_name': 'London',
                'cloud_cover_percentage': 75,
                'visibility_metres': 10000,
                'min_temp': 15,
                'max_temp': 17,
                'pressure':1007,
                'wind_direction_compass': "N",
                'wind_speed': 20,
                'forecast_timestamp': "2010-01-01"}

    assert weather_obj_with_default_city.build_weather_dict() == expected
