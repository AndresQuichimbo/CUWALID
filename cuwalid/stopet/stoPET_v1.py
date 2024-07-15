# Import reqired modules
from netCDF4 import Dataset
import numpy as np
import os
import sys
import datetime as dt
from scipy import stats

## ----------------------------------------------------------##
## Single point stoPET 
## ----------------------------------------------------------##
def stoPET_wrapper_singlepoint(startyear, endyear, latval, lonval, locname,ens_num,
                               datapath, outputpath, tempAdj, deltat, udpi_pet):
    print('stoPET running ...')

    data=Dataset(datapath+'stopet_parameters.nc') 
    ##print(data_uob.variables)
    lats=data.variables['latitude'][:]
    lons=data.variables['longitude'][:]
   
    ampl=data.variables['amplitude'][:,:,:]
    omega=data.variables['omega'][:,:,:]
    phase=data.variables['phase'][:,:,:]
    shift=data.variables['shift'][:,:,:]
    sr=data.variables['sunrise'][:,:,:]
    ss=data.variables['sunset'][:,:,:]
    skew=data.variables['a_estimate'][:,:,:]
    loc=data.variables['loc_estimate'][:,:,:]
    scale=data.variables['scale_estimate'][:,:,:]

    # deltaT parameters
    if tempAdj == 1: # method 1: user defined percentage increase
        # for the single point user provide the percentage with which to increase the annual PET
        # to mainain the array dimentions in the code we replicate these values
        # to the same dimentinon as the rest of the input data
        slope_vals=np.ones((ampl.shape[1],ampl.shape[2])) * udpi_pet

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]
        
    elif tempAdj == 2: # method 2: user defined temperature increase (the hPET data dpetdt.nc)
        deltat_slope=Dataset(datapath+'hpet_slope.nc') 
        slope_vals = deltat_slope.variables['slope'][:,:]

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]

    elif tempAdj == 3: # method 3: progressive change based on hPET trend 
        deltat_slope=Dataset(datapath+'hpet_slope.nc') 
        slope_vals = deltat_slope.variables['slope'][:,:]

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]
   
    else:
        raise ValueError('tempAdj only takes values 1,2,3 ... please check!')
    # monthly contribution percentage
    mpercent=Dataset(datapath+'monthly_cont_percentage.nc') 
    mcont_vals = mpercent.variables['mcontper'][:,:,:]

    # Run the stoPET generation
    stopet = future_pet_ts_generate_singlepoint(startyear, endyear, latval, lonval, lats, lons, locname,
                                                ampl, omega, phase, shift, sr, ss, skew, loc, scale,
                                                slope_vals, mcont_vals, ens_num, datapath, outputpath,
                                                tempAdj, deltat, dpetdt)

    print('stoPET finished successfully.')

    return None


