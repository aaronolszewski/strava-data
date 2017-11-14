# -*- coding: utf-8 -*-
from stravalib import Client
import psycopg2
from ConfigParser import SafeConfigParser
import warnings
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datawarehouse.settings")
django.setup()
from strava.models import Strava
from datawarehouse.settings import APP_NAME


class StravaConnector(object):

    """
    Class for connecting to the Strava API given a public access token
    """

    def __init__(self):
        """
        Instantiate the class by entering your access token
        """
        self.token = self.get_access_token()
        self.tablename = APP_NAME + Strava.__name__.lower()

    @staticmethod
    def get_access_token():
        token = os.environ.get('STRAVA_ACCESS_TOKEN')
        if token:
            return token
        else:
            return raw_input("Please enter your token here:")

    def get_connection(self):
        """
        Method to connect to the Strava API given a access token
        :return: connection
        """
        conn = Client(access_token=self.token)
        try:
            conn.protocol.get('/athlete')
        except Exception as e:
            print "Authorisation Error: {error}".format(error=e)
            raise e
        return conn

    def get_details(self):
        """
        Method which confirms the athlete is actually you.
        :return: dict with your first name, surname and how many followers you have on Strava
        """
        conn = self.get_connection()
        athlete = conn.get_athlete()
        return {
            'first_name': athlete.firstname,
            'last_name': athlete.lastname,
            'followers': athlete.follower_count
        }

    @staticmethod
    def distance_converter(qnty_obj):
        """
        Method which converts from metres to miles seeing as we live in the UK. We DON'T TALK IN KM's!!!
        :param qnty_obj: units.quantity.Quantity instance
        :return: distance cycled in miles
        """
        metres = qnty_obj.get_num()
        return metres * 0.000621371

    @staticmethod
    def real_watts(flag, watts):
        """
        Method which checks whether the watts which are shown are "estimated" or from a actual powermeter.
        If the watts are from a powermeter, show the average power, otherwise get rid of it as it's garbage data
        :param flag: boolean flag
        :param watts: average power
        :return: average watts for activity
        """
        if flag is True:
            return watts

    @staticmethod
    def time_in_seconds(timedelta):
        """
        method which takes in a timedelta object and converts it to seconds
        :param timedelta: timedelta object
        :returns: time of ride in seconds
        """
        return timedelta.total_seconds()

    @staticmethod
    def metres_to_feet(qnty_obj):
        """
        Method which converts from metres into feet.
        :param qnty_obj: units.quantity.Quantity instance
        :return: elevation climbed in feet
        """
        metres = qnty_obj.get_num()
        return metres * 3.28084

    def get_activities(self):
        """
        Main method which gets all historic ride data and transforms it accordingly so that we can insert the data
        into our a Postgres table to easily query
        """
        ride_info = []
        conn = self.get_connection()
        activities = conn.get_activities()
        for activity in activities:
            ride_info.append((activity.id,
                              activity.name,
                              activity.start_date.strftime('%Y-%m-%d'),
                              self.distance_converter(activity.distance),
                              self.real_watts(activity.device_watts, activity.average_watts),
                              self.time_in_seconds(activity.moving_time),
                              self.time_in_seconds(activity.elapsed_time),
                              activity.kudos_count,
                              self.metres_to_feet(activity.total_elevation_gain),
                              activity.kilojoules,
                              activity.location_country,
                              activity.location_city,
                              activity.start_longitude,
                              activity.start_latitude,
                              activity.trainer,
                              activity.total_photo_count))
            if len(ride_info) % 100 == 0:
                print "{rows} rides processed so far...".format(rows=len(ride_info))
        return ride_info


class DBConnection(object):
    """
    Class for getting DB Connections
    """

    def __init__(self, config, section):
        """
        Initialise the class by reading a config file and config section
        :param config: config file to read from
        :param section: section of config file
        """
        self.config = config
        self.section = section
        warnings.filterwarnings("ignore")
        self.table = APP_NAME + '_' + Strava.__name__.lower()

    def get_config_details(self):
        """
        Gets our local connection details from a config file
        :return: config details
        """
        config = SafeConfigParser()
        config.read(self.config)
        return dict(config.items(self.section))

    def connect(self):
        """
        Method for getting a connection
        :returns: DB Connection
        """
        return psycopg2.connect(**self.get_config_details())

    def execute_sql(self, sql, data=None, executemany=False):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                if data:
                    cursor.executemany(sql, data) if executemany else cursor.execute(sql, data)
                    conn.commit()
                    return cursor.rowcount

                cursor.execute(sql)
                return cursor.rowcount

    @staticmethod
    def get_field_names(model):
        return [fields.name for fields in model._meta.get_fields()]

    @staticmethod
    def get_placement_holders(fields):
        return ",".join('%s' for x in fields)

    def insert_data(self, data, update_fields):
        """
        Method which inserts our data
        """
        fields = self.get_field_names(model=Strava)
        holders = self.get_placement_holders(fields)
        fields_to_update = ", ".join("{field}=excluded.{field}".format(field=field) for field in update_fields)
        sql = "insert into {table_name} ({fields}) " \
              "values ({holders}) on conflict (activity_id) do update set {update_columns}".format(
            table_name=self.table, fields=",".join(fields), holders=holders, update_columns=fields_to_update
        )
        rows = self.execute_sql(sql=sql, data=data, executemany=True)
        print "{rows} rows inserted!".format(rows=rows)


def calculate_list_index(index, activity_list, calc=sum):
    """
    :param index:
    :param activity_list:
    :param calc:
    :return: calculation for a given index in a list
    """
    return calc(activity[index] for activity in activity_list if activity[index] is not None)


def summary_printout(user_details, activity_list):
    """
    Method which prints out your lifetime summary stats
    :param user_details: details about the Strava user
    :param activity_list: list which we will be iterating over
    :return: message containing our stats
    """
    summary = {'activities': len(activity_list),
               'miles': calculate_list_index(index=3, activity_list=activity_list),
               'feet': calculate_list_index(index=8, activity_list=activity_list),
               'calories': calculate_list_index(index=9, activity_list=activity_list),
               'min_date': calculate_list_index(index=2, activity_list=activity_list, calc=min),
               'max_date': calculate_list_index(index=2, activity_list=activity_list, calc=max)}
    message = \
        """Hello {first_name} {last_name}. You have {followers} followers on Strava\n
        You have recorded {act:,} activities between {min_date} and {max_date}\n
        Cycled {miles:,} miles\n
        Climbed {feet:,} feet\n
        Burned {cal:,} calories"""

    return message.format(first_name=user_details['first_name'],
                          last_name=user_details['last_name'],
                          followers=user_details['followers'],
                          act=summary['activities'],
                          miles=int(summary['miles']),
                          feet=int(summary['feet']),
                          cal=int(summary['calories']),
                          min_date=summary['min_date'],
                          max_date=summary['max_date'])

if __name__ == '__main__':
    strava = StravaConnector()
    activities = strava.get_activities()
    DBConnection('config.conf', 'local').insert_data(data=activities, update_fields=['kudos_count', 'photo_count', 'name'])
    print summary_printout(user_details=strava.get_details(), activity_list=activities)
