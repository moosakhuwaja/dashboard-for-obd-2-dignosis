import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import os
from math import radians, cos, sin, asin, sqrt
from flask_login import current_user
from app import app, trip_number
import numpy as np

forgraph = pd.DataFrame()
maindf = pd.DataFrame()


def cleann():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)

    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        df = pd.read_csv(csv_path)
    if df.empty:
        return "No data available"

    df = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
             "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]
    df = df[(df != 0).all(axis=1)]

    # Remove null values
    df.dropna(inplace=True)

    # Remove duplicate rows
    df.drop_duplicates(inplace=True)

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    fmt = "%Y-%m-%d %H:%M:%S"
    df['time_stamp'] = pd.to_datetime(
        df['time_stamp'].replace("/", "-"), format=fmt, errors='coerce')
    problematic_dates = df.loc[df['time_stamp'].isnull()].index
    df.drop(problematic_dates, inplace=True)
    return df


def trip_details():
    df = cleann()
    # user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    # files = os.listdir(user_folder)

    # if len(files) == 1:
    #     csv_path = os.path.join(user_folder, files[0])
    #     df = pd.read_csv(csv_path)
    # if df.empty:
    #     return "No data available"
    # global maindf
    # maindf = df
    # Select necessary columns and drop rows with missing values
    df1 = df[['car_reg_no', 'engine_rpm', 'mass_air_flow_rate',
              'vehicle_speed', 'time_stamp']].dropna()

    df1 = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
              "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]

    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)

    # Convert timestamp to datetime and drop rows with problematic dates
    fmt = "%Y-%m-%d %H:%M:%S"
    df1['time_stamp'] = pd.to_datetime(
        df1['time_stamp'].replace("/", "-"), format=fmt, errors='coerce')
    problematic_dates = df1.loc[df1['time_stamp'].isnull()].index
    df1.drop(problematic_dates, inplace=True)

    # Identify trip numbers based on gaps in timestamps over 5 minutes
    df1['gap_over_5_mins'] = (df1['time_stamp'].diff()).dt.seconds > 300
    df1['trip_number'] = (df1['gap_over_5_mins'] == True).cumsum()

    # Group by trip number and calculate average engine RPM and mass air flow rate
    df1_grouped = df1.groupby('trip_number').agg(
        {'car_reg_no': 'first', 'engine_rpm': 'mean', 'mass_air_flow_rate': 'mean'})

    # Calculate fuel consumption (litres/km) for each trip based on mass air flow rate and engine RPM
    df1_grouped['fuel_consumption_per_km'] = (
        df1_grouped['mass_air_flow_rate'] / 14.7) * (1 / 720) * (60 / df1_grouped['engine_rpm']) * 100

    # Calculate average speed for each trip in km/h
    df1_grouped['speed'] = df1.groupby('trip_number')['vehicle_speed'].mean()

    # Convert speed from km/h to mph and calculate fuel efficiency (L/100km)
    df1_grouped['speed'] = df1_grouped['speed'] * 0.621371
    df1_grouped['fuel_efficiency'] = df1_grouped['fuel_consumption_per_km'] / \
        (df1_grouped['speed'] * 1.60934)

    # Calculate trip duration in minutes and distance in km
    df1_grouped['trip_duration'] = (df1.groupby('trip_number')['time_stamp'].max(
    ) - df1.groupby('trip_number')['time_stamp'].min()).dt.seconds / 60
    df1_grouped['distance_km'] = df1_grouped['speed'] * \
        df1_grouped['trip_duration'] / 60

    # Calculate fuel consumption in liters per trip
    df1_grouped['litres_per_trip'] = df1_grouped['fuel_consumption_per_km'] * \
        df1_grouped['distance_km']

    # Add start and end timestamps of each trip
    df1_grouped['start_timestamp'] = df1.groupby('trip_number')[
        'time_stamp'].min()
    df1_grouped['end_timestamp'] = df1.groupby('trip_number')[
        'time_stamp'].max()

    df1_grouped['trip_numberr'] = df1_grouped.index
    df1_grouped['fuel_consumption_per_kmm'] = df1_grouped['fuel_consumption_per_km']
    global forgraph
    forgraph = df1_grouped
    # Select necessary columns and drop rows with missing values
    df1_grouped = df1_grouped[['car_reg_no',  'trip_duration', 'distance_km']]
    df1_grouped.dropna(inplace=True)

    return df1_grouped


# def plot_speed_vs_time(trip_num):
#     # user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
#     # files = os.listdir(user_folder)

