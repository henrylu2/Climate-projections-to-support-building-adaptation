### Use this to calculate the daily-standardized values of all climate variables
### for bias corrected CanRCM4 data at airport locations 
### output -> Save the standardized output as .npy with dimensions (4073400,17)

# in_path <- folder location for CanRCM4 data
# out_path -> folder location for daily standardized CanRCM4 data

import pandas as pd
from glob import glob
import numpy as np

in_path = "input_path\\"
out_path = "output_path\\"

files = sorted(glob(in_path+'Weatherfile*.csv'))

for f in files:
    print(f)
    f_name = f.split('\\')[-1][:-4]
    d = pd.read_csv(f)
    col_names = d.columns.values
    out_df = d.copy() # make a copy of the dataframe
    
    datas = np.reshape(np.array(d[col_names[6:]]),(-1,24,12)) # Reshape array tp (# days, 24hours, 12 vars)
    datas = np.swapaxes(datas, 0, 1)
    
    # calculate standardized values (day to day)
    a = datas - np.mean(datas,axis=0)
    b = np.std(datas,axis=0)
    norm = np.divide(a,b,out=np.zeros_like(a), where=b!=0)
    
    norm = np.swapaxes(norm, 0 , 1)
    norm = np.reshape(norm, (-1,12))
    
    out_df.loc[:, col_names[6:]] = norm # replaces the climate data columns with standardized values 
    
    out_data = out_df.iloc[:,1:].to_numpy(dtype='float64')
    np.save(out_path+'standardized_{}.npy'.format(f.split('\\')[-1][:-4]),out_data,allow_pickle=False)
