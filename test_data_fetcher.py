import pytest
import mock
import data_fetcher
import datetime

API_KEY_MOCKER = {'STRAVA_ACCESS_TOKEN': 'ABC123'}


@pytest.fixture
@mock.patch('data_fetcher.StravaConnector.get_access_token')
def connector_with_key(api_token_mocker):
    api_token_mocker.return_value = API_KEY_MOCKER.get('STRAVA_ACCESS_TOKEN')
    return data_fetcher.StravaConnector()


@pytest.fixture
def connector():
    return data_fetcher.StravaConnector


@mock.patch('os.environ', API_KEY_MOCKER)
def test_get_access_token(connector):
    assert connector.get_access_token() == API_KEY_MOCKER.get('STRAVA_ACCESS_TOKEN')


@mock.patch("os.environ", {})
def test_get_access_token_with_raw_input(connector, API_KEY='Manually Entered API KEY'):
    with mock.patch('__builtin__.raw_input', side_effect=[API_KEY]):
        assert connector.get_access_token() == API_KEY


@mock.patch('data_fetcher.Client')
def test_get_connection(mocked_client, connector_with_key):
    mocked_client.return_value.protocol.get.return_value = {}
    assert connector_with_key.get_connection() == mocked_client()


@mock.patch('data_fetcher.Client')
def test_get_connection_throws_exception(mocked_client, connector_with_key):
    mocked_client.return_value.protocol.get = mock.MagicMock(side_effect=Exception)
    with pytest.raises(Exception):
        connector_with_key.get_connection()


@mock.patch('data_fetcher.StravaConnector.get_connection')
def test_get_details(mocked_connection, connector_with_key):
    mocked_details = mock.MagicMock(firstname='Aaron', lastname='Olszewski', follower_count=200)
    mocked_connection.return_value.get_athlete.return_value = mocked_details
    assert connector_with_key.get_details() == {'first_name': mocked_details.firstname,
                                                'last_name': mocked_details.lastname,
                                                'followers': mocked_details.follower_count
                                                }


@mock.patch('data_fetcher.StravaConnector.metres_to_feet')
@mock.patch('data_fetcher.StravaConnector.time_in_seconds')
@mock.patch('data_fetcher.StravaConnector.real_watts')
@mock.patch('data_fetcher.StravaConnector.distance_converter')
@mock.patch('data_fetcher.StravaConnector.get_connection')
def test_get_activities(mocked_connection, mocked_converter, mocked_watts, mocked_time_seconds, mocked_metres,
                        connector_with_key):

    mocked_converter.return_value = 100
    mocked_watts.return_value = 100
    mocked_time_seconds.return_value = 100
    mocked_metres.return_value = 100
    mocked_activity = mock.MagicMock(
        id=1,
        name='Ride',
        start_date=datetime.datetime(2017, 1, 1),
        distance=100,
        device_watts=True,
        average_watts=300,
        moving_time=100,
        elapsed_time=100,
        kudos_count=10,
        total_elevation_gain=100,
        kilojoules=100,
        location_country='USA',
        location_city='San Francisco',
        start_longitude='50',
        start_latitude='50',
        trainer=False,
        total_photo_count=10
    )
    mocked_activity.configure_mock(name='Ride')
    mocked_connection.return_value.get_activities.return_value = [mocked_activity]
    assert connector_with_key.get_activities() == [
        (1, 'Ride', '2017-01-01', 100, 100, 100, 100, 10, 100, 100, 'USA', 'San Francisco', '50', '50', False, 10),
    ]


@pytest.fixture
def get_db_connection():
    return data_fetcher.DBConnection(config='Test', section='Test')


@mock.patch('data_fetcher.SafeConfigParser')
def test_get_config_details(mocked_config, get_db_connection):
    config_items = [('host', 'localhost'), ('user', 'test')]
    mocked_config.return_value.items.return_value = config_items
    results = get_db_connection.get_config_details()
    mocked_config.return_value.read.assert_called_with(get_db_connection.config)
    assert results == dict(config_items)


@mock.patch('data_fetcher.DBConnection.get_config_details')
@mock.patch('data_fetcher.psycopg2.connect')
def test_connect(mocked_connection, mocked_config, get_db_connection):
    config = {'user': 'postgres', 'host': 'localhost'}
    mocked_config.return_value = {'user': 'postgres', 'host': 'localhost'}
    assert get_db_connection.connect() == mocked_connection.return_value
    mocked_connection.assert_called_with(**config)


@mock.patch('data_fetcher.DBConnection.connect')
def test_execute_sql(connect_mocker, get_db_connection):
    conn = connect_mocker.return_value.__enter__()
    cursor = conn.cursor.return_value.__enter__()
    assert cursor.rowcount == get_db_connection.execute_sql(sql='TEST')
    cursor.execute.assert_called_with('TEST')


@mock.patch('data_fetcher.Strava')
def test_get_field_names(mocked_model, get_db_connection, name='Test'):
    field = mock.MagicMock()
    field.configure_mock(name=name)
    mocked_model._meta.get_fields.return_value = [field, ]
    assert get_db_connection.get_field_names(mocked_model) == [name]


@mock.patch('data_fetcher.DBConnection.execute_sql')
@mock.patch('data_fetcher.DBConnection.get_placement_holders')
@mock.patch('data_fetcher.DBConnection.get_field_names')
def test_insert_data(field_names_mocker, holders_mocker, execute_mocker, get_db_connection, update_fields=['kudos']):

    get_db_connection.table = 'Test'
    fields = ['Test']
    holders = '%s'
    field_names_mocker.return_value = fields
    holders_mocker.return_value = holders
    fields_to_update = ", ".join("{field}=excluded.{field}".format(field=field) for field in update_fields)
    sql = """insert into {table_name} ({fields}) values ({holders}) on conflict (activity_id) do update set {update_columns}""".format(
        table_name=get_db_connection.table, fields=",".join(fields), holders=holders, update_columns=fields_to_update
    )
    data = ''
    get_db_connection.insert_data(data=data, update_fields=update_fields)
    execute_mocker.assert_called_with(sql=sql, data=data, executemany=True)