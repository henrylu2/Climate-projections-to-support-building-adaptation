##### Use this to calculate the standardized daily variable for all summer months (urban set-up)
# utc <- time zone correction for airport location
# out_path -> path to folder where daily standardized files are saved
# in_path <- path where WRF noUP simulations are located

from glob import glob
from netCDF4 import Dataset
import numpy as np
import metpy.calc
from metpy.units import units
from wrf import (to_np, getvar, g_uvmet, rh, cloudfrac)

### Time zone to correct WRF to 
utc = 5 # for eastern standard time (UTC-5)

# Get list of testing and training files
out_path = "output_path\\"

# Path to files
in_path = "input_path\\"
files = sorted(glob(in_path + 'wrfout*'))

# This function standardizes the data and saves it (over a day, 24hrs)
# files <- a list of files from a single scenario
# .npy file -> (9, 24, 363, 390) a numpy array of the standardized data for each day for the whole domain
#              the order that the variables are saved is important
def standardize_wrf(files):
    new_all_files = files[utc+24:-1-(24-utc)] # correct for time zone
    # Get the dates strings
    days = new_all_files[0::24] 
    dates = [x.split('_')[4] for x in days]

    # Initialize arrays for storing hourly testing data for whole day 
    day_test_swdown = []
    day_test_rain = []
    day_test_wsp = []
    day_test_wdir = []
    day_test_tcc = []
    day_test_temp = []
    day_test_pres = []
    day_test_snowh = []
    day_test_rh = []
    
    counter = 0
    prev_precip = 999
    # For hourly WRF output read and combine array into 24hrs
    for file1 in new_all_files:
        counter += 1 
        
        name1 = file1.split('\\')[-1]
        print('Standardizing Test Dates: ', name1)
        test_ncfile = Dataset(file1,'r')
        
        # Read testing data
        test_temp = to_np(getvar(test_ncfile,"T2")) * units("K") # [K] 
        test_swdown = to_np(getvar(test_ncfile,"SWDOWN")) # [W m-2]
        test_wsp, test_wdir = to_np(g_uvmet.get_uvmet10_wspd_wdir(test_ncfile)) # [m s-1] [degree from North-CW]
        test_pres = to_np(getvar(test_ncfile,"PSFC")) * units("Pa") # surface pressure [Pa]
        test_snowh = to_np(getvar(test_ncfile,"SNOWH")) # snow height [m]
        
        test_rainc = to_np(getvar(test_ncfile,"RAINC")) # [mm]
        test_rainnc = to_np(getvar(test_ncfile,"RAINNC")) # [mm]
        test_prec = test_rainc + test_rainnc # Calculate total accumulated precipitation [mm]
        test_sr = to_np(getvar(test_ncfile,"SR")) # fraction of frozen precipitation [SR>0.5 means all precip is snowfall]
        
        # Calculate rainfall (this step is needed to decumulate the precipitation)
        try:
            if prev_precip==999: 
                cur_precip = test_prec
                test_rain = np.clip(np.where(test_sr<=0.5, cur_precip, 0), a_min=0, a_max=None)
            else:
                cur_precip = test_prec - prev_precip
                test_rain = np.clip(np.where(test_sr<=0.5, cur_precip, 0), a_min=0, a_max=None)
        except:
            cur_precip = test_prec - prev_precip
            test_rain = np.clip(np.where(test_sr<=0.5, cur_precip, 0), a_min=0, a_max=None)
        prev_precip = test_prec
        
        # Calculate relative humidity [%] 
        test_spec = getvar(test_ncfile,"Q2")
        test_rh = metpy.calc.relative_humidity_from_specific_humidity(test_pres,test_temp,test_spec) * 100
        test_rh = np.clip(test_rh, a_min=0, a_max =100)
        
        # Calculate cloud fraction (based on pressure level) [0-1] * 100%
        # Define as: 97000 Pa <= low_cloud < 80000 Pa <= mid_cloud < 45000 Pa <= high_cloud
        test_qv = to_np(getvar(test_ncfile,"QVAPOR"))
        test_p = to_np(getvar(test_ncfile,"P"))
        test_pb = to_np(getvar(test_ncfile,"PB"))
        test_t = to_np(getvar(test_ncfile,"T"))
        
        test_pressure = test_p+test_pb
        test_total_t = (test_t+300)  * ((test_pressure/100)/1000)**(2/7)
        test_eta_rh = rh(test_qv,test_pressure,test_total_t)
        test_cld = cloudfrac(test_pressure,test_eta_rh,0,97000,80000,45000,meta=False)
        test_cld = np.ma.mean(test_cld,axis=0) # Calculate the mean of three levels
        test_tcc = np.clip(np.array(test_cld), a_min=0, a_max=1)
        
        day_test_temp.append(test_temp)
        day_test_swdown.append(test_swdown)
        day_test_rain.append(test_rain)
        day_test_wsp.append(test_wsp)
        day_test_wdir.append(test_wdir)
        day_test_tcc.append(test_tcc)
        day_test_pres.append(test_pres)
        day_test_snowh.append(test_snowh)
        day_test_rh.append(test_rh)
        test_ncfile.close()
        del test_ncfile
    
        if counter>=24 and counter%24 == 0:
            cur_date = dates[counter//24-1]
            print("Writing day file: {}".format(cur_date))
                
            temps = np.array(day_test_temp)
            swdowns = np.array(day_test_swdown)
            rains = np.array(day_test_rain)
            wsps = np.array(day_test_wsp)
            wdirs = np.array(day_test_wdir)
            press = np.array(day_test_pres)
            tccs = np.array(day_test_tcc)
            rhs = np.array(day_test_rh)
            snowhs = np.array(day_test_snowh)
            
            # Standardize the variables for each day (24 hour period)
            # Results in a (aa,xx,yy) shaped array, where aa is the number of days in the series 
            norm_test_temp = (temps - np.mean(temps,axis=0)) / np.std(temps,axis=0)
            norm_test_swdown = (swdowns - np.mean(swdowns,axis=0)) / np.std(swdowns,axis=0)
    
            a = rains - np.mean(rains,axis=0)
            b = np.std(rains,axis=0)
            norm_test_rain = np.divide(a,b,out=np.zeros_like(a), where=b!=0)
    
            norm_test_wsp = (wsps - np.mean(wsps,axis=0)) / np.std(wsps,axis=0)
            norm_test_wdir = (wdirs - np.mean(wdirs,axis=0)) / np.std(wdirs,axis=0)
            norm_test_pres = (press - np.mean(press,axis=0)) / np.std(press,axis=0)
                
            a = tccs - np.mean(tccs,axis=0)
            b = np.std(tccs,axis=0)
            norm_test_tcc = np.divide(a,b,out=np.zeros_like(a), where=b!=0)
    
            a = rhs- np.mean(rhs,axis=0)
            b = np.std(rhs,axis=0)
            norm_test_rh = np.divide(a,b,out=np.zeros_like(a), where=b!=0)
    
            a = snowhs - np.mean(snowhs,axis=0)
            b = np.std(snowhs,axis=0)
            norm_test_snowh = np.divide(a,b,out=np.zeros_like(a),where=b!=0)
    
            # Save the standardized value for future use
            all_data = np.stack((np.array(norm_test_temp), np.array(norm_test_swdown),
                                 np.array(norm_test_rain), np.array(norm_test_wsp),
                                 np.array(norm_test_wdir), np.array(norm_test_tcc),
                                 np.array(norm_test_pres), np.array(norm_test_rh),
                                 np.array(norm_test_snowh)))
            np.save(out_path+"{}_standardized_vars.npy".format(cur_date), all_data)
            
            # Re-initialize arrays for storing hourly testing data for whole day 
            # Resets the stored data for the next day of data
            day_test_swdown = []
            day_test_rain = []
            day_test_wsp = []
            day_test_wdir = []
            day_test_tcc = []
            day_test_temp = []
            day_test_pres = []
            day_test_snowh = []
            day_test_rh = []
    return 0

if __name__ == "__main__":
    standardize_wrf(files)