#     # if len(files) == 1:
#     #     csv_path = os.path.join(user_folder, files[0])
#     #     df = pd.read_csv(csv_path)
#     # if df.empty:
#     #     return "No data available"
#     df = cleann()
#     df_main = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
#                   "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]
#     df_main = df[(df != 0).all(axis=1)]

#     # Remove null values
#     df_main.dropna(inplace=True)

#     # Remove duplicate rows
#     df_main.drop_duplicates(inplace=True)

#     # Reset the index
#     df_main.reset_index(drop=True, inplace=True)
#     fmt = "%Y-%m-%d %H:%M:%S"
#     df_main['time_stamp'] = pd.to_datetime(
#         df_main['time_stamp'].str.replace("/", "-"), format=fmt, errors='coerce')
#     problematic_dates = df.loc[df['time_stamp'].isnull()].index
#     df_main.drop(problematic_dates, inplace=True)
#     # Get start and end timestamps for the specified trip
#     trip_row = forgraph.loc[forgraph['trip_numberr'] == trip_num]
#     start_time = trip_row['start_timestamp'].values[0]
#     end_time = trip_row['end_timestamp'].values[0]

#     # Filter the main dataset for timestamps within the trip's start and end times
#     df_filtered = df_main[(df_main['time_stamp'] >= start_time) & (
#         df_main['time_stamp'] <= end_time)]

#     # Generate time intervals for 5-second intervals
#     num_intervals = int(
#         np.ceil((end_time - start_time) / pd.Timedelta(seconds=5)))
# #     intervals = pd.timedelta_range(start='0 seconds', end=str(num_intervals * 5) + ' seconds', freq='5 seconds')[:num_intervals]
#     intervals = pd.timedelta_range(start='0 seconds', end=str(
#         num_intervals * 5) + ' seconds', freq='5s')[:num_intervals]

#     time_stamps = pd.Series(start_time + intervals)

#     # Calculate mean speed for each time interval
#     speeds = []
#     for interval in intervals:
#         interval_start = start_time + interval - pd.Timedelta(seconds=5)
#         interval_end = start_time + interval
#         interval_data = df_filtered[(df_filtered['time_stamp'] >= interval_start) & (
#             df_filtered['time_stamp'] <= interval_end)]
#         mean_speed = interval_data['vehicle_speed'].mean()
#         speeds.append(mean_speed)

#     # Plot speed vs time for the trip
# #     fig, ax = plt.subplots()
#     fig, ax = plt.subplots(figsize=(10, 5))
#     ax.plot(time_stamps, speeds)
#     ax.set_xlabel('Time')
#     ax.set_ylabel('Speed')
#     ax.set_title(f'Trip {trip_num}: Speed vs Time')

#     # Convert plot to PNG image and return it
#     img = io.BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     plot_url = base64.b64encode(img.getvalue()).decode()
#     return plot_url
def plot_speed_vs_time(trip_num):
    #     user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    #     files = os.listdir(user_folder)

    #     if len(files) == 1:
    #         csv_path = os.path.join(user_folder, files[0])
    #         df = pd.read_csv(csv_path)
    #     if df.empty:
    #         return "No data available"
    df_main = cleann()
#     df_main = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
#                   "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]
#     df_main = df[(df != 0).all(axis=1)]

#     # Remove null values
#     df_main.dropna(inplace=True)

#     # Remove duplicate rows
#     df_main.drop_duplicates(inplace=True)

#     # Reset the index
#     df_main.reset_index(drop=True, inplace=True)
#     fmt = "%Y-%m-%d %H:%M:%S"
#     df_main['time_stamp'] = pd.to_datetime(
#         df_main['time_stamp'].replace("/", "-"), format=fmt, errors='coerce')
#     problematic_dates = df.loc[df['time_stamp'].isnull()].index
#     df_main.drop(problematic_dates, inplace=True)
    # Get start and end timestamps for the specified trip
    trip_row = forgraph.loc[forgraph['trip_numberr'] == trip_num]
#     print(trip_row)
    start_time = trip_row['start_timestamp'].values[0]
    end_time = trip_row['end_timestamp'].values[0]

    # Filter the main dataset for timestamps within the trip's start and end times
    df_filtered = df_main[(df_main['time_stamp'] >= start_time) & (
        df_main['time_stamp'] <= end_time)]

    # Generate time intervals for 5-second intervals
    num_intervals = int(
        np.ceil((end_time - start_time) / pd.Timedelta(seconds=5)))
