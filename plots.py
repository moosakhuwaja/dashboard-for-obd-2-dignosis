import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import os
from math import radians, cos, sin, asin, sqrt
from flask_login import current_user
from app import app

def coolant_temp():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)

    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        df = pd.read_csv(csv_path)
    df1 = df[["engine_rpm","vehicle_speed","engine_coolant_temperature","ambient_air_temperature","time_stamp"]]


    df1 = df[ ["engine_rpm", "vehicle_speed", "engine_coolant_temperature", "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]


    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)


    df1['time_stamp'] = pd.to_datetime(df1['time_stamp'],errors='coerce')
    df1.dropna(axis=0, inplace = True)
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
    

def trip_details():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)
    
    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        df = pd.read_csv(csv_path)
    if df.empty:
        return "No data available"

    # Select necessary columns and drop rows with missing values
    df1 = df[['car_reg_no', 'engine_rpm', 'mass_air_flow_rate', 'vehicle_speed', 'time_stamp']].dropna()

    df1 = df[ ["engine_rpm", "vehicle_speed", "engine_coolant_temperature", "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]


    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)

    # Convert timestamp to datetime and drop rows with problematic dates
    fmt = "%Y-%m-%d %H:%M:%S"
    df1['time_stamp'] = pd.to_datetime(df1['time_stamp'].str.replace("/", "-"), format=fmt, errors='coerce')
    problematic_dates = df1.loc[df1['time_stamp'].isnull()].index
    df1.drop(problematic_dates, inplace=True)

    # Identify trip numbers based on gaps in timestamps over 5 minutes
    df1['gap_over_5_mins'] = (df1['time_stamp'].diff()).dt.seconds > 300
    df1['trip_number'] = (df1['gap_over_5_mins'] == True).cumsum()

    # Group by trip number and calculate average engine RPM and mass air flow rate
    df1_grouped = df1.groupby('trip_number').agg({'car_reg_no': 'first', 'engine_rpm': 'mean', 'mass_air_flow_rate': 'mean'})

    # Calculate fuel consumption (litres/km) for each trip based on mass air flow rate and engine RPM
    df1_grouped['fuel_consumption_per_km'] = (df1_grouped['mass_air_flow_rate'] / 14.7) * (1 / 720) * (60 / df1_grouped['engine_rpm']) * 100

    # Calculate average speed for each trip in km/h
    df1_grouped['speed'] = df1.groupby('trip_number')['vehicle_speed'].mean()

    # Convert speed from km/h to mph and calculate fuel efficiency (L/100km)
    df1_grouped['speed'] = df1_grouped['speed'] * 0.621371
    df1_grouped['fuel_efficiency'] = df1_grouped['fuel_consumption_per_km'] / (df1_grouped['speed'] * 1.60934)

    # Calculate trip duration in minutes and distance in km
    df1_grouped['trip_duration'] = (df1.groupby('trip_number')['time_stamp'].max() - df1.groupby('trip_number')['time_stamp'].min()).dt.seconds / 60
    df1_grouped['distance_km'] = df1_grouped['speed'] * df1_grouped['trip_duration'] / 60
    
    # Calculate fuel consumption in liters per trip
    df1_grouped['litres_per_trip'] = df1_grouped['fuel_consumption_per_km'] * df1_grouped['distance_km']

    # Select necessary columns and drop rows with missing values
    df1_grouped = df1_grouped[['car_reg_no',  'trip_duration', 'distance_km']]
    df1_grouped.dropna(inplace=True)

    return df1_grouped


def acc_detect():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.name)
    files = os.listdir(user_folder)
    
    if len(files) == 1:
        csv_path = os.path.join(user_folder, files[0])
        data = pd.read_csv(csv_path)
    
    data.drop_duplicates(subset ="time_stamp",keep='last')
    speed_threshold = 25 
    rpm_threshold = 2500


    prev_speed = data.iloc[0]["vehicle_speed"]
    prev_rpm = data.iloc[0]["engine_rpm"]
    count=0
    l1=[]
    for index, row in data.iterrows():
        speed = row["vehicle_speed"]
        rpm = row["engine_rpm"]

        if speed < prev_speed - speed_threshold and rpm < prev_rpm - rpm_threshold:
            e= "Sudden decrease in speed and RPM detected at index: ", str(row["time_stamp"])
            l1.append(e)
            count+=1


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
    df1 = df[['car_reg_no', 'engine_rpm', 'mass_air_flow_rate', 'vehicle_speed', 'time_stamp']].dropna()

    df1 = df[ ["engine_rpm", "vehicle_speed", "engine_coolant_temperature", "ambient_air_temperature", "time_stamp", "car_reg_no", "mass_air_flow_rate"]]


    df1 = df1[(df1 != 0).all(axis=1)]

    # Remove null values
    df1.dropna(inplace=True)

    # Remove duplicate rows
    df1.drop_duplicates(inplace=True)

    # Reset the index
    df1.reset_index(drop=True, inplace=True)
    # Convert timestamp to datetime and drop rows with problematic dates
    fmt = "%Y-%m-%d %H:%M:%S"
    df1['time_stamp'] = pd.to_datetime(df1['time_stamp'].str.replace("/", "-"), format=fmt, errors='coerce')
    problematic_dates = df1.loc[df1['time_stamp'].isnull()].index
    df1.drop(problematic_dates, inplace=True)

    # Identify trip numbers based on gaps in timestamps over 5 minutes
    df1['gap_over_5_mins'] = (df1['time_stamp'].diff()).dt.seconds > 300
    df1['trip_number'] = (df1['gap_over_5_mins'] == True).cumsum()

    # Group by trip number and calculate average engine RPM and mass air flow rate
    df1_grouped = df1.groupby('trip_number').agg({'car_reg_no': 'first', 'engine_rpm': 'mean', 'mass_air_flow_rate': 'mean'})

    # Calculate fuel consumption (litres/km) for each trip based on mass air flow rate and engine RPM
    df1_grouped['fuel_consumption_per_km'] = df1_grouped['mass_air_flow_rate'] /14.7/454/6.701*3600/3.78541

    # Calculate average speed for each trip in km/h
    df1_grouped['speed'] = df1.groupby('trip_number')['vehicle_speed'].mean()

    # Convert speed from km/h to mph and calculate fuel efficiency (L/100km)
    df1_grouped['speed'] = df1_grouped['speed'] * 0.621371
    df1_grouped['fuel_efficiency'] = df1_grouped['fuel_consumption_per_km'] / (df1_grouped['speed'] * 1.60934)

    # Calculate trip duration in minutes and distance in km
    df1_grouped['trip_duration'] = (df1.groupby('trip_number')['time_stamp'].max() - df1.groupby('trip_number')['time_stamp'].min()).dt.seconds / 60
    df1_grouped['distance_km'] = df1_grouped['speed'] * df1_grouped['trip_duration'] / 60
    
    # Calculate fuel consumption in liters per trip
    
    df1_grouped['litres_per_trip'] = round(df1_grouped['fuel_consumption_per_km'] * df1_grouped['distance_km'], 2)

    # Select necessary columns and drop rows with missing values
    df1_grouped = df1_grouped[['car_reg_no', 'fuel_consumption_per_km', 'fuel_efficiency', 'trip_duration', 'distance_km', 'litres_per_trip']]
    df1_grouped.dropna(inplace=True)

    return df1_grouped
