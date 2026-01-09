def extract_attribute(attrs, code):
    for attr in attrs:
        if attr.get("attribute_code") == code:
            return attr.get("value")
    return None


def map_product_attributes(p):
    """Extract structured fields from raw Magento product data."""
    attrs = p.get("custom_attributes", [])
    return {
        "description": extract_attribute(attrs, "description") or "",
        "features": extract_attribute(attrs, "product_features") or "",
        "length": extract_attribute(attrs, "length"),
        "uom": extract_attribute(attrs, "uom"),
        "country": extract_attribute(attrs, "country_of_manufacture"),
        "corrosion": extract_attribute(attrs, "corrosion_resistant") == "1",
        "category_ids": extract_attribute(attrs, "category_ids"),
        "download_datasheet": extract_attribute(attrs, "download_datasheet"),
        
    }
