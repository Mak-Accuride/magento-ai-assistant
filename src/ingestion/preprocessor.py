import json
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, Any, List

from src.ingestion.clean.cleaners import (
    clean_text,
    flatten_products,
    normalize_capacity,
    normalize_dimensions,
)
from src.ingestion.clean.transformers import map_product_attributes

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PDF_EN_FILE = Path(
    "data/datasheets/processed/clean_pdf_json/product_specs_en_fixed.json"
)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def get_download_datasheet(product: Dict[str, Any]) -> str | None:
    """
    Extract download_datasheet attribute from Magento custom_attributes.
    Returns normalized value like 'DB3832-EC-D'
    """
    for attr in product.get("custom_attributes", []):
        if attr.get("attribute_code") == "download_datasheet":
            val = attr.get("value")
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None

# --------------------------------------------------
# PDF LOADING
# --------------------------------------------------

def load_pdf_specs_en() -> Dict[str, Dict[str, Any]]:
    """Load English structured PDF specs and index by SKU."""
    pdf_lookup = {}

    if not PDF_EN_FILE.exists():
        print(f"⚠️ PDF specs not found: {PDF_EN_FILE}")
        return pdf_lookup

    with open(PDF_EN_FILE, "r", encoding="utf-8") as f:
        specs_list = json.load(f)

    for spec in specs_list:
        sku = spec.get("product_id") or spec.get("sku")
        if not sku:
            continue

        # Exact key
        pdf_lookup[sku] = spec

        # Also index by normalized family (safety net)
        pdf_lookup[normalize_sku_family(sku)] = spec

    print(f"✅ Loaded {len(pdf_lookup)} PDF specs")
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
        r'\\u00c4': 'Ä',
        r'\\u00dc': 'Ü',
        r'\\u00d6': 'Ö',
    }

    for pat, rep in replacements.items():
        text = re.sub(pat, rep, text)

    return text


