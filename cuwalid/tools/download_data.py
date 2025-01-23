import os
from urllib.request import urlretrieve
from tqdm import tqdm

# URLs for StopET data
stopet_download_urls = {
    "stopet_parameters.nc": "https://figshare.com/ndownloader/files/34923690",
    "monthly_cont_percentage.nc": "https://figshare.com/ndownloader/files/34923684",
    "dpetdt.nc": "https://figshare.com/ndownloader/files/34923663",
    "hpet_slope.nc": "https://figshare.com/ndownloader/files/34923720",
    "meanshift_had.nc": "https://figshare.com/ndownloader/files/49400419",
    "stdshift_had.nc": "https://figshare.com/ndownloader/files/49400425"
}

# Directory for StopET data
script_dir = os.path.dirname(os.path.abspath(__file__))
stopet_data_dir = os.path.join(script_dir, '..', 'stopet', 'stopet_parameters')

class DownloadProgressBar(tqdm):
    def update_to(self, blocks_transferred=1, block_size=1, total_size=None):
        if total_size is not None:
            self.total = total_size
        self.update(blocks_transferred * block_size - self.n)

def download_file(url, target_path, filename):
    """Download a file with a progress bar."""
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=filename) as t:
        urlretrieve(url, target_path, reporthook=t.update_to)

def download_stopet():
    """Download StopET data, replacing any missing files."""
    os.makedirs(stopet_data_dir, exist_ok=True)
    for filename, url in stopet_download_urls.items():
        target_path = os.path.join(stopet_data_dir, filename)
        if not os.path.exists(target_path):
            print(f"Downloading {filename}...")
            download_file(url, target_path, filename)
        else:
            print(f"{filename} already exists. Skipping.")

if __name__ == "__main__":
    download_stopet()
