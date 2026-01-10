import json
from datetime import datetime
from pathlib import Path
import re
from src.ingestion.clean.cleaners import clean_text, flatten_products, normalize_capacity, normalize_dimensions
from ingestion.clean.transformers_backup import map_product_attributes
from typing import Dict, Any, List

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PDF_EN_FILE = Path("data/datasheets/processed/clean_pdf_json/product_specs_en_fixed.json")  # English only
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)  # Ensure folder exists

def normalize_sku_for_lookup(sku: str) -> str:
    """
    Robust normalization for SKU to match PDF lookup keys.
    Examples:
    DZ4501EC      -> DZ4501-EC
    DZ45010060EC  -> DZ4501-0060EC
    DZ4501-60EC   -> DZ4501-0060EC
    """
    if not sku:
        return sku

    # Ensure there's a hyphen before the last alpha suffix (EC, TR, etc.)
    m = re.match(r"(DZ\d{4})(?:-?(\d{2,4}))?([A-Z]+)$", sku)
    if m:
        base, length, suffix = m.groups()
        if length:
            length = length.zfill(4)  # pad to 4 digits if needed
            return f"{base}-{length}{suffix}"
        else:
            return f"{base}-{suffix}"
    return sku

def load_pdf_specs_en() -> Dict[str, Dict[str, Any]]:
    """Load only English structured PDF specs and create SKU lookup."""
    pdf_lookup = {}

    if not PDF_EN_FILE.exists():
        print(f"⚠️ English PDF specs file not found: {PDF_EN_FILE} (no PDF enrichment will be applied)")
        return pdf_lookup

    with open(PDF_EN_FILE, "r", encoding="utf-8") as f:
        specs_list = json.load(f)

    for spec in specs_list:
        parent_sku = normalize_sku_for_lookup(spec.get("product_id") or spec.get("sku"))
        if parent_sku != spec.get("product_id"):
            print(f"⚠️ PDF parent SKU corrected: {spec.get('product_id')} -> {parent_sku}")
            spec["product_id"] = parent_sku

        # Normalize all model SKUs inside
        if "model" in spec and isinstance(spec["model"], list):
            for model_entry in spec["model"]:
                model_sku = model_entry.get("model")
                if model_sku:
                    normalized_model_sku = normalize_sku_for_lookup(model_sku)
                    if normalized_model_sku != model_sku:
                        print(f"⚠️ PDF model SKU corrected: {model_sku} -> {normalized_model_sku}")
                        model_entry["model"] = normalized_model_sku

        # Use the normalized parent SKU as lookup key
        pdf_lookup[parent_sku] = spec


    print(f"✅ Loaded English PDF specs for {len(pdf_lookup)} products")
    return pdf_lookup



def clean_escapes(text):
    """Replace common Unicode escape sequences with actual characters."""
    if isinstance(text, str):
        text = re.sub(r'\\u00b0', '°', text)   # °C
        text = re.sub(r'\\u00e4', 'ä', text)   # ä
        text = re.sub(r'\\u00fc', 'ü', text)   # ü
        text = re.sub(r'\\u00f6', 'ö', text)   # ö
        text = re.sub(r'\\u00df', 'ß', text)   # ß (German eszett)
        text = re.sub(r'\\u00c4', 'Ä', text)   # Ä
        text = re.sub(r'\\u00dc', 'Ü', text)   # Ü
        text = re.sub(r'\\u00d6', 'Ö', text)   # Ö
        # Add more patterns if you see other escapes in your data
        return text
    return text
def dedupe_by_sku(items):
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

def get_parent_sku(sku: str) -> str:
    """
    Remove ONLY the length part of the SKU.
    Keep all feature / mechanism suffixes.
    """
    parts = sku.split("-")

    if len(parts) == 1:
        return sku

    # If last part is numeric (length), remove it
    if parts[-1].isdigit():
        return "-".join(parts[:-1])

    # If last part ends with digits (e.g. 0040TR), strip digits only
    m = re.match(r"(\d+)([A-Z]+)$", parts[-1])
    if m:
        return "-".join(parts[:-1] + [m.group(2)])

    return sku

def identify_parents_and_children(products: List[Dict[str, Any]], pdf_lookup: Dict[str, Dict[str, Any]]) -> tuple[Dict[str, Dict], Dict[str, List[Dict]]]:
    """
    Identify parent products (those with rich description/features or pdf_specs)
    and group children under their parent base SKU.
    Assumption: Child SKUs share the same base (e.g., DZ4501-TR vs DZ4501-0040TR)
    """
    parents = {}
    children_by_parent = {}

    for prod in products:
        sku = prod.get("sku", "")
        if not sku:
            continue
        # Extract base SKU (remove length suffix like "-0040TR")
        base_sku = get_parent_sku(sku)

        has_content = bool(
            prod.get("description") or
            prod.get("features") or
            prod.get("pdf_specs")
        )
        
        if has_content and base_sku not in parents:
            parents[base_sku] = prod
        else:
            children_by_parent.setdefault(base_sku, []).append(prod)
    return parents, children_by_parent

