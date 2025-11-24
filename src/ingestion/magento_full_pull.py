from src.utils.magento_client import MagentoClient
import json, time, os

client = MagentoClient()

def fetch_all_products(page_size=100):
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
    try:
        children = client.get(f"/V1/configurable-products/{sku}/children")
        return children if isinstance(children, list) else []
    except Exception as e:
        print(f"⚠️  Failed to fetch children for {sku}: {e}")
        return []


def fetch_bundle_items(sku: str):
    try:
        bundle = client.get(f"/V1/bundle-products/{sku}/children")
        return bundle if isinstance(bundle, list) else []
    except Exception as e:
        print(f"⚠️  Failed to fetch bundle items for {sku}: {e}")
        return []


def build_structured_product(product):
    """Normalize configurable/bundle structures."""
    sku = product.get("sku")
    type_id = product.get("type_id")

    structured = {
        "sku": sku,
        "name": product.get("name"),
        "type": type_id,
        "status": product.get("status"),
        "visibility": product.get("visibility"),
        "price": product.get("price"),
        "custom_attributes": product.get("custom_attributes", []),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Add children for configurable/bundle
    if type_id == "configurable":
        structured["children"] = fetch_configurable_children(sku)
    elif type_id == "bundle":
        structured["bundle_items"] = fetch_bundle_items(sku)
    else:
        structured["children"] = []

    return structured


if __name__ == "__main__":
    print("🚀 Fetching all products from Magento...")
    products = fetch_all_products()

    structured_products = []
    for p in products:
        structured_products.append(build_structured_product(p))

    os.makedirs("data/raw/products", exist_ok=True)
    output_path = "data/raw/magento_products_full.json"

    with open(output_path, "w") as f:
        json.dump(structured_products, f, indent=2)

    print(f"✅ Saved {len(structured_products)} structured products to {output_path}")