def dedupe_by_sku(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge duplicate SKUs, preferring non-empty values."""
    merged = {}

    for item in items:
        sku = item.get("sku")
        if not sku:
            continue

        if sku not in merged:
            merged[sku] = item
        else:
            for k, v in item.items():
                if merged[sku].get(k) in (None, "", []) and v not in (None, "", []):
                    merged[sku][k] = v

    return list(merged.values())


# --------------------------------------------------
# SKU NORMALIZATION (CRITICAL FIX)
# --------------------------------------------------

def normalize_sku_family(sku: str) -> str:
    """
    Normalize SKU to family form:
    - Removes length segment (-0035, -0040, etc)
    - Preserves compound suffixes (EC, EC-D, TR, TR-HD, etc)

    Examples:
    DB3832-0035EC-D → DB3832-EC-D
    DB3832-EC-D     → DB3832-EC-D
    DZ4505-0025     → DZ4505
    DZ4501-0040EC   → DZ4501-EC
    """
    if not sku:
        return sku

    # Split base (letters+digits) from rest
    m = re.match(r"^([A-Z]+\d+)(.*)$", sku)
    if not m:
        return sku

    base, rest = m.groups()

    # Remove length blocks like -0035 or -0040
    rest = re.sub(r"-\d{3,4}", "", rest)

    # Ensure suffix starts with hyphen if it exists
    if rest and not rest.startswith("-"):
        rest = "-" + rest

    return base + rest



# --------------------------------------------------
# PARENT RESOLUTION
# --------------------------------------------------

def build_parent_index(products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Parents are ONLY products that have pdf_specs.
    Indexed by normalized family SKU.
    """
    parents = {}

    for p in products:
        if p.get("sku") and p.get("pdf_specs"):
            family = normalize_sku_family(p["sku"])
            parents[family] = p

    return parents


def find_parent(product_sku: str, parents: Dict[str, Dict[str, Any]]):
    """
    Resolve parent via:
    1. Normalized family SKU
    2. Fallback: parent SKU is prefix of child SKU
    """
    if not product_sku:
        return None

    family = normalize_sku_family(product_sku)

    # 1️⃣ Exact family match (preferred)
    if family in parents:
        return parents[family]

    # 2️⃣ Fallback: prefix match (DZ4505 → DZ4505-0025)
    for parent_family, parent in parents.items():
        parent_sku = parent.get("sku")
        if parent_sku and product_sku.startswith(parent_sku + "-"):
            return parent

    return None


# --------------------------------------------------
# INHERITANCE LOGIC
# --------------------------------------------------

def propagate_shared_data(
    products: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Propagate shared pdf_specs fields from parent to children."""
    parents = build_parent_index(products)
    enriched = []

    for prod in products:
        sku = prod.get("sku")
        if not sku:
            enriched.append(prod)
            continue

        parent = find_parent(sku, parents)

        # Skip if this product IS the parent
        if not parent or parent is prod:
            enriched.append(prod)
            continue

        pdf = parent.get("pdf_specs", {})

        prod["inherited_specs"] = {
            "load_rating": pdf.get("load_rating"),
            "slide_extension": pdf.get("slide_extension"),
            "slide_height": pdf.get("slide_height"),
            "slide_thickness": pdf.get("slide_thickness"),
            "temperature_range": pdf.get("temperature_range"),
            "main_material": pdf.get("main_material"),
            "finish": pdf.get("finish"),
            "features_summary": pdf.get("features"),
        }

        print(
            f"Propagated specs → child {sku} ← parent {parent['sku']}"
        )

        enriched.append(prod)

    return enriched


# --------------------------------------------------
# FINAL CLEANING
# --------------------------------------------------

def clean_product(p: Dict[str, Any]) -> Dict[str, Any]:
    mapped = map_product_attributes(p)

    full_text = (
        f"{mapped.get('description', '')} "
        f"{mapped.get('features', '')} "
        f"{p.get('name', '')}"
    )

    dimensions = normalize_dimensions(
        full_text, p.get("sku", ""), p.get("name", "")
    )
    capacity = normalize_capacity(full_text) or normalize_capacity(
        mapped.get("description", "")
    )

    if "inherited_specs" in p:
        for k in p["inherited_specs"]:
            p["inherited_specs"][k] = clean_escapes(
                p["inherited_specs"][k]
            )

    cleaned = {
        "sku": p.get("sku"),
        "name": clean_text(p.get("name", "")),
        "description": clean_text(mapped.get("description", "")),
        "features": clean_text(mapped.get("features", "")),
        "material": mapped.get("material"),
        "length_mm": (
            int(mapped.get("length"))
            if str(mapped.get("length")).isdigit()
            else None
        ),
        "dimensions": dimensions,
        "capacity": capacity,
        "weight_kg": p.get("weight"),
        "corrosion_resistant": mapped.get("corrosion_resistant", False),
        "uom": mapped.get("uom"),
        "country_of_manufacture": mapped.get("country_of_manufacture"),
        "category_id": (
            mapped.get("category_ids")[0]
            if isinstance(mapped.get("category_ids"), list)
            and mapped.get("category_ids")
            else None
        ),
        "inherited_specs": p.get("inherited_specs"),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Parent keeps pdf_specs, children never do
    if p.get("pdf_specs"):
        cleaned["pdf_specs"] = {
            k: v
            for k, v in p["pdf_specs"].items()
            if k not in {"product_id", "sku", "language"}
        }
        cleaned.pop("inherited_specs", None)

    return cleaned


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------

def preprocess_all():
    input_file = RAW_DIR / "magento_products_full.json"
    output_file = PROCESSED_DIR / "clean_products_with_pdf_newfile.json"

    if not input_file.exists():
        print(f"❌ Missing input: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", []) if isinstance(data, dict) else data
    items = flatten_products(items)
    items = dedupe_by_sku(items)

    pdf_lookup = load_pdf_specs_en()

    for item in items:
        # 1️⃣ Try Magento datasheet attribute (BEST)
        datasheet_ref = get_download_datasheet(item)

        spec = None
        if datasheet_ref and datasheet_ref in pdf_lookup:
            spec = pdf_lookup[datasheet_ref]
            print(f"📄 PDF matched via datasheet attribute → {item['sku']} ← {datasheet_ref}")

        # 2️⃣ Fallback: SKU-based match
        if not spec:
            sku = item.get("sku")
            if sku in pdf_lookup:
                spec = pdf_lookup[sku]

        if spec:
            item["pdf_specs"] = {
                k: v
                for k, v in spec.items()
                if k not in {"product_id", "sku", "language"}
            }

    items = propagate_shared_data(items)
    cleaned = [clean_product(i) for i in items]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(cleaned)} products → {output_file}")


if __name__ == "__main__":
    preprocess_all()
