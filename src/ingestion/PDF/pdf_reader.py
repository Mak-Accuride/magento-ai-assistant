import fitz  # PyMuPDF
import re
import os
import json

# ---------- CONFIG ----------
PDF_FOLDER = "scripts/pdf/datasheets"
RAW_OUTPUT_FOLDER = "data/raw/pdfs/datasheets"
STRUCTURED_OUTPUT_EN_FILE = "data/datasheets/processed/clean_pdf_json/product_specs_en.json"
STRUCTURED_OUTPUT_FR_FILE = "data/datasheets//processed/clean_pdf_json/product_specs_fr.json"
STRUCTURED_OUTPUT_DE_FILE = "data/datasheets//processed/clean_pdf_json/product_specs_de.json"

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

def infer_sku_from_text(text):
    """Fallback SKU extraction from text for special filenames."""
    match = re.search(r"(DS|DZ)\d+[A-Z0-9-]*", text)
    return match.group(0) if match else "unknown"

def separate_languages(text):
    """Improved separation for parallel multilingual PDFs (EN/FR/DE blocks)."""
    lang_blocks = {'en': [], 'fr': [], 'de': [], 'shared': []}
    lines = [line.rstrip() for line in text.split('\n') if line.strip()]  # Clean lines
    # Identify shared sections (tables, pure numbers, headers like SL/TR/A/B/etc.)
    i = 0
    while i < len(lines):
        line_stripped = lines[i].strip()
        if (re.match(r'^[\d,.-]+(\s+[\d,.-]+)*$', line_stripped) or
        re.match(r'^[-]+$', line_stripped) or
        re.match(r'^\d+$', line_stripped) or  # Pure integers (load ratings)
        re.match(r'^[A-Z0-9]{1,3}$', line_stripped) or
        line_stripped in ['SL', 'TR', 'A', 'B', 'C', 'D', 'W', 'L', 'mm', 'kg']):
            # Capture table block
            print(f"Found shared block at line {i}")
            table_start = i
            i += 1
            while i < len(lines):
                current = lines[i].strip()
                if (
                    re.match(r'^[\d,.-]+(\s+[\d,.-]+)*$', current) or
                    current in ['-', '']
                ):
                    print(f"Line {i}: {current}")
                    i += 1
                else:
                    break

            lang_blocks['shared'].extend(lines[table_start:i])
            continue
        print(f"Line {i}: {line_stripped}")
        # Non-shared descriptive lines
        lang_blocks['en' if len(lang_blocks['en']) <= len(lang_blocks['fr']) else 
                    'fr' if len(lang_blocks['fr']) <= len(lang_blocks['de']) else 'de'].append(lines[i])
        i += 1
    print(f"Shared: {len(lang_blocks['shared'])}")
    # Alternative robust method: Split non-shared lines into approximate thirds
    non_shared = [line for line in lines if line not in lang_blocks['shared']]
    third = len(non_shared) // 3
    lang_blocks['en'] = non_shared[:third]
    lang_blocks['fr'] = non_shared[third:2*third]
    lang_blocks['de'] = non_shared[2*third:]

    # Re-append shared to all
    shared_text = '\n'.join(lang_blocks['shared'])
    for lang in ['en', 'fr', 'de']:
        lang_blocks[lang] = '\n'.join(lang_blocks[lang] + lang_blocks['shared'])

    lang_blocks['shared'] = shared_text

    detected = [l for l in ['en', 'fr', 'de'] if lang_blocks[l].strip()]
    print(f"Detected languages: {', '.join(detected)}")
    return {k: v for k, v in lang_blocks.items() if k == 'shared' or k in detected}

def extract_common_variants(text):
    """Extract variants using the original full-text regex."""
    variant_pattern = r"([A-Z0-9-]+)\n([\d,]+)\n([\d,]+)\n([-\d.,]+)\n([\d.]+)\n([\d,]+)"
    variants = re.findall(variant_pattern, text)
    return [
        {'model': v[0], 'sl': v[1], 'tr': v[2], 'a': v[3], 'w': v[4], 'l1': v[5]}
        for v in variants
    ]