#     intervals = pd.timedelta_range(start='0 seconds', end=str(num_intervals * 5) + ' seconds', freq='5 seconds')[:num_intervals]
    intervals = pd.timedelta_range(start='0 seconds', end=str(
        num_intervals * 5) + ' seconds', freq='5s')[:num_intervals]

    time_stamps = pd.Series(start_time + intervals)

    # Calculate mean speed for each time interval
    speeds = []
    for interval in intervals:
        interval_start = start_time + interval - pd.Timedelta(seconds=5)
        interval_end = start_time + interval
        interval_data = df_filtered[(df_filtered['time_stamp'] >= interval_start) & (
            df_filtered['time_stamp'] <= interval_end)]
        mean_speed = interval_data['vehicle_speed'].mean()
        speeds.append(mean_speed)

    # Plot speed vs time for the trip
#     fig, ax = plt.subplots()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(time_stamps, speeds)
    ax.set_xlabel('Time')
    ax.set_ylabel('Speed')
    ax.set_title(f'Trip {trip_num}: Speed vs Time')

    # Convert plot to PNG image and return it
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url


def plot_coolant_vs_time(trip_num):
    #     user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    #     files = os.listdir(user_folder)

    #     if len(files) == 1:
    #         csv_path = os.path.join(user_folder, files[0])
    #         df = pd.read_csv(csv_path)
    #     if df.empty:
    #         return "No data available"
    df_main = cleann()
#     df_main = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
#                   "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]
#     df_main = df[(df != 0).all(axis=1)]

#     # Remove null values
#     df_main.dropna(inplace=True)

#     # Remove duplicate rows
#     df_main.drop_duplicates(inplace=True)

#     # Reset the index
#     df_main.reset_index(drop=True, inplace=True)
#     fmt = "%Y-%m-%d %H:%M:%S"
#     df_main['time_stamp'] = pd.to_datetime(
#         df_main['time_stamp'].replace("/", "-"), format=fmt, errors='coerce')
#     problematic_dates = df.loc[df['time_stamp'].isnull()].index
#     df_main.drop(problematic_dates, inplace=True)

    # Get start and end timestamps for the specified trip
    trip_row = forgraph.loc[forgraph['trip_numberr'] == trip_num]
    start_time = trip_row['start_timestamp'].values[0]
    end_time = trip_row['end_timestamp'].values[0]

    # Filter the main dataset for timestamps within the trip's start and end times
    df_filtered = df_main[(df_main['time_stamp'] >= start_time) & (
        df_main['time_stamp'] <= end_time)]

    # Generate time intervals for 1-minute intervals
    start_interval = pd.to_datetime(pd.Timestamp(start_time).round('1min'))
    end_interval = pd.to_datetime(pd.Timestamp(end_time).round('1min'))
    num_intervals = int(
        np.ceil((end_interval - start_interval) / pd.Timedelta(minutes=1)))
    intervals = pd.timedelta_range(start='0 seconds', end=str(
        num_intervals * 1) + ' minute', freq='1min')[:num_intervals]
    time_stamps = pd.Series(start_interval + intervals)

    # Calculate mean engine coolant temperature for each time interval
    coolant_temps = []
    for interval in intervals:
        interval_start = start_interval + interval - pd.Timedelta(minutes=1)
        interval_end = start_interval + interval
        interval_data = df_filtered[(df_filtered['time_stamp'] >= interval_start) & (
            df_filtered['time_stamp'] <= interval_end)]
        mean_coolant_temp = interval_data['engine_coolant_temperature'].mean()
        coolant_temps.append(mean_coolant_temp)

    fig, ax = plt.subplots()
    ax.plot(time_stamps, coolant_temps)
    ax.set_xlabel('Time')
    ax.set_ylabel('Engine Coolant Temperature')
    ax.set_title(f'Trip {trip_num}: Temperature vs Time')

    # Convert plot to PNG image and return it
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plot_html = f'<img src="data:image/png;base64,{plot_url}">'
    return plot_url
# def plot_coolant_vs_time(trip_num):
#     # user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
#     # files = os.listdir(user_folder)

#     # if len(files) == 1:
#     #     csv_path = os.path.join(user_folder, files[0])
#     #     df = pd.read_csv(csv_path)
#     # if df.empty:
#     #     return "No data available"

#     df = maindf

#     df_main = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
#                   "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]
#     df_main = df[(df != 0).all(axis=1)]

#     # Remove null values
#     df_main.dropna(inplace=True)

#     # Remove duplicate rows
#     df_main.drop_duplicates(inplace=True)

