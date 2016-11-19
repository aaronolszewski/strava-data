# strava-data

Django App which gets all historical data from Strava API (given a Access Token) and then exposes this (once transformed)
as an API endpoint.

## Running Locally
Ensure you have a local Postgres database (version 9.5 or higher) and make sure you have created a postgres user.

```
$ createuser -s postgres
```

Clone the project to a local directory and create an virtualenv e.g. strava-data:

```
$ mkvirtualenv strava-data
```

Once created, run the make file from the root folder (strava-data)

```
(strava-data) $ make
```

You will be asked to enter your Strava Access Token to fetch all your data from Strava's API so make sure you have it ready.

Once completed, you can view your data using the below URL (make sure you are logged into admin) :

http://127.0.0.1:8000/strava/


## Tableau Visualization of all my cycling data
https://public.tableau.com/profile/aaronolszewski#!/vizhome/StravaData_0/StravaCyclingDashboard
