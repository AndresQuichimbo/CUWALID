import geopandas as gpd

# Load the shapefile into a GeoDataFrame
shapefile_path = "cuwalid/forecasting/forecasting_dataset/kenya/kenya-county/ke_county.shp"
gdf = gpd.read_file(shapefile_path)

# View the available columns (titles of attributes stored in the shapefile)
print(gdf.columns)

# Display the first few rows to see what kind of data is stored in each column
print(gdf.head())
