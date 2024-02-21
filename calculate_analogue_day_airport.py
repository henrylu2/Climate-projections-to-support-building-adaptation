##### USE THIS TO CALCULATE AND FIND THE ANALOGOUS DAY in WRF DATA FOR EACH DAY IN STATION DATA #####
### Compares the wrf data at airport location to weather station data at airport ### 
### output -> csv file of matching days at the weather station to all available wrf days ###

# city_name <- str for city name
# weather_path <- path to standardized weather CanRCM4 weather files at airport locations
# station_id <- airport weather station ID
# summer_wrf_data <- WRF noUP data at airport location (summer)
# summer_wrf_dates <- WRF noUP dates (summer)
# winter_wrf_data <- WRF noUP data at airport location (winter)
# winter_wrf_dates <- WRF noUP dates (winter)
# output -> csv file with match day pairs and distance

from glob import glob
import numpy as np
import pandas as pd

city_name = 'cityname'

# Read in airport lat lon info
weather_path = "Standardized_Weatherfiles\\"
station_id = str(1234567) # weather station id
station_files = sorted(glob(weather_path+'*{}.npy'.format(station_id))) # get list of weather station standardized data files

# Read WRF airport station data 
summer_wrf_data = np.load('summer_wrf_mon_airport_station_loc.npy') # Read wrf airport data
summer_wrf_dates = np.load('summer_wrf_dates_order.npy') # Read the dates of wrf data in order
winter_wrf_data = np.load('non_summer_wrf_mon_airport_station_loc.npy')
winter_wrf_dates = np.load('non_summer_wrf_dates_order.npy') 

# weather station data columns
col_names = ['YEAR', 'MONTH', 'DAY', 'HOUR', 'YDAY', 'DRI_kJperm2_f100',
             'DHI_kJperm2_f100', 'DNI_kJperm2_f100', 'GHI_kJperm2_f100',
             'TCC_Percent_f100', 'RAIN_Mm_f100',
             'WDIR_ClockwiseDegFromNorth_f100', 'WSP_MPerSec_f100',
             'RHUM_Percent_f100', 'TEMP_K_f100', 'ATMPR_Pa_f100',
             'SNOWC_Yes1No0']
# output df columns
columns=['Original_Index_Order','Station Date','WRF Date','Distance']

for f in station_files:
    print('Working on file: ', f)
    gw_scenario = f.split('\\')[-1].split('_')[-2]
    station_id = f.split('\\')[-1].split('_')[-1].split('.')[0]

    station_data = np.load(f) 
    station_df = pd.DataFrame(station_data,columns=col_names)
    
    ### This section is for the summer months ###
    sub_station_df = station_df.loc[(station_df['MONTH']>=5) & (station_df['MONTH']<=8)] # Get only summer months
    sub_station_indices = sub_station_df.index
    df_dates = pd.to_datetime(sub_station_df[['YEAR','MONTH','DAY']]) # Get the dates in order of sub_station df
    df_dates = np.reshape(np.array(df_dates.dt.date),(-1,24)) # Get only the date and not hours
    
    sub_station_data = np.reshape(np.array(sub_station_df.iloc[:,8:]),(-1,24,9)) # Gets only necessary variables and reshape to daily (24hours)
    sub_station_data = np.swapaxes(sub_station_data,1,2) # Swap axes to match WRF data order
    
    # Create an empty array to store the distances
    distances = []
    
    # Loop through all station data to calculate the distances with station weather file
    counter = 0
    for i in sub_station_data:
        print(df_dates[counter,0])
        # Calculate the distance between testing and training datasets
        distance = np.sum((i - summer_wrf_data)**2,axis=(1,2))
        distances.append(distance)
        counter += 1
    distances = np.array(distances)
    
    # Find the position where distance==min (this is the most analogous day) 
    # These are the positions of the dates in the station data the correspond to the analog day in wrf data
    min_distance = np.argmin(distances, axis=1) 
    # With the position found above, find the corresponding date in wrf_dates at "position" 
    analog_days = summer_wrf_dates[min_distance]
    analog_vals = np.min(distances,axis=1)
    # Create an array with the matching pair days
    matching_pairs = np.swapaxes([sub_station_indices,df_dates.flatten(),np.repeat(analog_days,24),np.repeat(analog_vals,24)], 0, 1)
    # Save this info as DF to be read again at calibartion
    
    out_df1 = pd.DataFrame(matching_pairs,columns=columns)
    
    ### This section is for the non-summer months ###
    sub_station_df = station_df.loc[(station_df['MONTH']<5) | (station_df['MONTH']>8)] # Get only winter months
    sub_station_indices = sub_station_df.index
    df_dates = pd.to_datetime(sub_station_df[['YEAR','MONTH','DAY']]) # Get the dates in order of sub_station df
    df_dates = np.reshape(np.array(df_dates.dt.date),(-1,24)) # Get only the date and not hours
    
    sub_station_data = np.reshape(np.array(sub_station_df.iloc[:,8:]),(-1,24,9)) # Gets only necessary variables and reshape to daily (24hours)
    sub_station_data = np.swapaxes(sub_station_data,1,2) # Swap axes to match WRF data order
       
    # Create an empty array to store the distances
    distances = []
    
    # Loop through all station data to calculate the distances with station weather file
    counter = 0
    for i in sub_station_data:
        print(df_dates[counter,0])
        # Calculate the distance between testing and training datasets
        distance = np.sum((i - winter_wrf_data)**2,axis=(1,2))
        distances.append(distance)
        counter += 1
    distances = np.array(distances)
    
    # Find the position where distance==min (this is the most analogous day) 
    # These are the positions of the dates in the station data the correspond to the analog day in wrf data
    min_distance = np.argmin(distances, axis=1) 
    # With the position found above, find the corresponding date in wrf_dates at "position" 
    analog_days = winter_wrf_dates[min_distance]
    analog_vals = np.min(distances,axis=1)
    # Create an array with the matching pair days
    matching_pairs = np.swapaxes([sub_station_indices,df_dates.flatten(),np.repeat(analog_days,24),np.repeat(analog_vals,24)], 0, 1)
    # Save this info as DF to be read again at calibartion
    out_df2 = pd.DataFrame(matching_pairs,columns=columns)
    
    combined_df = pd.concat([out_df1,out_df2])
    sorted_df = combined_df.sort_values(by='Original_Index_Order')
    sorted_df.to_csv('{}_matching_pair_days_{}_{}.csv'.format(city_name,gw_scenario,station_id),columns=columns,index=False)