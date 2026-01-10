def extract_attribute(attrs, code=None):
    """
    Extracts attributes from Magento custom_attributes.
    If 'code' is provided, returns the value for that attribute code.
    Accepts a list of dicts or a dict.
    """
    if isinstance(attrs, dict):
        # If code is given, return that value, else return the whole dict
        return attrs.get(code) if code else attrs

    if isinstance(attrs, list):
        if code:
            for a in attrs:
                if isinstance(a, dict) and a.get("attribute_code") == code:
                    return a.get("value")
            return None
        else:
            # return all attributes as a dict
            return {a["attribute_code"]: a.get("value") for a in attrs if isinstance(a, dict)}

    # fallback for None or unexpected type
    return None if code else {}



def map_product_attributes(p):
    """Extract ALL structured fields from raw Magento product data."""
    attrs = p.get("custom_attributes", [])

    return {
        # --- Core content ---
        "name": p.get("name"),
        "sku": p.get("sku"),
        "description": extract_attribute(attrs, "description") or "",
        "short_description": extract_attribute(attrs, "short_description") or "",

        # --- Media ---
        "image": extract_attribute(attrs, "image"),
        "small_image": extract_attribute(attrs, "small_image"),
        "thumbnail": extract_attribute(attrs, "thumbnail"),
        "snippet_image": extract_attribute(attrs, "snippet_image"),
        "cross_section_image": extract_attribute(attrs, "cross_section_image"),

        # --- URLs & identifiers ---
        "url_key": extract_attribute(attrs, "url_key"),
        "mpn": extract_attribute(attrs, "mpn"),
        "gtin": extract_attribute(attrs, "gtin"),
        "hub_product_id": extract_attribute(attrs, "hub_product_id"),
        "commodity_code": extract_attribute(attrs, "commodity_code"),

        # --- Categorisation ---
        "category_ids": extract_attribute(attrs, "category_ids"),
        "type": extract_attribute(attrs, "type"),
        "finish": extract_attribute(attrs, "finish"),

        # --- Pricing / sales ---
        "tax_class_id": extract_attribute(attrs, "tax_class_id"),
        "uom": extract_attribute(attrs, "uom"),
        "product_for_sales": extract_attribute(attrs, "product_for_sales") == "1",
        "is_top_choice": extract_attribute(attrs, "is_top_choice") == "1",
        "is_returnable": extract_attribute(attrs, "is_returnable"),

        # --- Logistics ---
        "ship_separately": extract_attribute(attrs, "ship_separately") == "1",
        "must_ship_freight": extract_attribute(attrs, "must_ship_freight") == "1",
        "country_of_manufacture": extract_attribute(attrs, "country_of_manufacture"),

        # --- Technical specs ---
        "specifications": extract_attribute(attrs, "specifications"),
        "load_rating": extract_attribute(attrs, "load_rating"),
        "extension": extract_attribute(attrs, "extension"),
        "side_space": extract_attribute(attrs, "side_space"),
        "mounting": extract_attribute(attrs, "mounting"),
        "material": extract_attribute(attrs, "material"),
        "ball_bearings": extract_attribute(attrs, "ball_bearings"),
        "disconnect": extract_attribute(attrs, "disconnect"),

        # --- Features / behaviour flags ---
        "soft_close": extract_attribute(attrs, "soft_close") == "1",
        "self_close": extract_attribute(attrs, "self_close") == "1",
        "self_open": extract_attribute(attrs, "self_open") == "1",
        "hold_in": extract_attribute(attrs, "hold_in") == "1",
        "hold_out": extract_attribute(attrs, "hold_out") == "1",
        "lock_in": extract_attribute(attrs, "lock_in") == "1",
        "lock_out": extract_attribute(attrs, "lock_out") == "1",
        "interlock": extract_attribute(attrs, "interlock") == "1",
        "cam_adjust": extract_attribute(attrs, "cam_adjust") == "1",

        # --- Compliance / resistance ---
        "rohs": extract_attribute(attrs, "rohs") == "1",
        "bhma": extract_attribute(attrs, "bhma") == "1",
        "awi": extract_attribute(attrs, "awi") == "1",
        "weather_resistant": extract_attribute(attrs, "weather_resistant") == "1",
        "corrosion_resistant": extract_attribute(attrs, "corrosion_resistant") == "1",

        # --- Marketing / UX ---
        "product_features": extract_attribute(attrs, "product_features"),
        "download_datasheet": extract_attribute(attrs, "download_datasheet"),

        # --- Options & configuration ---
        "required_options": extract_attribute(attrs, "required_options") == "1",
        "has_options": extract_attribute(attrs, "has_options") == "1",
        "options_container": extract_attribute(attrs, "options_container"),

        # --- Gift / misc ---
        "gift_message_available": extract_attribute(attrs, "gift_message_available") == "1",
        "gift_wrapping_available": extract_attribute(attrs, "gift_wrapping_available") == "1",

        # --- Internal / misc ---
        "subaccount": extract_attribute(attrs, "subaccount"),
        "project_number": extract_attribute(attrs, "project_number"),
    }

