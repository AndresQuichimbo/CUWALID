import os
import sys
from urllib.request import urlretrieve
from tqdm import tqdm

stopet_download_urls = {
    "stopet_parameters.nc": "https://figshare.com/ndownloader/files/34923690",
    "monthly_cont_percentage.nc": "https://figshare.com/ndownloader/files/34923684",
    "dpetdt.nc": "https://figshare.com/ndownloader/files/34923663",
    "hpet_slope.nc": "https://figshare.com/ndownloader/files/34923720",
    "meanshift_had.nc": "https://figshare.com/ndownloader/files/49400419",
    "stdshift_had.nc": "https://figshare.com/ndownloader/files/49400425"
}

osm_download_urls = {
    "eritrea.osm.pbf": "https://download.geofabrik.de/africa/eritrea-latest.osm.pbf",
    "djibouti.osm.pbf": "https://download.geofabrik.de/africa/djibouti-latest.osm.pbf",
    "ethiopia.osm.pbf": "https://download.geofabrik.de/africa/ethiopia-latest.osm.pbf",
    "somalia.osm.pbf": "https://download.geofabrik.de/africa/somalia-latest.osm.pbf",
    "kenya.osm.pbf": "https://download.geofabrik.de/africa/kenya-latest.osm.pbf"
}

# Construct the data directory path relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
stopet_data_dir = os.path.join(script_dir, '..', 'stopet', 'stopet_parameters')
osm_data_dir = os.path.join(script_dir, '..', 'forecasting', 'osm_data')

class DownloadProgressBar(tqdm):
    def update_to(self, blocks_transferred=1, block_size=1, total_size=None):
        if total_size is not None:
            self.total = total_size
        self.update(blocks_transferred * block_size - self.n)

def download_file(url, target_path, filename):
    """Downloads a file from a URL and saves it to the target path with a progress bar."""

    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=filename) as t:
        urlretrieve(url, target_path, reporthook=t.update_to)

def download_stopet():
    """Download StopET data."""
    os.makedirs(stopet_data_dir, exist_ok=True)  # Create directory structure if it doesn't exist
    for filename, url in stopet_download_urls.items():
        target_path = os.path.join(stopet_data_dir, filename)
        download_file(url, target_path, filename)

def download_osm():
    """Download OSM data."""
    os.makedirs(osm_data_dir, exist_ok=True)  # Create directory structure if it doesn't exist
    for filename, url in osm_download_urls.items():
        target_path = os.path.join(osm_data_dir, filename)
        download_file(url, target_path, filename)

def download_data(option=None):
    """Handle downloads based on the specified option."""
    if option is None:
        print("No option provided. Downloading both StopET and OSM data...")
        download_stopet()
        download_osm()
    elif option == "--help":
        print("Usage:")
        print("  python -m cuwalid.tools.download_data [option]")
        print("Options:")
        print("  stopet   Download only StopET data")
        print("  osm      Download only OSM data")
        print("  (no option) Download both datasets")
    elif option == "stopet":
        print("Downloading StopET data...")
        download_stopet()
    elif option == "osm":
        print("Downloading OSM data...")
        download_osm()
    else:
        print(f"Unknown option: {option}")
        print("Use --help to see available options.")

def check_files_exist():
    """Check if all required files exist for StopET and OSM data."""
    stopet_downloaded = all(
        os.path.exists(os.path.join(stopet_data_dir, filename))
        for filename in stopet_download_urls.keys()
    )
    
    osm_downloaded = all(
        os.path.exists(os.path.join(osm_data_dir, filename))
        for filename in osm_download_urls.keys()
    )
    
    return [stopet_downloaded, osm_downloaded]

def check_and_download():
    """Check if required files exist, and download them if they don't."""
    downloaded_status = check_files_exist()

    if not downloaded_status[0]:
        print("StopET files are missing. Downloading StopET data...")
        download_data("stopet")
    else:
        print("All StopET files are present.")

    if not downloaded_status[1]:
        print("OSM files are missing. Downloading OSM data...")
        download_data("osm")
    else:
        print("All OSM files are present.")

if __name__ == "__main__":
    # Parse command-line arguments
    option = sys.argv[1].lower() if len(sys.argv) > 1 else None
    download_data(option)