def future_pet_ts_generate_singlepoint(startyear, endyear, latval, lonval, lats, lons, locname,
                                       ampl, omega, phase, shift, sr, ss, skew, loc, scale,
                                       slope_vals, mcont_vals,ens_num, datapath, outputpath,
                                       tempAdj,deltat, dpetdt):
    # create a folder to save the data
    if not os.path.isdir(outputpath+locname+'_E'+str(ens_num)+'_StoPET/'):
        os.mkdir(outputpath+locname+'_E'+str(ens_num)+'_StoPET/')

    # generate the hourly time series period
    years = np.arange(startyear,endyear+1)

    # generate the stochastic pet values
    latind, lonind = nearest_point(latval, lonval, lats, lons)
    
    for i in range(0,len(years)):
        # put the early values here first
        stoch_pet = []
        annual_pet = []
        yr = years[i]
       
        if yr%4 == 0 and (yr % 100 != 0 or yr % 400 == 0):
            m = [31,29,31,30,31,30,31,31,30,31,30,31]
               
        else:
            m = [31,28,31,30,31,30,31,31,30,31,30,31]

        add = 1
        for month in range(1,13):
            # read the sine function parameters
            A = ampl[month-1,latind,lonind]
            w = omega[month-1,latind,lonind]
            p = phase[month-1,latind,lonind]
            c = shift[month-1,latind,lonind]
            sunrise = sr[month-1,latind,lonind]
            sunset = ss[month-1,latind,lonind]
            a_estimate = skew[month-1,latind,lonind]
            loc_estimate = loc[month-1,latind,lonind]
            scale_estimate = scale[month-1,latind,lonind]
            # estimate the pet values from sine function
            t = np.linspace(0,24,24)
            res0 = A * np.sin(w*t + p) + c
            res0 = np.hstack([np.zeros(int(sunrise)),res0[:int(sunset-sunrise)+ add],np.zeros(24 - int(sunset) - add)])

            # skewed normal distribution
            noise_all = stats.skewnorm(a_estimate, loc_estimate, scale_estimate).rvs(m[month-1])
            
            # randoumly preterb the data to generate month lenght value
            for i in range(0,m[month-1]):
                # generate a random value for each day
                # minumum and maximum are seleced from the peak hour value of the ratio 
                noise = noise_all[i]      #np.random.uniform(mi, mx)                
                spet = noise * res0  
                spet = np.hstack([np.zeros(int(sunrise)),spet[int(sunrise):int(sunset) + add],np.zeros(24 - int(sunset) - add)])
                spet = np.where(spet<0, 0, spet) # remove negative values
                # Here we save the stochastic pet generated in two arrays
                # the first one is to save the stopet values with outn no adjustment
                # the second one is the same values to be adjusted latter down in the model.
                # this is ucessary to have two values one with and without change in temperature
                # so that if user wants to compare the two values the stocastically generated
                # pet values are generated from similar seeds.
                stoch_pet = np.append(stoch_pet, spet) # append the stopet with out adjustment
                annual_pet = np.append(annual_pet, spet) # append stopet for later adjustment

        # save each year generated pet timeseries in a text file
        filename1 = outputpath+locname+'_E'+str(ens_num)+'_StoPET/'+str(yr)+'_'+str(latval)+'_'+str(lonval)+'_'+str(tempAdj)+'_stoPET.txt'
        np.savetxt(filename1, stoch_pet, fmt='%0.5f')
        
        # here make the adjustment for change in temperature
        # deltaT parameters
        slope = slope_vals[latind,lonind]

        dpetdt_val = dpetdt[latind,lonind]

        # monthly contribution percentage values
        mcont = mcont_vals[:,latind,lonind]
        # annual PET
        adj_stopet = increase_temp_singlepoint(slope, mcont, annual_pet, tempAdj, deltat, yr, 
                                               startyear, endyear,dpetdt_val)
        # save the adjusted pet timeseries in a text file
        filename2 = outputpath+locname+'_E'+str(ens_num)+'_StoPET/'+str(yr)+'_'+str(latval)+'_'+str(lonval)+'_'+str(tempAdj)+'_AdjstoPET.txt'
        np.savetxt(filename2, adj_stopet, fmt='%0.5f')

        print(yr)
    
    return None


