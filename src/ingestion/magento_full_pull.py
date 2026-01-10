from src.utils.magento_client import MagentoClient
import json
import time
import os

client = MagentoClient()

# --------------------------------------------------
# FETCH PRODUCTS
# --------------------------------------------------
def fetch_all_products(page_size=100):
    """Fetch all products from Magento paginated."""
    all_items = []
    page = 1

    while True:
        print(f"📦 Fetching page {page} ...")
        params = {
            "searchCriteria[currentPage]": page,
            "searchCriteria[pageSize]": page_size,
        }
        data = client.get("/V1/products", params=params)
        items = data.get("items", [])
        if not items:
            break
        all_items.extend(items)
        if len(items) < page_size:
            break
        page += 1
        time.sleep(1)
    return all_items


def fetch_configurable_children(sku: str):
    """Fetch children of a configurable product."""
    try:
        children = client.get(f"/V1/configurable-products/{sku}/children")
        return children if isinstance(children, list) else []
    except Exception as e:
        print(f"⚠️  Failed to fetch children for {sku}: {e}")
        return []


def fetch_bundle_items(sku: str):
    """Fetch bundle items for bundle product."""
    try:
        bundle = client.get(f"/V1/bundle-products/{sku}/children")
        return bundle if isinstance(bundle, list) else []
    except Exception as e:
        print(f"⚠️  Failed to fetch bundle items for {sku}: {e}")
        return []


# --------------------------------------------------
# FETCH ATTRIBUTE & CATEGORY MAPPINGS
# --------------------------------------------------
def fetch_all_attributes():
    """Fetch all attributes + their option lists."""
    attributes = []
    page = 1
    page_size = 100

    while True:
        params = {
            "searchCriteria[currentPage]": page,
            "searchCriteria[pageSize]": page_size
        }
        data = client.get("/V1/products/attributes", params=params)
        items = data.get("items", [])
        if not items:
            break
        attributes.extend(items)
        if len(items) < page_size:
            break
        page += 1
        time.sleep(0.5)
    
    # Map options for each attribute
    attr_options = {}
    for attr in attributes:
        code = attr.get("attribute_code")
        details = client.get(f"/V1/products/attributes/{code}")
        options = {str(opt["value"]): opt["label"] for opt in details.get("options", []) if opt.get("value")}
        attr_options[code] = options

    return attr_options



def fetch_all_categories():
    """Fetch all categories and flatten tree to id->name mapping."""
    categories = client.get("/V1/categories")  # Returns tree
    flat_categories = {}

    def traverse(cat):
        flat_categories[str(cat["id"])] = cat["name"]
        for child in cat.get("children_data", []):
            traverse(child)

    traverse(categories)
    return flat_categories


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def map_custom_attributes(attrs, attr_options):
    """Convert custom_attributes array to dict with values replaced by option labels."""
    mapped = {}
    for a in attrs or []:
        code = a.get("attribute_code")
        value = a.get("value")
        # If attribute has predefined options, map ID -> label
        if code in attr_options and str(value) in attr_options[code]:
            mapped[code] = attr_options[code][str(value)]
        else:
            mapped[code] = value
    return mapped


# --------------------------------------------------
# BUILD STRUCTURED PRODUCT
# --------------------------------------------------
def build_structured_product(product, attr_options, category_lookup):
    sku = product.get("sku")
    type_id = product.get("type_id")

    # Map custom attributes
    mapped_attrs = map_custom_attributes(product.get("custom_attributes", []), attr_options)

    structured = { 
        "sku": sku,
        "name": product.get("name"),
        "type": type_id,
        "status": product.get("status"),
        "visibility": product.get("visibility"),
        "price": product.get("price"),
        "custom_attributes": mapped_attrs,
        "category_name": category_lookup.get(str(mapped_attrs.get("category_ids")[0])) if mapped_attrs.get("category_ids") else None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Add children for configurable/bundle
    if type_id == "configurable":
        children = fetch_configurable_children(sku)
        structured["children"] = [
            build_child_product(c, attr_options, category_lookup) for c in children
        ]
    elif type_id == "bundle":
        bundle_items = fetch_bundle_items(sku)
        structured["bundle_items"] = bundle_items
    else:
        structured["children"] = []

    return structured


def build_child_product(child, attr_options, category_lookup):
    """Build normalized child product."""
    mapped_attrs = map_custom_attributes(child.get("custom_attributes", []), attr_options)
    return {
        "sku": child.get("sku"),
        "name": child.get("name"),
        "type": child.get("type_id"),
        "status": child.get("status"),
        "visibility": child.get("visibility"),
        "price": child.get("price"),
        "weight": child.get("weight"),
        "custom_attributes": mapped_attrs,
        "category_name": category_lookup.get(str(mapped_attrs.get("category_ids")[0])) if mapped_attrs.get("category_ids") else None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------
if __name__ == "__main__":
    print("🚀 Fetching all attribute options ...")
    attr_options = fetch_all_attributes()

    print("🚀 Fetching all categories ...")
    category_lookup = fetch_all_categories()

    print("🚀 Fetching all products ...")
    products = fetch_all_products()

    structured_products = []
    for p in products:
        structured_products.append(build_structured_product(p, attr_options, category_lookup))

    os.makedirs("data/raw/products", exist_ok=True)
    output_path = "data/raw/magento_products_full.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structured_products, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(structured_products)} structured products to {output_path}")