#     # Reset the index
#     df_main.reset_index(drop=True, inplace=True)
#     fmt = "%Y-%m-%d %H:%M:%S"
#     df_main['time_stamp'] = pd.to_datetime(
#         df_main['time_stamp'].str.replace("/", "-"), format=fmt, errors='coerce')
#     problematic_dates = df.loc[df['time_stamp'].isnull()].index
#     df_main.drop(problematic_dates, inplace=True)

#     # Get start and end timestamps for the specified trip
#     trip_row = forgraph.loc[forgraph['trip_numberr'] == trip_num]
#     start_time = trip_row['start_timestamp'].values[0]
#     end_time = trip_row['end_timestamp'].values[0]

#     # Filter the main dataset for timestamps within the trip's start and end times
#     df_filtered = df_main[(df_main['time_stamp'] >= start_time) & (
#         df_main['time_stamp'] <= end_time)]

#     # Generate time intervals for 1-minute intervals
#     start_interval = pd.to_datetime(pd.Timestamp(start_time).round('1min'))
#     end_interval = pd.to_datetime(pd.Timestamp(end_time).round('1min'))
#     num_intervals = int(
#         np.ceil((end_interval - start_interval) / pd.Timedelta(minutes=1)))
#     intervals = pd.timedelta_range(start='0 seconds', end=str(
#         num_intervals * 1) + ' minute', freq='1min')[:num_intervals]
#     time_stamps = pd.Series(start_interval + intervals)

#     # Calculate mean engine coolant temperature for each time interval
#     coolant_temps = []
#     for interval in intervals:
#         interval_start = start_interval + interval - pd.Timedelta(minutes=1)
#         interval_end = start_interval + interval
#         interval_data = df_filtered[(df_filtered['time_stamp'] >= interval_start) & (
#             df_filtered['time_stamp'] <= interval_end)]
#         mean_coolant_temp = interval_data['engine_coolant_temperature'].mean()
#         coolant_temps.append(mean_coolant_temp)

#     fig, ax = plt.subplots()
#     ax.plot(time_stamps, coolant_temps)
#     ax.set_xlabel('Time')
#     ax.set_ylabel('Engine Coolant Temperature')
#     ax.set_title('Engine Coolant Temperature vs Time')

#     # Convert plot to PNG image and return it
#     img = io.BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     plot_url = base64.b64encode(img.getvalue()).decode()
#     plot_html = f'<img src="data:image/png;base64,{plot_url}">'
#     return plot_url


def coolant_temp():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)

    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        df = pd.read_csv(csv_path)
    df1 = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
              "ambient_air_temperature", "time_stamp"]]

    df1 = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
              "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]

    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)

    df1['time_stamp'] = pd.to_datetime(df1['time_stamp'], errors='coerce')
    df1.dropna(axis=0, inplace=True)
    df1.sort_values(by='time_stamp', inplace=True)
    split_datetime = pd.to_datetime("2021-12-02 17:30")
    df_before = df1.loc[df1['time_stamp'] < split_datetime]
    df_after = df1.loc[df1['time_stamp'] >= split_datetime]
    df_after.isna().sum()
    unique_values = df_before['ambient_air_temperature'].unique()
    df_before.reset_index(inplace=True)
    df_after.reset_index(inplace=True)
    df_after = df_after.drop_duplicates(subset=["time_stamp"], keep="first")
    start_index = 1410
    end_index = 1700
    new_df_after = df_after.iloc[start_index:end_index+1]
    new_df_after = new_df_after[new_df_after['engine_coolant_temperature'] != 0.0]
    new_df_after_P = new_df_after[["engine_coolant_temperature"]].copy()
    new_df_after_P.reset_index(inplace=True)

    fig, ax = plt.subplots()
    ax.set_xlabel("time average time between min-max collant temp")
    ax.set_ylabel("temperature")
    ax.set_title("coolant temperature")
    ax.plot(new_df_after_P.index, new_df_after_P['engine_coolant_temperature'])

    # Convert plot to PNG image and return it
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return f'<img src="data:image/png;base64,{plot_url}">'


# def plot_sales():

#     df = pd.read_csv('UPLOAD_FOLDER/data.csv')
#     # df = df[["ENGINE_COOLANT_TEMP", "ENGINE_LOAD", "AMBIENT_AIR_TEMP","ENGINE_RPM","AIR_INTAKE_TEMP","SPEED"]]
#     # df.dropna(inplace=True)
#     # df['ENGINE_COOLANT_TEMP'] = pd.to_numeric(df['ENGINE_COOLANT_TEMP'], errors='coerce')
#     # df['AMBIENT_AIR_TEMP'] = pd.to_numeric(df['AMBIENT_AIR_TEMP'], errors='coerce')
#     # df['ENGINE_RPM'] = pd.to_numeric(df['ENGINE_RPM'], errors='coerce')
#     # df['AIR_INTAKE_TEMP'] = pd.to_numeric(df['AIR_INTAKE_TEMP'], errors='coerce')
#     # df['SPEED'] = pd.to_numeric(df['SPEED'], errors='coerce')