def increase_temp_singlepoint(slope, mcont, annual_pet, tempAdj, deltat, yr, 
                              startyear, endyear,dpetdt_val):
    """
    This function increase the stochastically generated PET accounting
    for the specified temperature increase. The increase is based on
    a linear regression model where the total annual PET is used as a
    independent variable to identify the rte of change for a unit increase of
    temperature. Once the amount of PET increase due to a unit change is identified
    it will be multiplied by the specified change in temperature as the rate of change
    of PET due to temperature is identified to be more or less constant.
    The annual change in PET is then distributed to each month based on the climatological
    percentage contribution of each month. Then the monthly contribution is equally
    divided for the number of days and hours within each month.

    :param: slope: the slope of the linear model
    :param: mcont: the percentage contribution of each month (based on 40 years climatology)
    :param: totalpet: the annual PET generated by stoPET without change in temperature
    :param: deltat: user defined change in the temperature

    :return:  stochatic PET accounted for the change in temperature.

    """
    # number of years and index of the year running
    years = np.arange(startyear, endyear+1)
    ind = np.where(years == yr)
    
    # calculate the annual pet 
    totalpet = np.sum(annual_pet)
    # based on the method used to account for temperature increase
    # the total amount of PET increase per year is calculated here.
    # NOTICE for the first two methods a simple linear model is used
    # however for the thired method the linear model is multiplied
    # by the deltat value. this is because the slope and intercepts are calcualted for
    # a unit increase inteperature so if the temprature increase is below one or above
    # one we needed to adjust for that.
    if tempAdj == 1:
        delta_annual_pet = (totalpet * (slope / 100.))   #((slope*ind)  + intercept) 
        delta_month_pet = (mcont * delta_annual_pet) 

    elif tempAdj == 2:
        delta_annual_pet = dpetdt_val * deltat
        # calculate the monthly changes
        delta_month_pet = (mcont * delta_annual_pet)

    elif tempAdj == 3:
        if ind[0] == 0:
            delta_annual_pet = 0.0
        else:
            delta_annual_pet = slope * ind[0]
        # make the monthly contributions
        delta_month_pet = (mcont * delta_annual_pet)     

    else:
        raise ValueError('tempAdj only takes values 1,2,3 please check!')

    # add each month change in pet equaly for each day and hour.
    # pet is added only for the day time
    # identify the array count for each month
    if yr%4 == 0 and (yr % 100 != 0 or yr % 400 == 0):
        p = [ 744, 1440, 2184, 2904, 3648, 4368, 5112, 5856, 6576, 7320, 8040, 8784]
        m = [31,29,31,30,31,30,31,31,30,31,30,31]
    else:
        p = [ 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
        m = [31,28,31,30,31,30,31,31,30,31,30,31]

    adj_stopet = []
    for i in range(0,len(p)):
        if i == 0:
            start = 0
            end = p[i] 
        else:
            start = p[i-1]
            end = p[i]
        # extract the pet for each month
        x = annual_pet[start:end]
        # estimate the average contribution of each hour
        # to the daily pet
        y = np.reshape(x,(m[i],24)).T
        y_av=np.mean(y,axis=1)
        y_sum = np.sum(y_av)
        # this is the average hourly contribution
        cont = y_av / y_sum
        # repeat this to much the number of days
        cont_all = np.tile(cont,m[i])
        # find the number of hours with above zero pet
        #numhours = np.count_nonzero(x)
        # divide the monthly pet increase to those hours
        delta_hour_pet = delta_month_pet[i] * (cont_all / m[i]) # / numhours
        # add the increase to the day time hours only
        adj_x = x  + delta_hour_pet    # np.where(x > 0., x  + delta_hour_pet, x)
        adj_stopet = np.append(adj_stopet,adj_x)
        
    return adj_stopet

## ----------------------------------------------------------##
## Regional stoPET 
## ----------------------------------------------------------##
def stoPET_wrapper_regional(startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
                            locname, ens_num, datapath, outputpath, tempAdj, deltat, udpi_pet):
    print('stoPET running ...')

    data=Dataset(datapath+'stopet_parameters.nc') #'month_1_params.nc'
    ##print(data_uob.variables)
    lats=data.variables['latitude'][:]
    lons=data.variables['longitude'][:]
   
    ampl=data.variables['amplitude'][:,:,:]
    omega=data.variables['omega'][:,:,:]
    phase=data.variables['phase'][:,:,:]
    shift=data.variables['shift'][:,:,:]
    sr=data.variables['sunrise'][:,:,:]
    ss=data.variables['sunset'][:,:,:]
    skew=data.variables['a_estimate'][:,:,:]
    loc=data.variables['loc_estimate'][:,:,:]
    scale=data.variables['scale_estimate'][:,:,:]

    # deltaT parameters
    if tempAdj == 1: # method 1: user defined percentage increase
        # for the single point user provide only one sope and one intercept
        # to mainain the array dimentions in the code we replicate these values
        # to the same dimentinon as the rest of the input data
        slope_vals=np.ones((ampl.shape[1],ampl.shape[2])) * udpi_pet

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]
        
    elif tempAdj == 2: # method 3: user defined temperature increase 
        deltat_slope=Dataset(datapath+'hpet_slope.nc') 
        slope_vals = deltat_slope.variables['slope'][:,:]

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]

    elif tempAdj == 3: # progressive change based on hPET trend 
        deltat_slope=Dataset(datapath+'hpet_slope.nc') 
        slope_vals = deltat_slope.variables['slope'][:,:]

        dpetbydt=Dataset(datapath+'dpetdt.nc')
        dpetdt = dpetbydt.variables['dpetdt'][:,:]
        
    else:
        raise ValueError('tempAdj only takes values 1,2,3 please check!')
    # monthly contribution percentage
    mpercent=Dataset(datapath+'monthly_cont_percentage.nc') 
    mcont_vals = mpercent.variables['mcontper'][:,:,:]


    stopet = future_pet_ts_generate_regional(startyear, endyear, latval_min,latval_max, lonval_min,lonval_max,
                                             lats, lons, locname, ampl, omega, phase, shift, sr, ss, skew, loc, scale,
                                             slope_vals, mcont_vals,ens_num, datapath, outputpath, tempAdj, deltat, dpetdt)

    print('stoPET finished successfully.')

    return None



