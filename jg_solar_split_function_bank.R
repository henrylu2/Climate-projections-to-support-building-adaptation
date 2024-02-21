# function to get the declination angle
get.dly.soldcl=function(date.no,hour.no)
{
  # equation from Spencer(1971)
  
  # B.val
  B.val=((yday(date.no)-1)*360/365)
  
  # declination angle
  (180/pi)*(0.006918-0.399912*cos(B.val*pi/180)+0.070257*sin(B.val*pi/180)-0.006758*cos(2*B.val*pi/180)+0.000907*sin(2*B.val*pi/180)-0.002697*cos(3*B.val*pi/180)+0.00148*sin(3*B.val*pi/180))
  
}


# function to estimate the hour angle
get.sol.angl=function(date.no,hour.no,lon.val,lat.val,val.LSM)
{
  # B.val
  B.val=((yday(date.no)-1)*360/365)
  
  # equation of time.
  val.ET=229.2*(0.000075+0.001868*cos(B.val*pi/180)-0.032077*sin(B.val*pi/180)-0.014615*cos(2*B.val*pi/180)-0.04089*sin(2*B.val*pi/180))
  
  # time meridians
  #val.LSM=data.frame(region=c("atlantic","eastern","central","mountain","pacific","yukon"),
  #                   val=c(60,75,90,105,120,135))
  
  # AST
  val.AST=hour.no+(val.ET+(4*(val.LSM-abs(lon.val))))/60
  val.time.sol.noon=(val.AST-12)*60
  
  # hour angle.
  val.time.sol.noon*0.25
  
}


# function to estimate solar elevation angle
get.sol.alt=function(date.no,hour.no,lon.val,lat.val,val.LSM)
{
  # get declination angle
  sol.dec.angle=get.dly.soldcl(date.no=date.no,hour.no=hour.no)
  
  # get hour angle
  hour.angle=get.sol.angl(date.no=date.no,hour.no=hour.no,lon.val=lon.val,lat.val=lat.val,val.LSM=val.LSM)
  
  # calculate and return solar altitude angle
  (asin((cos(lat.val*pi/180)*cos(sol.dec.angle*pi/180)*cos(hour.angle*pi/180))+(sin(lat.val*pi/180)*sin(sol.dec.angle*pi/180)))*180)/pi
}


# function to calculate extra-terrestrial radiation given the time
extr_rad=function(time_ser,stn_info)
{
  sol.cons=1367 # solar constant
  
  # correction factors
  B.val=((yday(time_ser)-1)*360)/365
  dist.cor.f=(1.000110+0.034221*cos(B.val*pi/180)+0.001280*sin(B.val*pi/180)+0.000719*cos(2*B.val*pi/180)+0.000077*sin(2*B.val*pi/180))
  
  # horizontal component of eccentricity corrected extra-terrestrial rad.
  elev.angl=elev_angl(time_ser=time_ser,stn_info=stn_info)
  
  sol.cons*dist.cor.f*sin(elev.angl*pi/180)*3.6
  
}


# function to calculate elevation angle
elev_angl=function(time_ser,stn_info)
{
  get.sol.alt(date.no=date(time_ser),
              hour.no=(hour(time_ser)+(minute(time_ser)/60)),  
              lon.val=stn_info$lon,
              lat.val=stn_info$lat,
              val.LSM=abs(stn_info$UTC_offset*15)) # The local standard meridian is calculated by multiplying the time difference between local time and GMT by 15
  
}


# function to perform solar split by Orgill Hollands method

