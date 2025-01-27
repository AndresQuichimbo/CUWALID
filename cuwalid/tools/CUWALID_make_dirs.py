import os


def create_directory_structure(base_dir, season_name, year):
    # Define the full directory structure
    directories = [
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'output'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'postpp'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'postpp', "csv"),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'postpp', "netcdf"),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'postpp', 'fig'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'raster'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'model'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'dataset', 'pre'),
        os.path.join(base_dir, 'forecast/regional', f'{season_name}_{year}', 'dataset', 'pet'),

        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'output'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'postpp'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'postpp', "csv"),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'postpp', "netcdf"),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'postpp', 'fig'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'raster'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'model'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'dataset', 'pre'),
        os.path.join(base_dir, 'historical/regional', f'{season_name}_{year}', 'dataset', 'pet'),
    ]
    
    # Create each directory if it doesn't exist
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
