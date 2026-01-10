import json
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, Any, List
from src.ingestion.clean.transformers import map_product_attributes, map_child_product
from src.ingestion.clean.cleaners import clean_text, normalize_capacity, normalize_dimensions

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PDF_EN_FILE = Path(
    "data/datasheets/processed/clean_pdf_json/product_specs_en_fixed.json"
)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# PDF LOADING (PARENT ONLY)
# --------------------------------------------------
def load_pdf_specs_en() -> Dict[str, Dict[str, Any]]:
    pdf_lookup = {}

    if not PDF_EN_FILE.exists():
        print(f"⚠️ PDF specs not found: {PDF_EN_FILE}")
        return pdf_lookup

    with open(PDF_EN_FILE, "r", encoding="utf-8") as f:
        specs_list = json.load(f)

    for spec in specs_list:
        sku = spec.get("product_id") or spec.get("sku")
        if sku:
            pdf_lookup[sku] = {k: v for k, v in spec.items() if k not in {"product_id", "sku", "language"}}

    # print(f"✅ Loaded {len(pdf_lookup)} PDF specs")
    return pdf_lookup


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def clean_escapes(text):
    if not isinstance(text, str):
        return text

    replacements = {
        r'\\u00b0': '°',
        r'\\u00e4': 'ä',
        r'\\u00fc': 'ü',
        r'\\u00f6': 'ö',
        r'\\u00df': 'ß',
    }

    for pat, rep in replacements.items():
        text = re.sub(pat, rep, text)

    return text


def extract_attributes(attrs) -> dict:
    """
    Extracts attributes from Magento custom_attributes.
    Accepts a list of dicts, a single dict, or None.
    """
    if isinstance(attrs, dict):
        # Already a dictionary
        return attrs
    elif isinstance(attrs, list):
        # List of attribute dicts
        return {a["attribute_code"]: a.get("value") for a in attrs if isinstance(a, dict)}
    else:
        # Something else (string, None, etc.)
        return {}


