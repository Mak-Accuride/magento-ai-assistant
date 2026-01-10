def extract_attribute(attrs, code):
    for attr in attrs:
        if attr.get("attribute_code") == code:
            return attr.get("value")
    return None


def map_product_attributes(p):
    """Extract structured fields from raw Magento product data."""
    attrs = p.get("custom_attributes", [])
    print(f"Mapping product SKU: { extract_attribute(attrs, "description")}")
    return {
        "description": extract_attribute(attrs, "description") or "",
        "short_description": extract_attribute(attrs, "short_description") or "",
        "features": extract_attribute(attrs, "product_features") or "",
        "length": extract_attribute(attrs, "length"),
        "uom": extract_attribute(attrs, "uom"),
        "country": extract_attribute(attrs, "country_of_manufacture"),
        "corrosion": extract_attribute(attrs, "corrosion_resistant") == "1",
        "category_ids": extract_attribute(attrs, "category_ids"),
        "download_datasheet": extract_attribute(attrs, "download_datasheet"),
        "specifications": extract_attribute(attrs, "specifications"),
        "material": extract_attribute(attrs, "material"),
        "soft_close": extract_attribute(attrs, "soft_close") or "0",
        "self_open": extract_attribute(attrs, "self_open") or "0",
    
    }

def map_child_product(child):
    """Extract structured fields from raw Magento child product data."""
    attrs = child.get("custom_attributes", [])

    return {
        "sku": child.get("sku"),
        "name": child.get("name"),
        "weight": extract_attribute(attrs, "weight"),
        "prices": {
            "price": child.get("price"),
            "special_price": extract_attribute(attrs, "special_price"),
            "msrp": extract_attribute(attrs, "msrp"),
        },
    }