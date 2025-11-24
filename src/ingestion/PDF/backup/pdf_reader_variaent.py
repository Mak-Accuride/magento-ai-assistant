import fitz  # PyMuPDF
import re
import os
import json

# ---------- CONFIG ----------
PDF_FOLDER = "data/samples"
RAW_OUTPUT_FOLDER = "data/raw/pdfs"
STRUCTURED_OUTPUT_FILE = "data/processed/clean_pdf_json/product_specs.json"

# ---------- HELPER FUNCTIONS ----------
def extract_text_from_pdf(pdf_path):
    """Extract full text from a PDF."""
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return None
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def separate_languages(text):
    """Separate English and German sections using pattern matching."""
    # English: Before first German block (starts with "Maximale Durchbiegung" or similar)
    german_start = re.search(r"(?=Maximale Durchbiegung:|Hauptmaterial:|Lastwert:)", text, re.IGNORECASE)
    if german_start:
        english_text = text[:german_start.start()].strip()
        german_text = text[german_start.start():].strip()
    else:
        english_text = text.strip()
        german_text = None
    
    # Refine German to end at English transitions (e.g., "Technical Drawing")
    if german_text:
        english_end = re.search(r"(?=Technical Drawing|Additional Information|Recommended Accessories)", german_text, re.IGNORECASE)
        if english_end:
            german_text = german_text[:english_end.start()].strip()
    
    return {'english_text': english_text, 'german_text': german_text}

def extract_detailed_specs(text):
    """Extract maximum structured details from manual text."""
    specs = {}
    
    # Core specifications
    specs['max_deflection'] = re.search(r"Max Deflection[:\s]+([\d. %]+)", text, re.IGNORECASE)
    specs['max_deflection'] = specs['max_deflection'].group(1).strip() if specs['max_deflection'] else None
    
    specs['ball_bearings'] = re.search(r"Ball Bearings[:\s]+([\d]+ mm)", text, re.IGNORECASE)
    specs['ball_bearings'] = specs['ball_bearings'].group(1).strip() if specs['ball_bearings'] else None
    
    specs['load_rating'] = re.search(r"Load Rating[:\s]+up to ([\d.,]+ kg)", text, re.IGNORECASE)
    specs['load_rating'] = specs['load_rating'].group(1).strip() if specs['load_rating'] else None
    
    specs['slide_extension'] = re.search(r"Slide Extension[:\s]+([\d]+ %)", text, re.IGNORECASE)
    specs['slide_extension'] = specs['slide_extension'].group(1).strip() if specs['slide_extension'] else None
    
    specs['slide_height'] = re.search(r"Slide Height[:\s]+([\d]+ mm)", text, re.IGNORECASE)
    specs['slide_height'] = specs['slide_height'].group(1).strip() if specs['slide_height'] else None
    
    specs['slide_thickness'] = re.search(r"Slide Thickness[:\s]+([\d]+ mm)", text, re.IGNORECASE)
    specs['slide_thickness'] = specs['slide_thickness'].group(1).strip() if specs['slide_thickness'] else None
    
    specs['max_slide_length'] = re.search(r"Maximum Slide Length[:\s]+([\d,]+ mm)", text, re.IGNORECASE)
    specs['max_slide_length'] = specs['max_slide_length'].group(1).strip() if specs['max_slide_length'] else None
    
    specs['temperature_range'] = re.search(r"Temperature Range[:\s]+(-?\d+ °C to \d+ °C)", text, re.IGNORECASE)
    specs['temperature_range'] = specs['temperature_range'].group(1).strip() if specs['temperature_range'] else None
    
    specs['permitted_mounting'] = re.search(r"Permitted Mounting Orientations:\s*(.+?)(?=\nFlat|Corrosion)", text, re.IGNORECASE)
    specs['permitted_mounting'] = specs['permitted_mounting'].group(1).strip() if specs['permitted_mounting'] else None
    
    specs['flat_mounting_note'] = re.search(r"Flat Mounting:\s*(.+?)(?=\nCorrosion)", text, re.IGNORECASE)
    specs['flat_mounting_note'] = specs['flat_mounting_note'].group(1).strip() if specs['flat_mounting_note'] else None
    
    specs['corrosion_resistant'] = re.search(r"Corrosion Resistant:\s*(Yes|No)", text, re.IGNORECASE)
    specs['corrosion_resistant'] = specs['corrosion_resistant'].group(1).strip() if specs['corrosion_resistant'] else None
    
    specs['unit_of_measure'] = re.search(r"Unit Of Measure:\s*(.+?)(?=\n|$)", text, re.IGNORECASE)
    specs['unit_of_measure'] = specs['unit_of_measure'].group(1).strip() if specs['unit_of_measure'] else None
    
    # Materials
    specs['main_material'] = re.search(r"Main Material[:\s]+(.+?)(?=\nBall|Hauptmaterial)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None
    
    specs['ball_material'] = re.search(r"Ball Material[:\s]+(.+?)(?=\nRetainer|Kugelmaterial)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None
    
    specs['retainer_material'] = re.search(r"Retainer Material[:\s]+(.+?)(?=\nFinish|Kugelkäfigmaterial)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None
    
    specs['finish'] = re.search(r"Finish[:\s]+(.+?)(?=\n|$)", text, re.IGNORECASE)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None
    
    # Additional sections
    specs['fixing'] = re.search(r"Fixing\n(.+?)(?=\nNotes)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None
    
    specs['notes'] = re.search(r"Notes\n(.+?)(?=\nDZ4180|Recommended)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None
    
    specs['accessories'] = re.search(r"Recommended Accessories\n(.+?)$", text, re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None
    
    # Variants table
    variant_pattern = r"([A-Z0-9-]+)\n([\d,]+)\n([\d,]+)\n([-\d.,]+)\n([\d.]+)\n([\d,]+)"
    variants = re.findall(variant_pattern, text)
    specs['variants'] = [{'model': v[0], 'sl': v[1], 'tr': v[2], 'a': v[3], 'w': v[4], 'l1': v[5]} for v in variants]
    
    # Filter out None values
    return {k: v for k, v in specs.items() if v is not None}

# ---------- MAIN SCRIPT ----------
def process_all_pdfs(pdf_folder, raw_output_folder, structured_output_file):
    os.makedirs(raw_output_folder, exist_ok=True)
    os.makedirs(os.path.dirname(structured_output_file), exist_ok=True)
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_folder}")
        return
    
    all_specs = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"📄 Processing {pdf_file}...")
        
        # Infer SKU from filename
        sku = pdf_file.split("_")[0]
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            continue
        
        # Separate languages
        lang_split = separate_languages(text)
        
        # Save raw text with language split
        raw_output_file = os.path.join(raw_output_folder, f"{sku}_manual.json")
        raw_data = {"sku": sku, **lang_split}
        with open(raw_output_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved raw text (with lang split) to {raw_output_file}")
        
        # Extract detailed specs (prioritizes English)
        specs = extract_detailed_specs(text)
        specs['product_id'] = sku
        all_specs.append(specs)
    
    # Save structured specs
    with open(structured_output_file, "w", encoding="utf-8") as f:
        json.dump(all_specs, f, indent=2, ensure_ascii=False)
    print(f"\n🎉 All structured specs saved to {structured_output_file}")

if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, RAW_OUTPUT_FOLDER, STRUCTURED_OUTPUT_FILE)