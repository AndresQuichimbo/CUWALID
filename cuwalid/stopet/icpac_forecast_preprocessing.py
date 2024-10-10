from netCDF4 import Dataset, num2date
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
from mpl_toolkits.basemap import Basemap, maskoceans
import matplotlib.colors as mcolors
import matplotlib.colors as colors
import os
from PIL import Image, ImageChops
from PIL import ImageDraw, ImageFont

from matplotlib import rcParams
plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 10 


# ================ pre processing ICPAC forecast =============##
def wrapper():
    datapath = '/user/home/fp20123/v2_stopet/icpac_forecast/'
    fin = 'Ens_Tref_1monLead_JJAS2024_Raw.nc'
    fout = 'ICPAC_TempF_JJAS2024_HAD.nc'
    icpac_forecast_preprocessing(datapath, fin, fout)
    
    tercileplot('JJAS', 2024)
    
    
def icpac_forecast_preprocessing(datapath, fin, fout):
  """
  This function is used to modify the ICPAC forecast data to fit to the STOPET 
  model domain. But if someone need to use this please change the lat and lon values
  so you can extract the exact location you need from the forecast as it inclued the 
  whole IGAD region.
  
  In the second step it also invert the latitude as ICPAC normally provide values of latitude
  from negative to positive and STOPET nedd it from positive to negative.
  
  :param datapath: is the pathe where you put your ICPAC forecast files
  :param fin is the ICPAC forcast file (.nc)
  :param fout is the final file nae of the modified ICPAC forecast.
  """
  # split the fin from the extension
  name, extension = os.path.splitext(fin)
  # step 1 invert lat
  fin = datapath + fin
  fout_inv = datapath + name + '_inv.nc'
  command = 'cdo invertlat %s %s'%(fin, fout_inv)
  os.system(command)  
  
  # step 2 slice data to fit existing stoPET
  fout = datapath + fout
  command = 'cdo sellonlatbox,31.1,51.92,-6.82,15.9 %s %s' % (fout_inv, fout)
  os.system(command)  

  # step 3 remove intermidiate files
  command = 'rm -rf %s'%(fout_inv)
  os.system(command)  

  
def tercileplot(datapath, season, year, fname, shapefile):
  """
  This function plot the three terciles of ICPAC forecast.
  :param datapath: is the pathe where you put your ICPAC forecast file
  :param season:  is theseason of the forecast (e. g. 'OND')
  :param year: year of the forecast
  :param fname: the file name of the forecast
  :param shapefile: the shpefile you want to use in the plot (This need to be with out the extension .shp)
  :param year: year of the forecast
  """
 
  nc = Dataset(datapath + fname)
  try:
    lats = nc.variables['lat'][:]
    lons = nc.variables['lon'][:]
  except:
    lats = nc.variables['LAT'][:]
    lons = nc.variables['LON'][:]
    
  Adata=nc.variables['above'][:,:]
  title = '%s-%s Above normal (T)'%(season,year)
  label = '-'
  vmin=0
  vmax=100
  fname='temp_Above_%s.png'%season
  trend_plot_defined(Adata, lats, lons, title, label, vmin, vmax, fname, 1, 'a)', shapefile)
  
  Ndata=nc.variables['normal'][:,:]
  title = '%s-%s Near Normal (T)'%(season,year)
  label = '-'
  vmin=0
  vmax=100
  fname='temp_Normal_%s.png'%season
  trend_plot_defined(Ndata, lats, lons, title, label, vmin, vmax, fname, 1, 'b)', shapefile)
  
  Bdata=nc.variables['below'][:,:]
  title = '%s-%s Below normal (T)'%(season,year)
  label = '-'
  vmin=0
  vmax=100
  fname='temp_Below_%s.png'%season
  trend_plot_defined(Bdata, lats, lons, title, label, vmin, vmax, fname, 1, 'c)', shapefile)
  
  # combine image
  combine_all_plots_horizontal_seasonal(datapath , season, year)
 
  # remove intermidiate files
  command = 'rm -rf temp_*.png'
  os.system(command)  
  


def trend_plot_defined(data, lats, lons, title, label, vmin, vmax, fname, creverse, title2, shapefile):
    
    bounds = np.array(np.arange(vmin, vmax, 10))
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=256)

    cmap = plt.get_cmap('RdYlBu_r')##Spectral_r
#    cmap.set_under('silver', 1.0)
    fig = plt.figure(figsize=(6, 6))
    ax=fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(projection='cyl', llcrnrlat=min(lats), urcrnrlat=max(lats), llcrnrlon=min(lons),
                urcrnrlon=max(lons), resolution='h')
    cs4 = plt.imshow(data[:,:], interpolation='nearest', cmap=cmap,
                     extent=[min(lons), max(lons), min(lats), max(lats)],norm=norm)#vmin=vmin,vmax=vmax) 
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    parallels=np.arange(-90.,90.,2.4)
    meridians=np.arange(-180.,180.,2.4)
    m.readshapefile(shapefile,'had_basins', linewidth=1, color='yellow')
    plt.title(title, fontweight='bold')
    plt.title(title2,loc='left', fontweight='bold')
    cb4 = plt.colorbar(cs4, shrink=0.75, pad=0.02, label=label, extend='neither', orientation='horizontal')
    plt.tight_layout()  
    fig.savefig(fname,bbox_inches='tight', dpi=300)
    plt.close()   


def combine_all_plots_horizontal_seasonal(datapath, season, year):
    """
    This function combine all the first horizontally merged figures
    vertically.
    """

    # the saved three plots will be merged vertically
    list_im = [datapath+'temp_Above_%s.png'%season, datapath+'temp_Normal_%s.png'%season, datapath+'temp_Below_%s.png'%season]
    imgs    = [Image.open(i) for i in list_im ]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.hstack([np.asarray(i.resize(min_shape)) for i in imgs])#
    # for a vertical stacking it is simple: use vstack
#    imgs_comb = np.vstack((np.asarray(i.resize(min_shape)) for i in imgs))
    imgs_comb = Image.fromarray(imgs_comb)
    imgs_comb.save(datapath+'Tforecast_%s%s.png'%(season,year))  
    

# *********************************************** #    
if __name__ =='__main__':
    wrapper()
 



  