# fix_unicode.py
import json
from pathlib import Path

file_path = Path("data/processed/magento_products_cleaned.json")
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def clean_dict(d):
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = v.encode('utf-8').decode('unicode-escape')
        elif isinstance(v, dict):
            clean_dict(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    clean_dict(item)

for product in data:
    clean_dict(product)

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Unicode escapes fixed.")