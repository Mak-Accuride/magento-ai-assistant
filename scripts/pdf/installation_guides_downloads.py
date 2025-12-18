import pandas as pd
import requests
import os

# Automatically locate the CSV in the script's directory for robustness
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'installation_guides.csv')  # Adjust filename if needed

df = pd.read_csv(csv_path)

# Column containing the base code (e.g., '2642', 'DA4120', or 'MISSING')
base_code_column = 'datasheet_url'  # Adjust if your column header differs

# Clean and filter: Convert to string, strip whitespace, handle missing/'MISSING'
df[base_code_column] = df[base_code_column].astype(str).str.strip()
missing_mask = (
    (df[base_code_column].isnull()) |
    (df[base_code_column] == '') |
    (df[base_code_column] == '<NULL>') |  # Common pandas representation
    (df[base_code_column].str.upper() == 'MISSING')
)
missing_skus = df[missing_mask]['sku'].tolist()

if missing_skus:
    print(f"Skipping {len(missing_skus)} SKUs with missing installation guide: {', '.join(missing_skus)}")

df = df[~missing_mask].copy()

if df.empty:
    print("No valid installation guides to download after filtering missing values.")
else:
    # Construct the full URL
    df['full_url'] = 'https://hs-europe.accuride.com/hubfs/InstallationGuides/' + df[base_code_column]

    # Identify unique installation guides
    unique_df = df.drop_duplicates(subset=['full_url']).copy()

    # Group SKUs for logging
    grouped = df.groupby('full_url')['sku'].apply(list).reset_index()

    # Create download directory
    download_dir = os.path.join(script_dir, 'installation_guides')
    os.makedirs(download_dir, exist_ok=True)

    # Download loop
    for index, row in unique_df.iterrows():
        url = row['full_url']
        base_code = row[base_code_column]
        filename = f"{base_code}.pdf"
        filepath = os.path.join(download_dir, filename)
        
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
            if getattr(response, 'status_code', None) == 404:
                print(f"File not found (404): {url} — Skipping (guide may not exist for this series)")
            else:
                print(f"HTTP error for {url}: {http_err}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    print("Installation guides download process completed.")