sol_split_orgill=function(data_var,stn_info)
{
  # get xtr
  data_var$elev.angl=elev_angl(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$xtr_kjperm2=extr_rad(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$clr_ind=ifelse(test=data_var$xtr_kjperm2<data_var$rsds_kjperm2,
                          yes=1,
                          no=data_var$rsds_kjperm2/data_var$xtr_kjperm2)
    
  data_var$kd=ifelse(test=data_var$clr_ind>0,
                                       no=0,
                                       yes=ifelse(test=data_var$clr_ind<0.35,
                                                  yes = 1-0.249*data_var$clr_ind,
                                                  no=ifelse(test=data_var$clr_ind<0.75,
                                                            yes=1.557-1.84*data_var$clr_ind,
                                                            no=ifelse(test=data_var$clr_ind>1,
                                                                      yes=NA,
                                                                      no=0.177))))
  data_var$elev.angl[which(data_var$elev.angl<0)]=0
  
  # If DHI<5º, GHI=DHI
  solangthresh=5
  data_var$DHI_kjperm2=ifelse(test=data_var$elev.angl>0,
                              yes=ifelse(test=data_var$elev.angl<solangthresh,
                                         yes=data_var$rsds_kjperm2,
                                         no=data_var$rsds_kjperm2*data_var$kd),
                              no=0)
  
  # Direct Horizontal Irradiance or DRI
  data_var$DRI_kjperm2=ifelse(test=data_var$elev.angl>0,
                              yes=data_var$rsds_kjperm2-data_var$DHI_kjperm2,
                              no=0)
  
  # Direct Normal Irradiance or DNI
  data_var$DNI_kjperm2=ifelse(test=data_var$elev.angl<solangthresh,
                                                yes=0,
                                                no=data_var$DRI_kjperm2/sin(data_var$elev.angl*pi/180))
  
  
  data_var
}



# function to perform solar split by Orgill Hollands+turbidity method

sol_split_orgill_turb=function(data_var,stn_info,t_linke_info)
{
  data_var$t_linke=t_linke_info[month(data_var$time_lst)]
  
  # get xtr
  data_var$elev.angl=elev_angl(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$xtr_kjperm2=extr_rad(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$clr_ind=ifelse(test=data_var$xtr_kjperm2<data_var$rsds_kjperm2,
                          yes=1,
                          no=data_var$rsds_kjperm2/data_var$xtr_kjperm2)
  
  data_var$kd=ifelse(test=data_var$clr_ind>0,
                     no=0,
                     yes=ifelse(test=data_var$clr_ind<0.35,
                                yes = 1-0.249*data_var$clr_ind,
                                no=ifelse(test=data_var$clr_ind<0.75,
                                          yes=1.557-1.84*data_var$clr_ind,
                                          no=ifelse(test=data_var$clr_ind>1,
                                                    yes=NA,
                                                    no=0.177))))
  data_var$elev.angl[which(data_var$elev.angl<0)]=0
  
  
  # Diffused Horizontal Irradiance or DHI
  data_var$DHIuncor_kjperm2=ifelse(test=data_var$elev.angl>0,
                                   yes=data_var$rsds_kjperm2*data_var$kd,
                                   no=0)
  
  # Direct Horizontal Irradiance or DRI
  data_var$DRIuncor_kjperm2=ifelse(test=data_var$elev.angl>0,
                                   yes=data_var$rsds_kjperm2-data_var$DHIuncor_kjperm2,
                                   no=0)
  
  # Direct Normal Irradiance or DNI
  data_var$DNIuncor_kjperm2=ifelse(test=data_var$elev.angl<=0,
                              yes=0,
                              no=data_var$DRIuncor_kjperm2/sin(data_var$elev.angl*pi/180))
  
  
  # Turbidity calculations
  ma_alpha=(exp(-stn_info$elev.m./8434.5))/(sin(data_var$elev.angl*pi/180)+0.50572*((data_var$elev.angl*pi/180+6.07995)^(-1.6364)))
  r_ma=ifelse(test=ma_alpha<=20,
              yes=1/(6.6296+1.7513*ma_alpha-0.1202*ma_alpha^2+0.0065*ma_alpha^3-0.00013*ma_alpha^4),
              no=1/(10.4+0.718*ma_alpha))
  
  
  sol.cons=1367 # solar constant
  data_var$DNIlim_kjperm2=ifelse(test=data_var$DNIuncor_kjperm2==0,
                                 yes=0,
                                 no=sol.cons*3.6*exp(-0.8662*ma_alpha*data_var$t_linke*r_ma))
    
  data_var$DNI_kjperm2=ifelse(test=data_var$DNIuncor_kjperm2>data_var$DNIlim_kjperm2,
                              yes=data_var$DNIlim_kjperm2,
                              no=data_var$DNIuncor_kjperm2)
  
  data_var$DRI_kjperm2=data_var$DNI_kjperm2*sin(data_var$elev.angl*pi/180)
  data_var$DHI_kjperm2=ifelse(test=data_var$elev.angl>0,
                              yes=data_var$rsds_kjperm2-data_var$DRI_kjperm2,
                              no=0)
  
  
  data_var
}





# function to perform solar split by bolands+turbidity method

sol_split_bolands_turb=function(data_var,stn_info,t_linke_info)
{
  
  data_var$t_linke=t_linke_info[month(data_var$time_lst)]
  
  data_var$elev.angl=elev_angl(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$elev.angl[which(data_var$elev.angl<0)]=0
  
  data_var$xtr_kjperm2=extr_rad(time_ser=data_var$time_lst,stn_info=stn_info)
  data_var$clr_ind=ifelse(test=data_var$rsds_kjperm2==0,
                          yes=0,
                          no=ifelse(data_var$xtr_kjperm2<data_var$rsds_kjperm2,
                                    yes=1,
                                    no=data_var$rsds_kjperm2/data_var$xtr_kjperm2))
  
  data_var$ihdperih=1/(1+exp(-5+8.6*data_var$clr_ind))
  
  # Diffused Horizontal Irradiance or DHI
  data_var$DHIuncor_kjperm2=ifelse(test=data_var$elev.angl>0,
                                   yes=data_var$ihdperih*data_var$rsds_kjperm2,
                                   no=0)
  
  # Direct Horizontal Irradiance or DRI
  data_var$DRIuncor_kjperm2=ifelse(test=data_var$elev.angl>0,
                                   yes=data_var$rsds_kjperm2-data_var$DHIuncor_kjperm2,
                                   no=0)
  
  # Direct Normal Irradiance or DNI
  data_var$DNIuncor_kjperm2=ifelse(test=data_var$elev.angl<=0,
                                   yes=0,
                                   no=data_var$DRIuncor_kjperm2/sin(data_var$elev.angl*pi/180))
  
  
  # Turbidity calculations
  ma_alpha=(exp(-stn_info$elev.m./8434.5))/(sin(data_var$elev.angl*pi/180)+0.50572*((data_var$elev.angl*pi/180+6.07995)^(-1.6364)))
  r_ma=ifelse(test=ma_alpha<=20,
              yes=1/(6.6296+1.7513*ma_alpha-0.1202*ma_alpha^2+0.0065*ma_alpha^3-0.00013*ma_alpha^4),
              no=1/(10.4+0.718*ma_alpha))
  
  
  sol.cons=1367 # solar constant
  data_var$DNIlim_kjperm2=ifelse(test=data_var$DNIuncor_kjperm2==0,
                                 yes=0,
                                 no=sol.cons*3.6*exp(-0.8662*ma_alpha*data_var$t_linke*r_ma))
  
  data_var$DNI_kjperm2=ifelse(test=data_var$DNIuncor_kjperm2>data_var$DNIlim_kjperm2,
                              yes=data_var$DNIlim_kjperm2,
                              no=data_var$DNIuncor_kjperm2)
  
  data_var$DRI_kjperm2=data_var$DNI_kjperm2*sin(data_var$elev.angl*pi/180)
  data_var$DHI_kjperm2=ifelse(test=data_var$elev.angl>0,
                              yes=data_var$rsds_kjperm2-data_var$DRI_kjperm2,
                              no=0)
  
  
  data_var
}
