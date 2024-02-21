# USE THIS TO PERFORM SOLAR SPLIT MODEL ON DOWNSCALED CANRCM4 DATA
# setwd <- path to working directory 
# stn_info <- file with the weather station information
# in_path <- path to downscaled + bias corrected canrcm4 data
# out_path -> path to write out solar split data 

library(lubridate)
library(dplyr)

# set working directory
setwd("K:/Codes to calibrate airport locations/")

# import necessary solar split functions
source("jg_solar_split_function_bank.R")

# import monthly 2010 t_link table
stn_info=read.csv("jg_t_linke_2010_CWEEDS_2020_stns_all.csv")

# get list of all files that need to be solar split
city = "lav"
in_path = "input_path/"
all_files = list.files(in_path)

# output path 
out_path = "output_path/"

# desired columns in final dataframe in the corrected order
desired_order = c('RUN','YEAR','MONTH','DAY','HOUR','YDAY',
                 "DRI_kjperm2","DHI_kjperm2","DNI_kjperm2",'rsds_kjperm2',
                 'clt_per','rain_mm','wdr_deg','wsp_mpers',
                 'hurs_per','tas_degc','ps_pa','snowc_yes1no0','snd_cm') # list of variables to check in dataframe
final_col_names = c('RUN','YEAR','MONTH','DAY','HOUR','YDAY',
                       "DRI_kJperm2_f100","DHI_kJperm2_f100","DNI_kJperm2_f100","GHI_kJperm2_f100",
                       "TCC_Percent_f100","RAIN_Mm_f100","WDIR_ClockwiseDegFromNorth_f100","WSP_MPerSec_f100",
                       "RHUM_Percent_f100","TEMP_K_f100","ATMPR_Pa_f100","SNOWC_Yes1No0","SNWD_Cm_f100") # final name and order of columns to write out
exclude_columns = c('RUN','YEAR','MONTH','DAY','HOUR','YDAY',"SNOWC_Yes1No0") # list of columns to exclude to make f100 units

# correct each file
for (file in all_files) {
  print(file)
  # Get the station ID to extract location data
  a = strsplit(file, "_")
  b = tail(a[[1]],1)
  station_id = substr(b,0,7)
  # Extract station static data
  stn = stn_info[which(stn_info$climate_ID==station_id),] 
  
  # read downscaled canrcm data
  data = read.csv(paste0(in_path,file))
  sol_step = sol_split_orgill_turb(data_var=data,
                                   stn_info=stn,
                                   t_linke_info=as.numeric(stn[,(ncol(stn_info)-11):ncol(stn_info)]))
  
  sol_step = sol_step[,which(colnames(sol_step) %in% desired_order)] # subset columns 
  sol_step = sol_step[, desired_order] # reorder columns to desired order
  colnames(sol_step) = final_col_names # rename columns in the correct desired order
  
  print("Saving data frame!")
  final_df = sol_step %>% 
    mutate(across(-all_of(exclude_columns), ~ . * 100))
  write.csv(final_df,paste0(out_path,file),row.names = FALSE)
}