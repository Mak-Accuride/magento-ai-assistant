import fitz  # PyMuPDF
import os
import json

PDF_PATH = "data/samples/manual.pdf"

def extract_text(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found at {pdf_path}")
        return
    
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        print(f"--- Page {page_num} ---\n{text}\n")
        full_text += text + "\n"
    doc.close()
    return full_text

if __name__ == "__main__":
    extracted = extract_text(PDF_PATH)
    if extracted:
        print("✅ PDF text extraction complete!")

        # --- Save extracted text to JSON ---
        product_sku = "DS3031"
        output_file = f"data/processed/{product_sku}_manual.json"
        
        # Make sure the folder exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump({"sku": product_sku, "manual_text": extracted}, f, indent=2)
        
        print(f"✅ Saved manual text to {output_file}")
