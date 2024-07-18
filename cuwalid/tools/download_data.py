import os
from urllib.request import urlretrieve
from tqdm import tqdm

download_urls = {
    "stopet_parameters.nc": "https://figshare.com/ndownloader/files/34923690",
    "monthly_cont_percentage.nc": "https://figshare.com/ndownloader/files/34923684"
}

# Construct the data directory path relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, '..', 'stopet', 'stopet_parameters')

class DownloadProgressBar(tqdm):
    def update_to(self, blocks_transferred=1, block_size=1, total_size=None):
        if total_size is not None:
            self.total = total_size
        self.update(blocks_transferred * block_size - self.n)

def download_file(url, target_path, filename):
    """Downloads a file from a URL and saves it to the target path with a progress bar."""
    os.makedirs(data_dir, exist_ok=True)  # Create directory structure if it doesn't exist
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=filename) as t:
        urlretrieve(url, target_path, reporthook=t.update_to)

def main():
    """Main function to be executed when the script is run from the command line."""
    for filename, url in download_urls.items():
        target_path = os.path.join(data_dir, filename)
        download_file(url, target_path, filename)

if __name__ == "__main__":
    main()