def propagate_shared_data(
    products: List[Dict[str, Any]],
    pdf_lookup: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Propagate pdf_specs and key fields from parent to children."""
    parents, children_by_parent = identify_parents_and_children(products,pdf_lookup)

    enriched = []
    for prod in products:
        sku = prod.get("sku", "")
        if not sku:
            enriched.append(prod)
            continue
        # base_match = re.search(r"([A-Z]+\d+)(?:-\d{4}(TR)?)?", sku)
        # base_sku = base_match.group(1) + (base_match.group(2) or "") if base_match else sku
        base_sku = get_parent_sku(sku)
        parent = parents.get(base_sku)
        if parent and parent is not prod and parent.get("pdf_specs"):
            # Extract essential shared fields to avoid huge duplication
            shared_specs = {
                "load_rating": parent["pdf_specs"].get("load_rating"),
                "slide_extension": parent["pdf_specs"].get("slide_extension"),
                "slide_height": parent["pdf_specs"].get("slide_height"),
                "slide_thickness": parent["pdf_specs"].get("slide_thickness"),
                "temperature_range": parent["pdf_specs"].get("temperature_range"),
                "main_material": parent["pdf_specs"].get("main_material"),
                "finish": parent["pdf_specs"].get("finish"),
                "features_summary": parent["pdf_specs"].get("features"),
                # "variants": parent["pdf_specs"].get("variants", [])  # Full variants list for post-retrieval lookup
            }
            prod.setdefault("inherited_specs", shared_specs)
            # print(f"Propagated shared specs to child {sku} from parent {base_sku}")

        enriched.append(prod)

    # Also add parents (already rich)
    return enriched

def clean_product(p: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced cleaning with propagation-aware extraction."""
    mapped = map_product_attributes(p)  # Existing transformer

    # Extract with fallbacks
    full_text = f"{mapped.get('description', '')} {mapped.get('features', '')} {p.get('name', '')}"
    dimensions = normalize_dimensions(full_text, p.get("sku", ""), p.get("name", ""))
    capacity = normalize_capacity(full_text) or normalize_capacity(mapped.get("description", ""))

    sku = p.get("sku", "")
    if "inherited_specs" in p and isinstance(p["inherited_specs"], dict):
        for field in ['features_summary', 'finish', 'temperature_range', 'main_material']:
            if field in p["inherited_specs"]:
                p["inherited_specs"][field] = clean_escapes(p["inherited_specs"][field])
    cleaned = {
        "sku": sku,
        "name": clean_text(p.get("name", "")),
        "description": clean_text(mapped.get("description", "")),
        "features": clean_text(mapped.get("features", "")),
        "material": mapped.get("material", "aluminium" if "aluminium" in p.get("name", "").lower() else None),
        "length_mm": int(mapped.get("length")) if mapped.get("length") and str(mapped.get("length")).isdigit() else None,
        "dimensions": dimensions,
        "capacity": capacity,
        "weight_kg": p.get("weight"),
        "corrosion_resistant": mapped.get("corrosion_resistant", False),
        "uom": mapped.get("uom"),
        "country_of_manufacture": mapped.get("country_of_manufacture"),
        "category_id": mapped.get("category_ids")[0] if isinstance(mapped.get("category_ids"), list) and mapped.get("category_ids") else None,
        "inherited_specs": p.get("inherited_specs"),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if p.get("pdf_specs"):
        cleaned["pdf_specs"] = {k: v for k, v in p["pdf_specs"].items() if k not in ["product_id", "sku", "language"]}

    if cleaned.get("pdf_specs"):
        cleaned.pop("inherited_specs", None)
    
    return cleaned

def preprocess_all():
    input_file = RAW_DIR / "magento_products_full.json"
    output_file = PROCESSED_DIR / "clean_products_with_pdf.json"
    

    if not input_file.exists():
        print(f"❌ No raw data found at {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", []) if isinstance(data, dict) else data
    flattened_items = flatten_products(items)
    flattened_items = dedupe_by_sku(flattened_items)
    pdf_lookup = load_pdf_specs_en()
    for item in flattened_items:
        sku = item.get("sku", "")
        
        normalized_sku = normalize_sku_for_lookup(sku)
        pdf_specs = pdf_lookup.get(normalized_sku)
        if pdf_specs is None and normalized_sku != sku:
            print(f"⚠️ SKU mismatch corrected: {sku} -> {normalized_sku}")
        if pdf_specs:
            pdf_specs_clean = {k: v for k, v in pdf_specs.items() if k not in ["product_id", "sku", "language"]}
            item["pdf_specs"] = pdf_specs_clean
    enriched_items = propagate_shared_data(flattened_items, pdf_lookup)
    
    cleaned = [clean_product(item) for item in enriched_items]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2 , ensure_ascii=False)

    print(f"✅ Cleaned {len(cleaned)} products → saved to {output_file}")

if __name__ == "__main__":
    preprocess_all()
