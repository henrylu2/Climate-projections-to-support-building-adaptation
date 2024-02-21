##### USE THIS CODE TO CALCULATE THE URBAN SIGNATURE ACQUIRED BETWEEN 
##### AN URBAN LOCATION AND AIRPORT IN A CITY

# utc <- time zone correction for airport location
# X_out_path <- path to output urban signatures 
# X_lat, X_lon <- lat and lon of urban core locations
# X_air_lat, X_air_lon <- location of city's airport
# up_pathX, no_pathX <- path to all urban and non-urban training data
# output -> urban signature calculated as UP(city) - noUP(airport) for each day in WRF training dataset

from glob import glob
import numpy as np
import metpy.calc
from metpy.units import units
import wrf
import xarray as xr

### Time zone to correct WRF to (this sets the number of files to "ignore" at the beginning of the file list)
utc = 5 # for eastern standard time (UTC-5) ignore the first 5 files 

# path to write out to
ott_out_path = 'output_path\\'
# urban core location
ott_lat, ott_lon = 45.42,-75.69
# airport location
ott_air_lat, ott_air_lon = 45.32,-75.67

var_order = ['GHI','RH','WSP','WDIR','TCC','TEMP','PRES','SNOWH','RAIN'] # output file variable order

# Path to training and testing files
up_path1 = r'urban_files_path\\'
no_path1 = r'nonurban_files_path\\'
up_files1 = sorted(glob(up_path1 + 'wrfout*'))
no_files1 = sorted(glob(no_path1 + 'wrfout*'))

up_files = [up_files1]
no_files = [no_files1]

#### Get the index for urban core locations in urban training data
with xr.open_dataset(up_files1[0]) as test_data:
    lons = test_data.variables['XLONG'].values[0]
    lats = test_data.variables['XLAT'].values[0]
    ott_sn_index, ott_ew_index = np.unravel_index(np.argmin((ott_lon-lons)**2+(ott_lat-lats)**2),lons.shape) # Get closest grid to urban location
    print(lons[ott_sn_index,ott_ew_index],lats[ott_sn_index,ott_ew_index])
    all_vars_list = list(test_data.variables) # Get a list of all variables 
test_data.close()
del test_data

### Get the index for airport locations for non-urban training data
with xr.open_dataset(no_files1[0]) as test_data:
    lons = test_data.variables['XLONG'].values[0]
    lats = test_data.variables['XLAT'].values[0]
    ott_air_sn_index, ott_air_ew_index = np.unravel_index(np.argmin((ott_air_lon-lons)**2+(ott_air_lat-lats)**2),lons.shape)
    print(lons[ott_air_sn_index,ott_air_ew_index],lats[ott_air_sn_index,ott_air_ew_index])
    all_vars_list = list(test_data.variables) # Get a list of all variables 
test_data.close()
del test_data

