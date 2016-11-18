from stravalib import Client
import psycopg2
from ConfigParser import SafeConfigParser
import warnings


class Strava(object):
    """
    Class which holds all of our Strava API attributes along with conversion / helper methods
    """

    def __init__(self):
        """
        Instantiate the class
        :param token: access token to use to gain access
        """
        self.token = raw_input("Please enter your token here:")
        self.tablename = self.__class__.__name__.lower() + "_" + 'strava'

    def get_connection(self):
        """
        Method to connect to the Strava API
        :returns: connection
        """
        conn = Client(access_token=self.token)
        return conn

    def get_details(self):
        """
        Method which confirms the athlete is actually you.
        :returns: Message with your first name, surname and how many followers you have on Strava
        """
        conn = self.get_connection()
        athlete = conn.get_athlete()
        details = {'first_name': athlete.firstname, 'last_name': athlete.lastname, 'followers': athlete.follower_count}
        return details

    @staticmethod
    def distance_converter(qnty_obj):
        """
        Method which converts from metres to miles seeing as we live in the UK. We DON'T TALK IN KM's!!!
        :param qnty_obj: Quantity Class
        :returns: distance cycled in miles
        """
        metres = qnty_obj.get_num()
        miles = metres * 0.000621371
        return miles

    @staticmethod
    def real_watts(flag, watts):
        """
        Method which checks whether the watts which are shown are "estimated" or from a actual powermeter.
        If the watts are from a powermeter, show the average power, otherwise get rid of it as it's garbage data
        :param flag: boolean flag
        :param watts: average power
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
        sec = timedelta.total_seconds()
        return sec

    @staticmethod
    def metres_to_feet(qnty_obj):
        """
        Method which converts from metres into feet.
        :param qnty_obj: Quantity class
        :returns: elevation climbed in feet
        """
        metres = qnty_obj.get_num()
        feet = metres * 3.28084
        return feet

    def get_activities(self):
        """
        Main method which gets all historic ride data and transforms it accordingly so that we can insert the data
        into our a table to easily query
        """
        ride_info = []

        conn = self.get_connection()
        activities = conn.get_activities()
        for active in activities:
            ride_info.append((active.id,
                              active.name,
                              active.start_date.strftime('%Y-%m-%d'),
                              self.distance_converter(active.distance),
                              self.real_watts(active.device_watts, active.average_watts),
                              self.time_in_seconds(active.moving_time),
                              self.time_in_seconds(active.elapsed_time),
                              active.kudos_count,
                              self.metres_to_feet(active.total_elevation_gain),
                              active.kilojoules))
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
        self.strava = Strava()

    def get_config_details(self):
        """
        Gets our local connection details from a config file
        :return: config details
        """
        config = SafeConfigParser()
        config.read(self.config)
        details = dict(config.items(self.section))
        return details

    def connect(self):
        """
        Method for getting a connection
        :returns: DB Connection
        """
        conn = psycopg2.connect(**self.get_config_details())
        return conn

    def execute_sql(self, sql, data=None, executemany=False):

        conn = self.connect()
        cursor = conn.cursor()
        if data:
            cursor.executemany(sql, data) if executemany else cursor.execute(sql, data)
            conn.commit()
            rows = cursor.rowcount
            return rows
        cursor.execute(sql)
        conn.commit()
        rows = cursor.rowcount
        return rows

    def summary_printout(self, activity_list):
        """
        Method which prints out your lifetime summary stats
        :param activity_list: list which we will be iterating over
        :return: message containing our stats
        """
        summary = {'activities': len(activity_list),
                   'miles': sum(i[3] for i in activity_list if i[3] is not None),
                   'feet': sum(i[8] for i in activity_list if i[8] is not None),
                   'calories': sum(i[9] for i in activity_list if i[9] is not None)}
        message = \
            """Hello {first_name} {last_name}. You have {followers} followers on Strava\n
            You have recorded {act:,} activities\n
            Cycled {miles:,} miles\n
            Climbed {feet:,} feet\n
            Burned {cal:,} calories"""
        details = self.strava.get_details()
        print message.format(first_name=details['first_name'],
                             last_name=details['last_name'],
                             followers=details['followers'],
                             act=summary['activities'],
                             miles=int(summary['miles']),
                             feet=int(summary['feet']),
                             cal=int(summary['calories']))

    def insert_data(self):
        """
        Method which inserts our data
        """
        activities = self.strava.get_activities()
        rows = self.execute_sql("""insert into {tablename}
        (activity_id,
        name,
        _date,
        distance_miles,
        avg_power,
        moving_time_seconds,
        elapsed_time_seconds,
        kudos_count,
        elevation_feet,
        kilojoules) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (activity_id) do update
        set name=excluded.name,
        kudos_count=excluded.kudos_count""".format(tablename=self.strava.tablename), activities, executemany=True)
        print "{rows} rows inserted!".format(rows=rows)
        self.summary_printout(activities)


if __name__ == '__main__':
    DBConnection('config.conf', 'local').insert_data()
