# src/ingestion/save_processor.py
"""
Data Persistence Module for Magento AI Assistant
Handles saving cleaned product data to JSON and CSV formats with timestamps and product_id keys.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
import re

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_cleaned_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned products data from JSON.
    
    Args:
        input_path (Optional[Path]): Path to the input JSON file. Defaults to processed folder.
    
    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    if input_path is None:
        input_path = PROCESSED_DIR / "clean_products_with_pdf_parent_child2.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run preprocessor first.")
    
    df = pd.read_json(input_path, orient='records')
    print(f"Loaded {len(df)} records from {input_path}")
    return df

def embed_keys_and_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add product_id as primary key and processed_timestamp for auditability.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
    
    Returns:
        pd.DataFrame: Enhanced DataFrame with index set to product_id.
    """
    df = df.copy()
    df['product_id'] = df['sku']
    df['processed_timestamp'] = datetime.utcnow().isoformat()
    df.set_index('product_id', inplace=True)
    
    print(f"Keys and timestamps embedded; indexed on {len(df)} product_ids")
    return df

def clean_nested_strings(row: pd.Series) -> pd.Series:
    """Clean whitespace and escapes in nested fields."""
    row = row.copy()
    for col in ['inherited_specs', 'pdf_specs', 'capacity', 'dimensions']:
        if col in row and isinstance(row[col], dict):
            if 'features_summary' in row[col]:
                text = row[col]['features_summary']
                # Normalize line breaks and strip extras
                if text is not None:  # Add null check
                    text = re.sub(r'\n+', '\n', text).strip()
                    row[col]['features_summary'] = text
                else:
                    row[col]['features_summary'] = ""
    return row

def serialize_nested_for_csv(row: pd.Series) -> pd.Series:
    """
    Serialize nested dicts (e.g., capacity, dimensions) to strings for CSV compatibility.
    
    Args:
        row (pd.Series): Single row.
    
    Returns:
        pd.Series: Modified row with serialized nests.
    """
    row = row.copy()
    row = clean_nested_strings(row)
    for col in ['capacity', 'dimensions', 'inherited_specs', 'pdf_specs']:
        if col in row and isinstance(row[col], dict):
            row[col] = str(row[col])
    return row

def save_to_formats(df: pd.DataFrame, output_dir: Optional[Path] = None) -> None:
    """
    Export DataFrame to JSON (full fidelity) and CSV (tabular).
    
    Args:
        df (pd.DataFrame): DataFrame to save.
        output_dir (Optional[Path]): Base directory for outputs. Defaults to PROCESSED_DIR.
    """
    output_dir = output_dir or PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_output = output_dir / "magento_products_cleaned.json"
    df.reset_index().to_json(json_output, orient='records', date_format='iso', indent=2)
    
    csv_df = df.reset_index().apply(serialize_nested_for_csv, axis=1)
    csv_output = output_dir / "magento_products_cleaned.csv"
    csv_df.to_csv(csv_output, index=False)
    
    print(f"✅ JSON exported: {json_output} ({len(df)} records)")
    print(f"✅ CSV exported: {csv_output} ({len(df)} records)")

def validate_exports(json_path: Path, csv_path: Path, original_len: int) -> bool:
    """
    Verify saved files match original data integrity.
    
    Args:
        json_path (Path): JSON file path.
        csv_path (Path): CSV file path.
        original_len (int): Expected row count.
    
    Returns:
        bool: True if validation passes.
    """
    try:
        reloaded_json = pd.read_json(json_path, orient='records')
        reloaded_csv = pd.read_csv(csv_path)
        
        json_match = len(reloaded_json) == original_len
        csv_match = len(reloaded_csv) == original_len
        sample_key = reloaded_json.iloc[0]['product_id'] if len(reloaded_json) > 0 else None
        
        print(f"Validation: JSON rows={len(reloaded_json)} (match: {json_match}), "
              f"CSV rows={len(reloaded_csv)} (match: {csv_match})")
        if sample_key:
            print(f"Sample key intact: {sample_key}")
        
        return json_match and csv_match
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main(input_path: Optional[str] = None) -> None:
    """
    Orchestrate the full json-save workflow.
    
    Args:
        input_path (Optional[str]): Optional override for input JSON path.
    """
    try:
        input_p = Path(input_path) if input_path else None
        df = load_cleaned_data(input_p)
        
        enhanced_df = embed_keys_and_timestamps(df)
        save_to_formats(enhanced_df)
        
        json_out = PROCESSED_DIR / "magento_products_cleaned.json"
        csv_out = PROCESSED_DIR / "magento_products_cleaned.csv"
        if validate_exports(json_out, csv_out, len(df)):
            print("🎉 Json-save task completed successfully.")
        else:
            print("⚠️ Validation issues detected; check outputs manually.")
            
    except Exception as e:
        print(f"❌ Error in json-save: {e}")
        raise

if __name__ == "__main__":
    main()
