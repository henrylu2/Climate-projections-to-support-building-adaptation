This repository contains a version of the scripts used to generate projected climate data for building simulations. Each file is meant to be run on its own and sequentially, given the appropriately formatted inputs. 
The general steps for generating statistically-dynamically downscaled climate data are as summarized:
1. Standardize the WRF dataset; for the entire WRF domain, standardize each variable 
    * calculate_standardized_wrf.py 
2.	Standardize the CanRCM4 datasets that will be downscaled 
    * calculate_standardized_weatherfiles.py
3.	Extract the standardized WRF data at the airport locations
    * get_airport_data_from_wrf.py
4.	Compare standardized days between WRF training dataset and CanRCM4 data, and save a list of matching pair days 
    * calculate_analogue_day_airport.py
5.	Calculate the urban signature at the “urbanized” location with respect to the corresponding city airport
    * calculate_urban_signature_single_loc.py
6.	Calibrate the CanRCM4 data with the urban signature calculated in previous steps for each matching day pair
    * calibrate_canrcm.py 
7.	Perform solar split on global horizontal irradiance
    * solar_split_main.R
    * solar_split_function_bank.R
