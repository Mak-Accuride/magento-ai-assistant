import pandas as pd
import requests
import os
from urllib.parse import urlparse

# Load the exported CSV file (adjust the path as needed)
# The CSV should have columns: 'sku' and 'datasheet_url' (where datasheet_url contains the base code like 'DA4120')
df = pd.read_csv('datasheets.csv')  # Replace with your actual file path

# Remove rows with empty or invalid datasheet_url
df = df.dropna(subset=['datasheet_url'])
df = df[df['datasheet_url'].str.strip() != '']

# Construct the full URL
df['full_url'] = 'https://hs-europe.accuride.com/hubfs/Datasheets/' + df['datasheet_url'].str.strip() + '_en.pdf'

# Identify unique datasheets to avoid duplicates
unique_df = df.drop_duplicates(subset=['full_url']).copy()

# For logging purposes, group SKUs per datasheet
grouped = df.groupby('full_url')['sku'].apply(list).reset_index()

# Create a directory for downloads
os.makedirs('datasheets', exist_ok=True)

# Download each unique datasheet
for index, row in unique_df.iterrows():
    url = row['full_url']
    base_code = row['datasheet_url']
    
    # Filename: base_code_en.pdf (e.g., DA4120_en.pdf)
    filename = f"{base_code}_en.pdf"
    filepath = os.path.join('datasheets', filename)
    
    # Associated SKUs (for logging)
    associated_skus = grouped.loc[grouped['full_url'] == url, 'sku'].values[0]
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded: {filename} (URL: {url})")
        print(f"   Associated SKUs: {', '.join(associated_skus)}")
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            print(f"File not found (404): {url} — Skipping (may not exist for this series)")
        else:
            print(f"HTTP error for {url}: {http_err}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

print("Download process completed.")