for up_months,noup_months in zip(up_files,no_files):
    # Initialize list to store all total precipitation data (needed to de-cumulate at specific times)
    up_prec_series = []
    noup_prec_series = []
    a = up_months[utc+24:-1-(24-utc)] 
    b = noup_months[utc+24:-1-(24-utc)] 
    for i in range(0,len(a),24): 
        file = a[i] 
        file2 = b[i]
        # Check to see if files are correct
        if file.split('\\')[-1] != file2.split('\\')[-1]:
            print("Files do not match!")
            break
        date = file.split('\\')[-1].split('_')[2] 
        print("Calculate US for {}".format(date))
        
        ### Get the time series data for urban location WITH urban parameters ###
        up_data = xr.open_mfdataset(a[i:i+24],concat_dim='Time',combine='nested',data_vars="minimal")
        
        # Calculate TCC 
        up_qv = up_data.variables['QVAPOR'].values
        up_p = up_data.variables['P'].values
        up_pb = up_data.variables['PB'].values
        up_t = up_data.variables['T'].values
        # Calculate total cloud cover
        up_total_pres = up_p+up_pb # Calculate total pressure [Pa]
        up_total_t = (up_t+300)  * ((up_total_pres/100)/1000)**(2/7) # Calculate total temperature [K]
        up_eta_rh = wrf.to_np(wrf.rh(up_qv,up_total_pres,up_total_t)) # Calculate relative humidity [%]
        up_cldfra = wrf.cloudfrac(up_total_pres,up_eta_rh,0,97000,80000,45000,meta=False) 
        # Calculate mean cloud fraction [0-1]
        up_tcc_mean = np.clip(np.array(np.ma.mean(up_cldfra,axis=0)), a_min=0, a_max=1) # Calculate the mean
        
        up_swdown = up_data.variables['SWDOWN'].values
        up_rainc = up_data.variables['RAINC'].values
        up_rainnc = up_data.variables['RAINNC'].values
        up_sr = up_data.variables['SR'].values
        up_temp = up_data.variables['T2'].values
        up_pres = up_data.variables['PSFC'].values
        up_snowh= up_data.variables['SNOWH'].values
        up_spec = up_data.variables['Q2'].values
        
        # Calculate relative humidity [%]
        up_rh = metpy.calc.relative_humidity_from_specific_humidity(up_pres*units("Pa"),up_temp*units("K"),up_spec) * 100
        
        up_u10 = up_data.variables['U10'].values
        up_v10 = up_data.variables['V10'].values
        up_cos = up_data.variables['COSALPHA'].values
        up_sin = up_data.variables['SINALPHA'].values
        # Calculate corrected wind speed and direction - earth relative
        up_cor_u10 = up_u10*up_cos - up_v10*up_sin
        up_cor_v10 = up_v10*up_cos + up_u10*up_sin
        up_wsp = np.sqrt(up_cor_u10**2 + up_cor_v10**2)
        up_wdir = np.mod(180+np.rad2deg(np.arctan2(up_cor_u10, up_cor_v10)),360)
        
        # Calculate rainfall
        up_total_prec = up_rainc + up_rainnc
        up_prec_series.append(up_total_prec) # Save precpitation time series 
        if len(up_prec_series) == 1:
            up_prec = np.insert(np.diff(up_total_prec, axis=0), 0, 0, axis=0) # de-accumulate total precipitation and add 0 at beginning
        else: 
            up_prec = np.diff(np.concatenate(up_prec_series,axis=0), axis=0)[-24:] # get only the latest 24 hours in the series after de-accumulating
        up_rain = np.where(up_sr<=0.5, up_prec, 0) # Calculate where rain occurs
        
        up_data.close() # Close up_data file
        
        ### Get the time series data for airport location NO urban parameters ###
        noup_data = xr.open_mfdataset(b[i:i+24],concat_dim='Time',combine='nested',data_vars="minimal")
        
        # Calculate TCC before selecting single location (cloudfrac() function needs 3D data)
        noup_qv = noup_data.variables['QVAPOR'].values
        noup_p = noup_data.variables['P'].values
        noup_pb = noup_data.variables['PB'].values
        noup_t = noup_data.variables['T'].values
        # Calculate total cloud cover
        noup_total_pres = noup_p+noup_pb # Calculate total pressure [Pa]
        noup_total_t = (noup_t+300)  * ((noup_total_pres/100)/1000)**(2/7) # Calculate total temperature [K]
        noup_eta_rh = wrf.to_np(wrf.rh(noup_qv,noup_total_pres,noup_total_t)) # Calculate relative humidity [%]
        noup_cldfra = wrf.cloudfrac(noup_total_pres,noup_eta_rh,0,97000,80000,45000,meta=False) 
        # Calculate mean cloud fraction [0-1]
        noup_tcc_mean = np.clip(np.array(np.ma.mean(noup_cldfra,axis=0)), a_min=0, a_max=1) # Calculate the mean
        
        noup_swdown = noup_data.variables['SWDOWN'].values
        noup_rainc = noup_data.variables['RAINC'].values
        noup_rainnc = noup_data.variables['RAINNC'].values
        noup_sr = noup_data.variables['SR'].values
        noup_temp = noup_data.variables['T2'].values
        noup_pres = noup_data.variables['PSFC'].values
        noup_snowh= noup_data.variables['SNOWH'].values
        noup_spec = noup_data.variables['Q2'].values
        
        # Calculate relative humidity [%]
        noup_rh = metpy.calc.relative_humidity_from_specific_humidity(noup_pres*units("Pa"),noup_temp*units("K"),noup_spec) * 100
        
        noup_u10 = noup_data.variables['U10'].values
        noup_v10 = noup_data.variables['V10'].values
        noup_cos = noup_data.variables['COSALPHA'].values
        noup_sin = noup_data.variables['SINALPHA'].values
        # Calculate corrected wind speed and direction - earth relative
        noup_cor_u10 = noup_u10*noup_cos - noup_v10*noup_sin
        noup_cor_v10 = noup_v10*noup_cos + noup_u10*noup_sin
        noup_wsp = np.sqrt(noup_cor_u10**2 + noup_cor_v10**2)
        noup_wdir = np.mod(180+np.rad2deg(np.arctan2(noup_cor_u10, noup_cor_v10)),360)
        
        # Calculate rainfall
        noup_total_prec = noup_rainc + noup_rainnc
        noup_prec_series.append(noup_total_prec) # Save precpitation time series 
        if len(noup_prec_series) == 1:
            noup_prec = np.insert(np.diff(noup_total_prec, axis=0), 0, 0, axis=0) # de-accumulate total precipitation and add 0 at beginning
        else: 
            noup_prec = np.diff(np.concatenate(noup_prec_series,axis=0), axis=0)[-24:] # get only the latest 24 hours in the series after de-accumulating
        noup_rain = np.where(noup_sr<=0.5, noup_prec, 0) # Calculate where rain occurs
        
        noup_data.close() # close noup_data file
        
        ### Subset the data at the desired grid locations and save them as .npy ###
        # GHI [W/m2] -> [kJ/m2]
        # SNOWH [m] -> [cm]
        us_ghi = np.round(up_swdown[:,ott_sn_index,ott_ew_index] - noup_swdown[:,ott_air_sn_index,ott_air_ew_index], 3) / 3.6 # convert units to kJ/m2
        us_rh = np.round(up_rh[:,ott_sn_index,ott_ew_index] - noup_rh[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_wsp = np.round(up_wsp[:,ott_sn_index,ott_ew_index] - noup_wsp[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_wdir = np.round(up_wdir[:,ott_sn_index,ott_ew_index] - noup_wdir[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_tcc = np.round(up_tcc_mean[:,ott_sn_index,ott_ew_index] - noup_tcc_mean[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_temp = np.round(up_temp[:,ott_sn_index,ott_ew_index] - noup_temp[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_pres = np.round(up_pres[:,ott_sn_index,ott_ew_index] - noup_pres[:,ott_air_sn_index,ott_air_ew_index], 3)
        us_snowh = np.round(up_snowh[:,ott_sn_index,ott_ew_index] - noup_snowh[:,ott_air_sn_index,ott_air_ew_index], 3) / 10 # convert units to cm
        us_rain = np.round(up_rain[:,ott_sn_index,ott_ew_index] - noup_rain[:,ott_air_sn_index,ott_air_ew_index], 3)
        
        all_us = np.array([us_ghi,us_rh,us_wsp,us_wdir,us_tcc,us_temp,us_pres,us_snowh,us_rain]).swapaxes(0,1)
        # Writes an array of of the urban signatures for 24hours of each day
        np.save(ott_out_path+'{}_urban_signature.npy'.format(date),all_us) ### The order of this array is important