def map_child_product(child):
    attrs = child.get("custom_attributes", [])

    return {
        # --- Core ---
        "id": child.get("id"),
        "sku": child.get("sku"),
        "name": child.get("name"),
        "type": child.get("type_id"),
        "status": child.get("status"),
        "visibility": child.get("visibility"),
        "price": child.get("price"),
        "weight": child.get("weight"),
        "created_at": child.get("created_at"),
        "updated_at": child.get("updated_at"),

        # --- URLs / identifiers ---
        "url_key": extract_attribute(attrs, "url_key"),
        "gtin": extract_attribute(attrs, "gtin"),
        "hub_product_id": extract_attribute(attrs, "hub_product_id"),

        # --- Categories ---
        "category_ids": extract_attribute(attrs, "category_ids"),

        # --- Length / variant-specific ---
        "length": extract_attribute(attrs, "length"),

        # --- Media ---
        "image": extract_attribute(attrs, "image"),
        "small_image": extract_attribute(attrs, "small_image"),
        "thumbnail": extract_attribute(attrs, "thumbnail"),
        "swatch_image": extract_attribute(attrs, "swatch_image"),
        "snippet_image": extract_attribute(attrs, "snippet_image"),
        "cross_section_image": extract_attribute(attrs, "cross_section_image"),

        # --- Pricing per region (keep or delete as needed) ---
        "prices": {
            "at": extract_attribute(attrs, "at_price"),
            "be": extract_attribute(attrs, "be_price"),
            "bg": extract_attribute(attrs, "bg_price"),
            "hr": extract_attribute(attrs, "hr_price"),
            "cy": extract_attribute(attrs, "cy_price"),
            "cz": extract_attribute(attrs, "cz_price"),
            "dk": extract_attribute(attrs, "dk_price"),
            "ee": extract_attribute(attrs, "ee_price"),
            "fi": extract_attribute(attrs, "fi_price"),
            "fr": extract_attribute(attrs, "fr_price"),
            "de": extract_attribute(attrs, "de_price"),
            "gr": extract_attribute(attrs, "gr_price"),
            "hu": extract_attribute(attrs, "hu_price"),
            "ie": extract_attribute(attrs, "ie_price"),
            "it": extract_attribute(attrs, "it_price"),
            "lv": extract_attribute(attrs, "lv_price"),
            "lt": extract_attribute(attrs, "lt_price"),
            "lu": extract_attribute(attrs, "lu_price"),
            "mt": extract_attribute(attrs, "mt_price"),
            "nl": extract_attribute(attrs, "nl_price"),
            "pl": extract_attribute(attrs, "pl_price"),
            "pt": extract_attribute(attrs, "pt_price"),
            "ro": extract_attribute(attrs, "ro_price"),
            "sk": extract_attribute(attrs, "sk_price"),
            "si": extract_attribute(attrs, "si_price"),
            "es": extract_attribute(attrs, "es_price"),
            "se": extract_attribute(attrs, "se_price"),
            "gb": extract_attribute(attrs, "gb_price"),
            "is": extract_attribute(attrs, "is_price"),
            "li": extract_attribute(attrs, "li_price"),
            "no": extract_attribute(attrs, "no_price"),
            "ch": extract_attribute(attrs, "ch_price"),
            "zn": extract_attribute(attrs, "zn_price"),
        },

        # --- Downloads ---
        "download_datasheet": extract_attribute(attrs, "download_datasheet"),
        "download_3dcad_step": extract_attribute(attrs, "download_3dcad_step"),

        # --- Options flags ---
        "required_options": extract_attribute(attrs, "required_options") == "1",
        "has_options": extract_attribute(attrs, "has_options") == "1",

        # --- Sales / misc ---
        "product_for_sales": extract_attribute(attrs, "product_for_sales") == "1",
        "is_top_choice": extract_attribute(attrs, "is_top_choice") == "1",
        "tax_class_id": extract_attribute(attrs, "tax_class_id"),
    }