# --------------------------------------------------
# CORE TRANSFORM
# --------------------------------------------------
def build_child_product(parent, child, parent_attrs):
    # Map parent & child
    mapped_parent = map_product_attributes(parent)
    mapped_child = map_child_product(child)
    # print(f"Processing parent SKU: {mapped_parent['description']}")
    # Full text for capacity & dimensions
    full_text = f"{mapped_parent.get('description', '')} {mapped_parent.get('features', '')} {mapped_child.get('name', '')}"
    dimensions = normalize_dimensions(full_text, mapped_child['sku'], mapped_child['name'])
    capacity = normalize_capacity(full_text)
    # pdf_specs = {}
    # child_sku = mapped_child.get("sku")
    # # Check if child or parent has a datasheet
    # datasheet_url = mapped_child.get("download_datasheet") or mapped_parent.get("download_datasheet")
    # # print(f"Child SKU: {child_sku}, Datasheet URL: {datasheet_url}")
    # pdf_lookup = load_pdf_specs_en()
    # if datasheet_url in pdf_lookup:
    #     pdf_specs = pdf_lookup[datasheet_url]
    #     # Only include matching PDF specs
    #     # pdf_specs = {k: clean_escapes(str(v)) for k, v in parent.get("pdf_specs", {}).items()}
    
    # Inherited specs from parent PDF
    inherited_specs = {k: clean_escapes(str(v)) for k, v in parent.get('pdf_specs', {}).items()}

    # Ensure length is numeric
    try:
        length_mm = mapped_child.get("length")
    except (TypeError, ValueError):
        length_mm = None

    # Build cleaned record
    cleaned = {
        "parent_sku": parent.get("sku"),
        "sku": mapped_child["sku"],
        "name": mapped_child["name"],
        "description": mapped_parent.get("description"),
        "short_description": mapped_parent.get("short_description"),
        "product_features": mapped_parent.get("product_features"),
        "material": mapped_parent.get("material"),
        "length_mm": length_mm,
        "dimensions": dimensions,
        "capacity": capacity,
        "weight_kg": mapped_child.get("weight"),
        "uom": mapped_parent.get("uom"),
        "country_of_manufacture": mapped_parent.get("country_of_manufacture"),
        "category_id": mapped_parent.get("category_ids")[0] if mapped_parent.get("category_ids") else None,
        "inherited_specs": inherited_specs,
        "prices": mapped_child.get("prices"),
        "download_datasheet": mapped_parent.get("download_datasheet"),
        # --- Add all remaining custom attributes from parent ---
        "mpn": mapped_parent.get("mpn"),
        "gtin": mapped_parent.get("gtin"),
        "hub_product_id": mapped_parent.get("hub_product_id"),
        "commodity_code": mapped_parent.get("commodity_code"),
        "finish": mapped_parent.get("finish"),
        "tax_class_id": mapped_parent.get("tax_class_id"),
        "product_for_sales": mapped_parent.get("product_for_sales"),
        "is_top_choice": mapped_parent.get("is_top_choice"),
        "is_returnable": mapped_parent.get("is_returnable"),
        "soft_close": mapped_parent.get("soft_close"),
        "self_close": mapped_parent.get("self_close"),
        "self_open": mapped_parent.get("self_open"),
        "hold_in": mapped_parent.get("hold_in"),
        "hold_out": mapped_parent.get("hold_out"),
        "lock_in": mapped_parent.get("lock_in"),
        "lock_out": mapped_parent.get("lock_out"),
        "interlock": mapped_parent.get("interlock"),
        "cam_adjust": mapped_parent.get("cam_adjust"),
        "rohs": mapped_parent.get("rohs"),
        "bhma": mapped_parent.get("bhma"),
        "awi": mapped_parent.get("awi"),
        "weather_resistant": mapped_parent.get("weather_resistant"),
        "corrosion_resistant": mapped_parent.get("corrosion_resistant"),
        "required_options": mapped_parent.get("required_options"),
        "has_options": mapped_parent.get("has_options"),
        "options_container": mapped_parent.get("options_container"),
        "gift_message_available": mapped_parent.get("gift_message_available"),
        "gift_wrapping_available": mapped_parent.get("gift_wrapping_available"),
        "subaccount": mapped_parent.get("subaccount"),
        "project_number": mapped_parent.get("project_number"),
        # "pdf_specs": pdf_specs,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return cleaned


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------
def preprocess_all():
    input_file = RAW_DIR / "magento_products_full.json"
    output_file = PROCESSED_DIR / "clean_products_with_pdf_parent_child2.json"

    if not input_file.exists():
        print(f"❌ Missing input: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", []) if isinstance(data, dict) else data
    pdf_lookup = load_pdf_specs_en()

    output_products = []

    for parent in items:
        parent_sku = parent.get("sku")
        parent_attrs = extract_attributes(parent.get("custom_attributes"))

        # Attach PDF specs if available
        if parent_sku in pdf_lookup:
            parent["pdf_specs"] = pdf_lookup[parent_sku]

        # Include the parent itself in output
        # mapped_parent = map_product_attributes(parent)
        # parent_record = {
        #     "sku": parent_sku,
        #     "name": parent.get("name"),
        #     "description": mapped_parent.get("description"),
        #     "product_features": mapped_parent.get("product_features"),
        #     "material": mapped_parent.get("material"),
        #     "uom": mapped_parent.get("uom"),
        #     "country_of_manufacture": mapped_parent.get("country"),
        #     "category_id": mapped_parent.get("category_ids")[0] if mapped_parent.get("category_ids") else None,
        #     "pdf_specs": parent.get("pdf_specs"),
        #     "timestamp": datetime.utcnow().isoformat(),
        # }
        # output_products.append(parent_record)

        # Process children
        children = parent.get("children", [])
        for child in children:
            output_products.append(build_child_product(parent, child, parent_attrs))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_products, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(output_products)} child products → {output_file}")


if __name__ == "__main__":
    preprocess_all()
