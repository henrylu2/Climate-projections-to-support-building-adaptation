##### USE THIS SCRIPT TO GET AND SAVE THE STANDARDIZED WRF DATA AT AIRPORT LOCATIONS #####
### Need to do this for the analog days step ###
### Saved files have dimenions (# days, vars, 24)

# summer_path <- path where WRF noUP Summer simulations are located
# ncfile <- ncfile to get lat/lon coord from 
# X_loc <- weather station information [ID, lat, lon]
# X_sn_index, X_ew_index <- south-north and east-west array index for the airport location X_loc
# output -> .npy files that save the standardized values for all days in order of the dates
    
import numpy as np
from netCDF4 import Dataset
from wrf import (getvar, latlon_coords)
from glob import glob

summer_path = "summer_wrf_data\\"
nonsummer_path = "winter_wrf_data\\"

ncfile = Dataset('geo_em.d03.nc')
lu = getvar(ncfile, "LU_INDEX")
lats, lons = np.array(latlon_coords(lu))

# Airport locations
ott_loc = [6106001,45.32,-75.67] 
mon_loc = [7025251,45.47,-73.74]

ott_sn_index, ott_ew_index = np.unravel_index(np.argmin((ott_loc[2]-lons)**2+(ott_loc[1]-lats)**2),lons.shape) # Get closest grid
print(lons[ott_sn_index,ott_ew_index],lats[ott_sn_index,ott_ew_index])

mon_sn_index, mon_ew_index = np.unravel_index(np.argmin((mon_loc[2]-lons)**2+(mon_loc[1]-lats)**2),lons.shape) # Get closest grid
print(lons[mon_sn_index,mon_ew_index],lats[mon_sn_index,mon_ew_index])


### Get Summer data
summer_files = sorted(glob(summer_path+'*standardized*.npy'))
# initialize empty array (faster)
combined_data1 = np.zeros((len(summer_files), 9,24)) 
combined_data2 = np.zeros((len(summer_files), 9,24))
all_dates = [] # Save the date of WRF data, necessary to calculate analog day
# For ottawa and montreal airport 
for i, fn in enumerate(summer_files):
    print(i, fn)
    date = fn.split('\\')[-1].split('_')[0] 
    combined_data1[i, :, :] = np.load(fn)[:,:,ott_sn_index,ott_ew_index] # append ottawa data
    combined_data2[i, :, :] = np.load(fn)[:,:,mon_sn_index,mon_ew_index] # append montreal data
    all_dates.append(date)

np.save('summer_wrf_ott_airport_station_loc.npy',combined_data1,allow_pickle=False)
np.save('summer_wrf_mon_airport_station_loc.npy',combined_data2,allow_pickle=False)
np.save('summer_wrf_dates_order.npy',np.array(all_dates),allow_pickle=True)


# Get non-summer data
nonsummer_files = sorted(glob(nonsummer_path+'*standardized*.npy'))
# initialize empty array (faster)
combined_data1 = np.zeros((len(nonsummer_files), 9,24)) 
combined_data2 = np.zeros((len(nonsummer_files), 9,24))
all_dates = [] # Save the date of WRF data, necessary to calculate analog day
# For ottawa and montreal airport 
for i, fn in enumerate(nonsummer_files):
    print(i, fn)
    date = fn.split('\\')[-1].split('_')[0] 
    combined_data1[i, :, :] = np.load(fn)[:,:,ott_sn_index,ott_ew_index] # append ottawa data
    combined_data2[i, :, :] = np.load(fn)[:,:,mon_sn_index,mon_ew_index] # append montreal data
    all_dates.append(date)

np.save('non_summer_wrf_ott_airport_station_loc.npy',combined_data1,allow_pickle=False)
np.save('non_summer_wrf_mon_airport_station_loc.npy',combined_data2,allow_pickle=False)
np.save('non_summer_wrf_dates_order.npy',np.array(all_dates),allow_pickle=True)