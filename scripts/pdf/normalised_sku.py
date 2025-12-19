import json
from pathlib import Path
import re

PDF_FILE = Path("data/datasheets/processed/clean_pdf_json/product_specs_en.json")
OUTPUT_FILE = Path("data/datasheets/processed/clean_pdf_json/product_specs_en_fixed.json")

def normalize_parent_sku(sku: str) -> str:
    """
    Normalize parent SKU by adding '-' before 'EC' if missing.
    Leaves child SKUs like DS5334-0045EC unchanged.
    """
    if not sku:
        return sku

    sku = sku.strip().replace("\u200b", "")  # remove spaces & hidden zero-width characters
    # Only fix SKUs that:
    # - end with EC
    # - do NOT already have a hyphen before EC
    # - do NOT contain extra hyphen or numbers (i.e., are parents)
    if re.match(r"^[A-Z]+\d+EC$", sku):
        sku = re.sub(r"([A-Z]+\d+)(EC)$", r"\1-\2", sku)
    return sku

def fix_pdf_skus(file_path: Path, output_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        specs_list = json.load(f)

    fixed_count = 0
    for spec in specs_list:
        # Try both product_id and sku fields
        for key in ["product_id", "sku"]:
            if key in spec and spec[key]:
                original_sku = spec[key]
                fixed_sku = normalize_parent_sku(original_sku)
                if fixed_sku != original_sku:
                    print(f"⚠️ Corrected parent SKU ({key}): {original_sku} -> {fixed_sku}")
                    spec[key] = fixed_sku
                    fixed_count += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(specs_list, f, indent=2, ensure_ascii=False)

    print(f"✅ Finished fixing PDF specs. Total corrected SKUs: {fixed_count}")
    print(f"Saved fixed file to {output_path}")

if __name__ == "__main__":
    fix_pdf_skus(PDF_FILE, OUTPUT_FILE)