def future_pet_ts_generate_regional(startyear, endyear, latval_min,latval_max, lonval_min,lonval_max, lats, lons, locname,
                                    ampl, omega, phase, shift, sr, ss, skew, loc, scale,
                                    slope_vals, mcont_vals,ens_num,datapath, outputpath, tempAdj,deltat, dpetdt):

    # create a folder to save the data
    if not os.path.isdir(outputpath+locname+'_E'+str(ens_num)+'_StoPET/'):
        os.mkdir(outputpath+locname+'_E'+str(ens_num)+'_StoPET/')

    # generate the hourly time series period
    years = np.arange(startyear,endyear+1)

    # generate the stochastic pet values
    latind_min, lonind_min = nearest_point(latval_min, lonval_min, lats, lons)
    latind_max, lonind_max = nearest_point(latval_max, lonval_max, lats, lons)

    latlen = lats[latind_max:latind_min]
    lonlen = lons[lonind_min:lonind_max]
    
    for i in range(0,len(years)):

        stoch_pet = []
        stoch_pet_adj = []

        yr = years[i]
        if yr%4 == 0 and (yr % 100 != 0 or yr % 400 == 0):
            m = [31,29,31,30,31,30,31,31,30,31,30,31]
               
        else:
            m = [31,28,31,30,31,30,31,31,30,31,30,31]

        add = 1
        for month in range(1,13):
            # read the sine function parameters
            A = ampl[month-1,latind_max:latind_min,lonind_min:lonind_max]
            w = omega[month-1,latind_max:latind_min,lonind_min:lonind_max]
            p = phase[month-1,latind_max:latind_min,lonind_min:lonind_max]
            c = shift[month-1,latind_max:latind_min,lonind_min:lonind_max]
            sunrise = sr[month-1,latind_max:latind_min,lonind_min:lonind_max]
            sunset = ss[month-1,latind_max:latind_min,lonind_min:lonind_max]
            a_estimate = skew[month-1,latind_max:latind_min,lonind_min:lonind_max]
            loc_estimate = loc[month-1,latind_max:latind_min,lonind_min:lonind_max]
            scale_estimate = scale[month-1,latind_max:latind_min,lonind_min:lonind_max]
            # estimate the pet values from sine function
            t = np.linspace(0,24,24)
            
            # expand the array to match the shape
            t = np.repeat(t[:,np.newaxis], A.shape[0], axis=1)
            t = np.repeat(t[:,:,np.newaxis], A.shape[1], axis=2)
            # estimate the values of PET from the sine function   
            res0 = A * np.sin(w*t + p) + c
            
            for i in range(A.shape[0]):
                for j in range(A.shape[1]):
                    xx = res0[:, i, j]
                    try:
                        yy = np.hstack([np.zeros(int(sunrise[i,j])),xx[:(int(sunset[i,j]-sunrise[i,j])+ add)],np.zeros(24 - int(sunset[i,j]) - add)])
                        res0[:,i,j] = yy
                    except:
                        pass
      
            #res0 = np.hstack([np.zeros(int(sunrise)),res0[:int(sunset-sunrise)+ add, :, :],np.zeros(24 - int(sunset) - add)])

            # skewed normal distribution
            noise_all = stats.skewnorm(a_estimate, loc_estimate, scale_estimate).rvs((m[month-1],A.shape[0],A.shape[1]))
            
            # randoumly preterb the data to generate month lenght value
            for i in range(0,m[month-1]):
                # generate a random value for each day
                # minumum and maximum are seleced from the peak hour value of the ratio 
                noise = noise_all[i,:,:]
                spet = noise * res0
                
                #spet = np.hstack([np.zeros(int(sunrise)),spet[int(sunrise):int(sunset) + add],np.zeros(24 - int(sunset) - add)])
                spet = np.where(spet<0., 0., spet) # remove negative values
                stoch_pet.append(spet)

        # change the stochastic pet to array
        stoch_pet = np.array(stoch_pet)
        # here make the adjustment for change in temperature
        # deltaT parameters
        slope = slope_vals[latind_max:latind_min,lonind_min:lonind_max]

        dpetdt_val = dpetdt[latind_max:latind_min,lonind_min:lonind_max]

        # monthly contribution percentage values
        mcont = mcont_vals[:,latind_max:latind_min,lonind_min:lonind_max]
        # adjusted pet value for temperture increase
        stoch_pet_adj = increase_temp_regional(slope, mcont, stoch_pet, tempAdj, deltat, yr, startyear, endyear, dpetdt_val)

        # mask ocean values
        stoch_pet=np.where(stoch_pet>1e5,-99.0,stoch_pet)
        stoch_pet_adj=np.where(stoch_pet_adj>1e5,-99.0,stoch_pet_adj)

        # save each year value separately (.nc)
        filename1 = outputpath+locname+'_E'+str(ens_num)+'_StoPET/'+str(yr)+'_'+str(tempAdj)+'_stoPET.nc'
        filename2 = outputpath+locname+'_E'+str(ens_num)+'_StoPET/'+str(yr)+'_'+str(tempAdj)+'_AdjstoPET.nc'
        tunits = 'days since '+str(yr)+'-01-01'       
        nc_write(stoch_pet, latlen, lonlen, 'pet', tunits, filename1)
        nc_write(stoch_pet_adj, latlen, lonlen, 'pet', tunits, filename2)

        # delete the array for next year
        del stoch_pet
        del stoch_pet_adj
        print(yr)

    return None

    