# ---------- EXTRACTION FUNCTIONS ----------
def extract_detailed_specs_en(text, shared_text):
    specs = {}
    specs['load_rating'] = re.search(r"Load Rating[:\s]+up to ([\d.,]+ kg)", text, re.IGNORECASE)
    specs['load_rating'] = specs['load_rating'].group(1).strip() if specs['load_rating'] else None

    specs['slide_extension'] = re.search(r"Slide Extension[:\s]+([\d]+ %)", text, re.IGNORECASE)
    specs['slide_extension'] = specs['slide_extension'].group(1).strip() if specs['slide_extension'] else None

    specs['slide_height'] = re.search(r"Slide Height[:\s]+([\d.]+ mm)", text, re.IGNORECASE)
    specs['slide_height'] = specs['slide_height'].group(1).strip() if specs['slide_height'] else None

    specs['slide_thickness'] = re.search(r"Slide Thickness[:\s]+([\d.]+ mm)", text, re.IGNORECASE)
    specs['slide_thickness'] = specs['slide_thickness'].group(1).strip() if specs['slide_thickness'] else None

    specs['max_slide_length'] = re.search(r"Maximum Slide Length[:\s]+([\d,]+ mm)", text, re.IGNORECASE)
    specs['max_slide_length'] = specs['max_slide_length'].group(1).strip() if specs['max_slide_length'] else None

    specs['temperature_range'] = re.search(r"Temperature Range[:\s]+(-?\d+ °C to \+?\d+ °C)", text, re.IGNORECASE)
    specs['temperature_range'] = specs['temperature_range'].group(1).strip() if specs['temperature_range'] else None

    specs['permitted_mounting'] = re.search(r"Permitted Mounting Orientations:\s*(.+?)(?=\nOther|Flat|Corrosion|Features)", text, re.IGNORECASE | re.DOTALL)
    specs['permitted_mounting'] = specs['permitted_mounting'].group(1).strip() if specs['permitted_mounting'] else None

    specs['other_mounting'] = re.search(r"Other Mounting Orientations:\s*(.+?)(?=\nFeatures)", text, re.IGNORECASE | re.DOTALL)
    specs['other_mounting'] = specs['other_mounting'].group(1).strip() if specs['other_mounting'] else None

    specs['flat_mounting_note'] = re.search(r"Flat Mounting:\s*(.+?)(?=\nCorrosion|Unit)", text, re.IGNORECASE | re.DOTALL)
    specs['flat_mounting_note'] = specs['flat_mounting_note'].group(1).strip() if specs['flat_mounting_note'] else None

    specs['corrosion_resistant'] = re.search(r"Corrosion Resistant:\s*(Yes|No)", text, re.IGNORECASE)
    specs['corrosion_resistant'] = specs['corrosion_resistant'].group(1).strip() if specs['corrosion_resistant'] else None

    specs['unit_of_measure'] = re.search(r"Unit Of Measure:\s*(.+?)(?=\nTechnical|$)", text, re.IGNORECASE | re.DOTALL)
    specs['unit_of_measure'] = specs['unit_of_measure'].group(1).strip() if specs['unit_of_measure'] else None

    specs['features'] = re.search(r"Features\n(.+?)(?=\nTechnical Drawing)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None

    specs['main_material'] = re.search(r"Main Material[:\s]+(.+?)(?=\nBall|Retainer|Finish)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None

    specs['ball_material'] = re.search(r"Ball Material[:\s]+(.+?)(?=\nRetainer|Finish)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None

    specs['retainer_material'] = re.search(r"Retainer Material[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None

    specs['finish'] = re.search(r"Finish[:\s]+(.+?)(?=\nFixing|Additional)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None

    specs['fixing'] = re.search(r"Fixing\n(.+?)(?=\nNotes)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None

    specs['notes'] = re.search(r"Notes\n(.+?)(?=\nRecommended Accessories|End)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None

    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []

    specs['accessories'] = re.search(r"Recommended Accessories\n(.+?)(?=\nSpare Parts|End)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None

    specs['spare_parts'] = re.search(r"Spare Parts\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None

    specs['variants'] = extract_common_variants(text)
    return {k: v for k, v in specs.items() if v is not None}

def extract_detailed_specs_fr(text, shared_text):
    specs = {}
    specs['load_rating'] = re.search(r"Charge[:\s]+jusqu’à ([\d.,]+kg)", text, re.IGNORECASE)
    specs['load_rating'] = specs['load_rating'].group(1).strip() if specs['load_rating'] else None

    specs['slide_extension'] = re.search(r"Course[:\s]+([\d]+%)", text, re.IGNORECASE)
    specs['slide_extension'] = specs['slide_extension'].group(1).strip() if specs['slide_extension'] else None

    specs['slide_height'] = re.search(r"Hauteur de glissière[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['slide_height'] = specs['slide_height'].group(1).strip() if specs['slide_height'] else None

    specs['slide_thickness'] = re.search(r"Épaisseur de glissière[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['slide_thickness'] = specs['slide_thickness'].group(1).strip() if specs['slide_thickness'] else None

    specs['max_slide_length'] = re.search(r"Longueur max\. de glissière[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['max_slide_length'] = specs['max_slide_length'].group(1).strip() if specs['max_slide_length'] else None

    specs['temperature_range'] = re.search(r"Température d’utilisation[:\s]+(-?\d+ °C à \+?\d+ °C)", text, re.IGNORECASE)
    specs['temperature_range'] = specs['temperature_range'].group(1).strip() if specs['temperature_range'] else None

    specs['permitted_mounting'] = re.search(r"Montage autorisé:\s*(.+?)(?=\nMontage à plat)", text, re.IGNORECASE | re.DOTALL)
    specs['permitted_mounting'] = specs['permitted_mounting'].group(1).strip() if specs['permitted_mounting'] else None

    specs['other_mounting'] = re.search(r"Montage à plat[:\s]*(.+?)(?=\nFonctions)", text, re.IGNORECASE | re.DOTALL)
    specs['other_mounting'] = specs['other_mounting'].group(1).strip() if specs['other_mounting'] else None

    specs['features'] = re.search(r"Fonctions\n(.+?)(?=\nDessin Technique)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None

    specs['main_material'] = re.search(r"Matériau principal[:\s]+(.+?)(?=\nMatériau des billes|Finish)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None

    specs['ball_material'] = re.search(r"Matériau des billes[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None

    specs['retainer_material'] = re.search(r"Matériau du support[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None

    specs['finish'] = re.search(r"Finish[:\s]+(.+?)(?=\nFixation)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None

    specs['fixing'] = re.search(r"Fixation\n(.+?)(?=\nNotes)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None

    specs['notes'] = re.search(r"Notes\n(.+?)(?=\nAccessoires Recommandés|Fin)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None

    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []

    specs['accessories'] = re.search(r"Accessoires Recommandés\n(.+?)(?=\nPièces de Rechange|Fin)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None

    specs['spare_parts'] = re.search(r"Pièces de Rechange\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None

    specs['variants'] = extract_common_variants(text)
    return {k: v for k, v in specs.items() if v is not None}

def extract_detailed_specs_de(text, shared_text):
    specs = {}
    specs['load_rating'] = re.search(r"Lastwert[:\s]+bis ([\d.,]+ kg)", text, re.IGNORECASE)
    specs['load_rating'] = specs['load_rating'].group(1).strip() if specs['load_rating'] else None

    specs['slide_extension'] = re.search(r"Auszug der Schiene[:\s]+([\d]+ %)", text, re.IGNORECASE)
    specs['slide_extension'] = specs['slide_extension'].group(1).strip() if specs['slide_extension'] else None

    specs['slide_height'] = re.search(r"Schienenhöhe[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['slide_height'] = specs['slide_height'].group(1).strip() if specs['slide_height'] else None

    specs['slide_thickness'] = re.search(r"Schienendicke[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['slide_thickness'] = specs['slide_thickness'].group(1).strip() if specs['slide_thickness'] else None

    specs['max_slide_length'] = re.search(r"Maximale Schienenlänge[:\s]+([\d.,]+ mm)", text, re.IGNORECASE)
    specs['max_slide_length'] = specs['max_slide_length'].group(1).strip() if specs['max_slide_length'] else None

    specs['temperature_range'] = re.search(r"Temperaturbereich[:\s]+(-?\d+ °C bis \+?\d+ °C)", text, re.IGNORECASE)
    specs['temperature_range'] = specs['temperature_range'].group(1).strip() if specs['temperature_range'] else None

    specs['permitted_mounting'] = re.search(r"Mögliche Montageweise:\s*(.+?)(?=\nAndere|Flachmontage)", text, re.IGNORECASE | re.DOTALL)
    specs['permitted_mounting'] = specs['permitted_mounting'].group(1).strip() if specs['permitted_mounting'] else None

    specs['other_mounting'] = re.search(r"Andere Montageweisen:\s*(.+?)(?=\nFunktionen)", text, re.IGNORECASE | re.DOTALL)
    specs['other_mounting'] = specs['other_mounting'].group(1).strip() if specs['other_mounting'] else None

    specs['features'] = re.search(r"Funktionen\n(.+?)(?=\nTechnische Zeichnung)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None

    specs['main_material'] = re.search(r"Hauptmaterial[:\s]+(.+?)(?=\nKugelmaterial|Kugelkäfigmaterial)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None

    specs['ball_material'] = re.search(r"Kugelmaterial[:\s]+(.+?)(?=\nKugelkäfigmaterial)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None

    specs['retainer_material'] = re.search(r"Kugelkäfigmaterial[:\s]+(.+?)(?=\nOberflächenbeschichtung)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None

    specs['finish'] = re.search(r"Oberflächenbeschichtung[:\s]+(.+?)(?=\nBefestigung)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None

    specs['fixing'] = re.search(r"Befestigung\n(.+?)(?=\nHinweise)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None

    specs['notes'] = re.search(r"Hinweise\n(.+?)(?=\nEmpfohlenes Zubehör)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None

    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []

    specs['accessories'] = re.search(r"Empfohlenes Zubehör\n(.+?)(?=\nErsatzteile)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None

    specs['spare_parts'] = re.search(r"Ersatzteile\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None

    specs['variants'] = extract_common_variants(text)
    return {k: v for k, v in specs.items() if v is not None}

# ---------- MAIN SCRIPT ----------
def process_all_pdfs(pdf_folder, raw_output_folder, en_output_file, fr_output_file, de_output_file):
    os.makedirs(raw_output_folder, exist_ok=True)
    os.makedirs(os.path.dirname(en_output_file), exist_ok=True)

    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_folder}")
        return

    all_specs_en = []
    all_specs_fr = []
    all_specs_de = []

    for pdf_file in pdf_files:
        sku = pdf_file.split("_")[0]
        if pdf_file == "manual.pdf":
            full_text = extract_text_from_pdf(os.path.join(pdf_folder, pdf_file))
            sku = infer_sku_from_text(full_text)
            print(f"🔍 Inferred SKU for manual.pdf: {sku}")

        if len(sku) < 3 or not re.match(r'^[A-Z0-9-]+$', sku) or sku == 'manual':
            print(f"⚠️ Skipping invalid SKU: {sku} from {pdf_file}")
            continue

        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"📄 Processing {pdf_file} (SKU: {sku})...")

        full_text = extract_text_from_pdf(pdf_path)
        print(f"✅ Extracted full text from {pdf_file}")
        if not full_text:
            continue
        
        # lang_split = separate_languages(full_text)
        # print(f"✅ Separated languages from {pdf_file}")
        # raw_output_file = os.path.join(raw_output_folder, f"{sku}_manual.json")
        # # raw_data = {"sku": sku, **full_text}
        # with open(raw_output_file, "w", encoding="utf-8") as f:
        #     json.dump(raw_data, f, indent=2, ensure_ascii=False)
        # print(f"✅ Saved raw text to {raw_output_file}")

        specs_en = {}
        specs_fr = {}
        specs_de = {}

        specs_en = extract_detailed_specs_en(full_text, full_text)
        if specs_en:
            specs_en['product_id'] = sku
            specs_en['language'] = 'en'
            all_specs_en.append(specs_en)

        specs_de = extract_detailed_specs_de(full_text, full_text)
        if specs_de:
            specs_de['product_id'] = sku
            specs_de['language'] = 'de'
            all_specs_de.append(specs_de)

        specs_fr = extract_detailed_specs_fr(full_text, full_text)
        if specs_fr:
            specs_fr['product_id'] = sku
            specs_fr['language'] = 'fr'
            all_specs_fr.append(specs_fr)

        defined_specs = [s for s in [specs_en, specs_fr, specs_de] if s]
        total_fields = sum(len(s) for s in defined_specs)
        if total_fields < 12:
            print(f"⚠️ Low yield for {sku} ({total_fields} fields); review manual.")

    if all_specs_en:
        with open(en_output_file, "w", encoding="utf-8") as f:
            json.dump(all_specs_en, f, indent=2, ensure_ascii=False)
        print(f"✅ English specs saved to {en_output_file} ({len(all_specs_en)} entries)")

    if all_specs_fr:
        with open(fr_output_file, "w", encoding="utf-8") as f:
            json.dump(all_specs_fr, f, indent=2, ensure_ascii=False)
        print(f"✅ French specs saved to {fr_output_file} ({len(all_specs_fr)} entries)")

    if all_specs_de:
        with open(de_output_file, "w", encoding="utf-8") as f:
            json.dump(all_specs_de, f, indent=2, ensure_ascii=False)
        print(f"✅ German specs saved to {de_output_file} ({len(all_specs_de)} entries)")

if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, RAW_OUTPUT_FOLDER, STRUCTURED_OUTPUT_EN_FILE, STRUCTURED_OUTPUT_FR_FILE, STRUCTURED_OUTPUT_DE_FILE)