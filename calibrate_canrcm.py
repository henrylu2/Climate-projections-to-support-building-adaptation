##### Use this to calibrate the bc'ed canrcm4 data with urban signatures ###

# out_path -> path to write calibrated data to
# canrcm_path <- path to CanRCM4 data 
# snow_path <- path to CanRCM4 snow depth data
# urbansig_path <- path to urban signatures for a specific location
# airport_name <- string for the city AIRPORT that is being calibrated 
# out_loc_name <- name of the urban location that is being calibrated (may not be the same as airport)
# station_id <- string of the airport weather station ID that is being corrected
    
import numpy as np
import pandas as pd 
from glob import glob

# Path to write out to
out_path = 'output_path\\'

# CanRCM4 data paths
canrcm_path = 'bc_canrcm_data_path\\'
snow_path = 'snow_depth_path\\'

urbansig_path = 'urban_signatures_path\\'
airport_name = 'city'
out_loc_name = 'city'
station_id = '1234567'
gw_scenarios = ['Historical', 'GW0.5', 'GW1.0', 'GW1.5', 'GW2.0', 'GW2.5', 'GW3.0', 'GW3.5']
wrf_var_order = ['GHI','RH','WSP','WDIR','TCC','TEMP','PRES','SNOWH','RAIN'] # output file variable order

# weather station desired variable order, use when subsetting to get matching wrf order
weather_var_order = ['GHI_kJperm2_f100','RHUM_Percent_f100','WSP_MPerSec_f100',
                     'WDIR_ClockwiseDegFromNorth_f100','TCC_Percent_f100',
                     'TEMP_K_f100','ATMPR_Pa_f100','SNOWC_Yes1No0','RAIN_Mm_f100']  
final_var_order = ['RUN','YEAR','MONTH','DAY','HOUR','YDAY',
                   'GHI_kJperm2_f100','TCC_Percent_f100','RAIN_Mm_f100',
                   'WDIR_ClockwiseDegFromNorth_f100','WSP_MPerSec_f100',
                   'RHUM_Percent_f100','TEMP_K_f100','ATMPR_Pa_f100',
                   'SNOWC_Yes1No0','SND_Cm_f100']
solar_split_var_names = ['RUN','YEAR','MONTH','DAY','HOUR','YDAY',
                         'rsds_kjperm2','clt_per','rain_mm','wdr_deg','wsp_mpers',
                         'hurs_per','tas_degc','ps_pa','snowc_yes1no0','snd_cm']

# add the signatures to bc'ed canrcm4 data airport stations
for gw in gw_scenarios:
    file_name = '{}_matching_pair_days_{}_{}.csv'.format(airport_name, gw, station_id)
    print(file_name)
    
    analog_days = pd.read_csv(file_name)
    wrf_days = analog_days['WRF Date']
    
    # generate a new time series of urban signatures based on these analog days
    urban_signature_files = [glob(urbansig_path+'{}_urban_signature.npy'.format(x))[0] for x in wrf_days[::24]]
    combined_data = np.array([np.load(fname) for fname in urban_signature_files]) # read all of the urban signature files in the same order
    combined_data = np.reshape(combined_data,(-1,9)) # flatten axis to match canrcm_data
    
    # the file to get snow depth from
    # snow depth from canrcm is in units CM (wrf is in m)
    snow_file = glob(snow_path+'snowdepth_*{}_{}.csv'.format(gw,station_id))[0]
    snow_data = pd.read_csv(snow_file)
    corrected_snow = snow_data['snd_cm'] + combined_data[:,7]*100 # units cm
    
    # Get the canrcm data at corresponding airport
    canrcm_data = pd.read_csv(canrcm_path+'Weatherfile_{}_{}.csv'.format(gw, station_id))
    canrcm_dates = canrcm_data[['RUN','YEAR','MONTH','DAY','HOUR','YDAY']] # get the misc data columns for later
    canrcm_subset = canrcm_data[weather_var_order].copy() # get the variables needed to correct
    
    corrected_canrcm = canrcm_subset/100 + combined_data # add the urban signatures onto canrcm data
    # Keep the corrected data within reasonable ranges 
    corrected_canrcm.loc[corrected_canrcm['GHI_kJperm2_f100'] <= 0, 'GHI_kJperm2_f100'] = 0
    corrected_canrcm.loc[corrected_canrcm['RHUM_Percent_f100'] < 0, 'RHUM_Percent_f100'] = 0
    corrected_canrcm.loc[corrected_canrcm['RHUM_Percent_f100'] >= 100, 'RHUM_Percent_f100'] = 100
    corrected_canrcm.loc[corrected_canrcm['WSP_MPerSec_f100'] <= 0, 'WSP_MPerSec_f100'] = 0
    corrected_canrcm['WDIR_ClockwiseDegFromNorth_f100'] = corrected_canrcm['WDIR_ClockwiseDegFromNorth_f100'] % 360
    corrected_canrcm.loc[corrected_canrcm['TCC_Percent_f100'] <= 0, 'TCC_Percent_f100'] = 0
    corrected_canrcm.loc[corrected_canrcm['TCC_Percent_f100'] >= 100, 'TCC_Percent_f100'] = 100
    corrected_canrcm.loc[corrected_canrcm['RAIN_Mm_f100'] <= 0, 'RAIN_Mm_f100'] = 0
    
    # combine the dates and corrected data, round to two decimals
    combined_canrcm = pd.concat([canrcm_dates,corrected_canrcm,corrected_snow],axis=1).round(2) 
    # Calculate new snow flag - do after multiply by 100 to stay 0 or 1
    combined_canrcm.loc[combined_canrcm['snd_cm'] > 0, 'SNOWC_Yes1No0'] = 1
    combined_canrcm.loc[combined_canrcm['snd_cm'] <= 0, 'SNOWC_Yes1No0'] = 0
    
    combined_canrcm.rename(columns={'snd_cm': 'SND_Cm_f100'}, inplace=True)
    combined_canrcm.loc[combined_canrcm['SND_Cm_f100'] <= 0, 'SND_Cm_f100'] = 0 # make sure no snow depth less than 0
    
    final_df = combined_canrcm[final_var_order] # Reorder the variables - the order matters
    final_df.columns = solar_split_var_names # Rename the columns corresponding to solar split model
    final_df.loc[:, 'time_lst'] = pd.to_datetime(final_df[['YEAR', 'MONTH', 'DAY', 'HOUR']]) # Add pandas datetime objects column
    final_df.to_csv(out_path+'{}_urban_Weatherfile_{}_{}.csv'.format(out_loc_name,gw,station_id),index=False)