def increase_temp_regional(slope, mcont, stoch_pet, tempAdj, deltat, yr, startyear, endyear, dpetdt_val):
    """
    This function increase the stochastically generated PET accounting
    for the specified temperature increase. The increase is based on
    a linear regression model where the total annual PET is used as a
    independent variable to identify the rte of change for a unit increase of
    temperature. Once the amount of PET increase due to a unit change is identified
    it will be multiplied by the specified change in temperature as the rate of change
    of PET due to temperature is identified to be more or less constant.
    The annual change in PET is then distributed to each month based on the climatological
    percentage contribution of each month. Then the monthly contribution is equally
    divided for the number of days and hours within each month.

    :param: slope: the slope of the linear model
    :param: mcont: the percentage contribution of each month (based on 40 years climatology)
    :param: totalpet: the annual PET generated by stoPET without change in temperature
    :param: deltat: user defined change in the temperature

    :return:  stochatic PET accounted for the change in temperature.

    """
    # number of years and index of the year running
    years = np.arange(startyear, endyear+1)
    ind = np.where(years == yr)
    # calculate the annual pet 
    totalpet = np.nansum(stoch_pet, axis=(0,1))
    # based on the method used to account for temperature increase
    # the total amount of PET increase per year is calculated here.
    # NOTICE for the first two methods a simple linear model is used
    # however for the thired method the linear model is multiplied
    # by the deltat value. this is because the slope and intercepts are calcualted for
    # a unit increase inteperature so if the temprature increase is below one or above
    # one we needed to adjust for that.
    if tempAdj == 1: # linear trend that use the year as independent variable
        delta_annual_pet =  totalpet * (slope / 100.)   
        delta_month_pet = (mcont * delta_annual_pet) 

    elif tempAdj == 2: # use the delta PET/ delta T value for the unit T increase and multiply by given delta T
        delta_annual_pet = dpetdt_val * deltat
        # calculate the monthly changes
        delta_month_pet = (mcont * delta_annual_pet) 

    elif tempAdj == 3:
        # add a new method where we only add the slope trend to existing
        # stoPET keeping the first year the same
        if ind == 0:
            delta_annual_pet = 0.0
        else:
            delta_annual_pet = slope * ind
        # make the monthly contributions
        delta_month_pet = (mcont * delta_annual_pet)
        
    else:
        raise ValueError('tempAdj only takes values 1,2,3 please check!')

    # add each month change in pet equaly for each day and hour.
    # pet is added only for the day time
    # identify the array count for each month 
    if yr%4 == 0 and (yr % 100 != 0 or yr % 400 == 0):
        p = [ 31,  60,  91, 121, 152, 182, 213, 244, 274, 305, 335, 366]
        m = [31,29,31,30,31,30,31,31,30,31,30,31]
    else:
        p = [ 31,  59,  90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
        m = [31,28,31,30,31,30,31,31,30,31,30,31]

    adj_stopet = np.ones((stoch_pet.shape[0],stoch_pet.shape[1],stoch_pet.shape[2],stoch_pet.shape[3]))

    for i in range(0,len(p)):
        if i == 0:
            start = 0
            end = p[i] 
        else:
            start = p[i-1]
            end = p[i]
        # extract the pet for each month
        x = stoch_pet[start:end, :, :,:]
        # make average
        y_av = np.mean(x,axis=0)
        # make sum
        y_sum = np.sum(y_av,axis=0)
        # find cont
        cont = y_av / y_sum
        # repeat the cont
        t = np.repeat(cont[np.newaxis,:,  :, :], m[i], axis=0)
        # find the hourly increase
        delta_hour_pet = t * (delta_month_pet[i,:,:] / m[i])
        adj_x = x  + delta_hour_pet
        # append the adjusted values
        adj_stopet[start:end,:,:,:] = adj_x
        
    return adj_stopet

##-------------- SUPPLENENTARY FUNCTONS ----------------------------------##
def nc_write(data, lat, lon, varname, tunits, filename):
    """
    this function write the PET on a netCDF file.

    :param: data: data to be written (time,lat,lon)
    :param: lat: latitude
    :param: lon: longitude
    :param: varname: name of the variable to be written (e.g. 'pet')
    :param: tunits: time units for the data (e.g. 'days since 1981-01-01')
    :param:filename: the file name to write the values with .nc extension

    :return:  produce a netCDF file in the same directory.
    """
    
    ds = Dataset(filename, mode='w', format='NETCDF4_CLASSIC')

    time = ds.createDimension('time', None)
    latitude = ds.createDimension('latitude', len(lat))
    longitude = ds.createDimension('longitude', len(lon))
    hours = ds.createDimension('hours', 24)
   
    time = ds.createVariable('time', np.float32, ('time',))
    hours = ds.createVariable('hours', np.float32, ('hours',))
    latitude = ds.createVariable('latitude', np.float32, ('latitude',))
    longitude = ds.createVariable('longitude', np.float32, ('longitude',))

    # check if the data is 2d or 3d
    if len(data.shape) == 4: # 4D array
        pet_val = ds.createVariable(varname, 'f4', ('time','hours','latitude','longitude'), zlib=True)
        time.units = tunits  
        time.calendar = 'proleptic_gregorian'
        time[:] = np.arange(data.shape[0])
        hours[:] = np.arange(data.shape[1])
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:,:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'

    elif len(data.shape) == 3: # 3D array
        pet_val = ds.createVariable(varname, 'f4', ('time','latitude','longitude'), zlib=True)
        time.units = tunits  
        time.calendar = 'proleptic_gregorian'
        time[:] = np.arange(data.shape[0])
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'
    
    elif len(data.shape) == 2: # 2D array
        pet_val = ds.createVariable(varname, 'f4', ('latitude','longitude'), zlib=True)
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'

    else:
        raise ValueError('the function can only write a 2D, 3D and 4D array data!')

    ds.close()
    
    return None    


def nearest_point(lat_var, lon_var, lats, lons):
    """
    This function identify the nearest grid location index for a specific lat-lon
    point.
    :param lat_var: the latitude
    :param lon_var: the longitude
    :param lats: all available latitude locations in the data
    :param lons: all available longitude locations in the data
    :return: the lat_index and lon_index
    """
    # this part is to handle if lons are givn 0-360 or -180-180
    if any(lons > 180.0) and (lon_var < 0.0):
        lon_var = lon_var + 360.0
    else:
        lon_var = lon_var
        
    lat = lats
    lon = lons

    if lat.ndim == 2:
        lat = lat[:, 0]
    else:
        pass
    if lon.ndim == 2:
        lon = lon[0, :]
    else:
        pass

    index_a = np.where(lat >= lat_var)[0][-1]
    index_b = np.where(lat <= lat_var)[0][-1]

    if abs(lat[index_a] - lat_var) >= abs(lat[index_b] - lat_var):
        index_lat = index_b
    else:
        index_lat = index_a

    index_a = np.where(lon >= lon_var)[0][0]
    index_b = np.where(lon <= lon_var)[0][0]
    if abs(lon[index_a] - lon_var) >= abs(lon[index_b] - lon_var):
        index_lon = index_b
    else:
        index_lon = index_a

    return index_lat, index_lon

## ------------------ END OF SCRIPT ------------------------------##

