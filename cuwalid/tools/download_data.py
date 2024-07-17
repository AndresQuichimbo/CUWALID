import os
from urllib.request import urlretrieve

download_urls = {
  "stopet_parameters.nc": "https://figshare.com/ndownloader/files/34923690",
  "monthly_cont_percentage.nc": "https://figshare.com/ndownloader/files/34923684"
}

# Construct the data directory path relative to the script location
script_dir = os.path.dirname(__file__)
data_dir = os.path.join(script_dir, '..', 'stopet', 'stopet_parameters')

def download_file(url, target_path, filename):
  """Downloads a file from a URL and saves it to the target path."""
  os.makedirs(data_dir, exist_ok=True)  # Create directory structure if it doesn't exist
  print(f'Downloading {filename}')
  urlretrieve(url, target_path)
  print(f"Downloaded {url} to {target_path}")

def main():
  """Main function to be executed when the script is run from the command line."""
  for filename, url in download_urls.items():
    target_path = os.path.join(data_dir, filename)
    download_file(url, target_path, filename)

if __name__ == "__main__":
  main()