#     # fig, ax = plt.subplots()
#     # ax.scatter(df['AIR_INTAKE_TEMP'], df['ENGINE_COOLANT_TEMP'])
#     if df.empty:
#         return ("DataFrame is empty")
#     else:
#         return df.info()

#     # Convert plot to PNG image and return it
#     # img = io.BytesIO()
#     # plt.savefig(img, format='png')
#     # img.seek(0)
#     # plot_url = base64.b64encode(img.getvalue()).decode()


def fetch_trip_data():
    return 1


def acc_detect():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)

    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        data = pd.read_csv(csv_path)

    data.drop_duplicates(subset="time_stamp", keep='last')
    speed_threshold = 25
    rpm_threshold = 2500

    prev_speed = data.iloc[0]["vehicle_speed"]
    prev_rpm = data.iloc[0]["engine_rpm"]
    count = 0
    l1 = []
    for index, row in data.iterrows():
        speed = row["vehicle_speed"]
        rpm = row["engine_rpm"]

        if speed < prev_speed - speed_threshold and rpm < prev_rpm - rpm_threshold:
            e = "Sudden decrease in speed and RPM detected at index: ", str(
                row["time_stamp"])
            l1.append(e)
            count += 1

        prev_speed = speed
        prev_rpm = rpm
    if count != 0:
        return l1
    else:
        return "nothing unusual"


def fuel_consumption_per_trip():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)

    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        df = pd.read_csv(csv_path)

    # Select necessary columns and drop rows with missing values
    df1 = df[['car_reg_no', 'engine_rpm', 'mass_air_flow_rate',
              'vehicle_speed', 'time_stamp']].dropna()

    df1 = df[["engine_rpm", "vehicle_speed", "engine_coolant_temperature",
              "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]

    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)
    # Convert timestamp to datetime and drop rows with problematic dates
    fmt = "%Y-%m-%d %H:%M:%S"
    df1['time_stamp'] = pd.to_datetime(
        df1['time_stamp'].str.replace("/", "-"), format=fmt, errors='coerce')
    problematic_dates = df1.loc[df1['time_stamp'].isnull()].index
    df1.drop(problematic_dates, inplace=True)

    # Identify trip numbers based on gaps in timestamps over 5 minutes
    df1['gap_over_5_mins'] = (df1['time_stamp'].diff()).dt.seconds > 300
    df1['trip_number'] = (df1['gap_over_5_mins'] == True).cumsum()

    # Group by trip number and calculate average engine RPM and mass air flow rate
    df1_grouped = df1.groupby('trip_number').agg(
        {'car_reg_no': 'first', 'engine_rpm': 'mean', 'mass_air_flow_rate': 'mean'})

    # Calculate fuel consumption (litres/km) for each trip based on mass air flow rate and engine RPM
    df1_grouped['fuel_consumption_per_km'] = df1_grouped['mass_air_flow_rate'] / \
        14.7/454/6.701*3600/3.78541

    # Calculate average speed for each trip in km/h
    df1_grouped['speed'] = df1.groupby('trip_number')['vehicle_speed'].mean()

    # Convert speed from km/h to mph and calculate fuel efficiency (L/100km)
    df1_grouped['speed'] = df1_grouped['speed'] * 0.621371
    df1_grouped['fuel_efficiency'] = df1_grouped['fuel_consumption_per_km'] / \
        (df1_grouped['speed'] * 1.60934)

    # Calculate trip duration in minutes and distance in km
    df1_grouped['trip_duration'] = (df1.groupby('trip_number')['time_stamp'].max(
    ) - df1.groupby('trip_number')['time_stamp'].min()).dt.seconds / 60
    df1_grouped['distance_km'] = df1_grouped['speed'] * \
        df1_grouped['trip_duration'] / 60

    # Calculate fuel consumption in liters per trip

    df1_grouped['litres_per_trip'] = round(
        df1_grouped['fuel_consumption_per_km'] * df1_grouped['distance_km'], 2)

    # Select necessary columns and drop rows with missing values
    df1_grouped = df1_grouped[['car_reg_no', 'fuel_consumption_per_km',
                               'fuel_efficiency', 'trip_duration', 'distance_km', 'litres_per_trip']]
    df1_grouped.dropna(inplace=True)

    return df1_grouped
