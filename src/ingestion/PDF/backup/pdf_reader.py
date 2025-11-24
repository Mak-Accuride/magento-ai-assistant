import fitz  # PyMuPDF
import re
import os
import json

# ---------- CONFIG ----------
PDF_FOLDER = "data/samples"
RAW_OUTPUT_FOLDER = "data/raw/pdfs"
STRUCTURED_OUTPUT_EN_FILE = "data/processed/clean_pdf_json/product_specs_en.json"
STRUCTURED_OUTPUT_FR_FILE = "data/processed/clean_pdf_json/product_specs_fr.json"
STRUCTURED_OUTPUT_DE_FILE = "data/processed/clean_pdf_json/product_specs_de.json"

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
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    lang_blocks = {"en": [], "fr": [], "de": [], "shared": []}

    # Keyword sets must be UNIQUE to each language
    en_kw = {"load", "extension", "slide", "mounting", "temperature", "features", "stainless", "grade"}
    fr_kw = {"charge", "course", "glissière", "température", "fonctions", "acier", "montage", "épaisseur"}
    de_kw = {"lastwert", "auszug", "schiene", "temperatur", "funktionen", "edelstahl", "befestigung"}

    for line in lines:
        lower = line.lower()

        # Numeric / table shared
        if re.fullmatch(r"[0-9.,\-]+", lower) or re.fullmatch(r"[a-z]{1,3}", lower):
            lang_blocks["shared"].append(line)
            continue

        score_en = sum(1 for k in en_kw if k in lower)
        score_fr = sum(1 for k in fr_kw if k in lower)
        score_de = sum(1 for k in de_kw if k in lower)

        scores = {"en": score_en, "fr": score_fr, "de": score_de}
        best = max(scores, key=scores.get)

        if scores[best] > 0:
            lang_blocks[best].append(line)
        else:
            # Default to English only for technical PDFs
            lang_blocks["en"].append(line)

    # 🔥 Remove languages with too little REAL content
    cleaned = {}
    for lang in ["en", "fr", "de"]:
        real_lines = [l for l in lang_blocks[lang] if len(l.split()) > 2]
        if len(real_lines) > 10:   # at least 10 meaningful lines
            cleaned[lang] = "\n".join(real_lines + lang_blocks["shared"])

    return cleaned


def detect_variant_header(line):
    # Normalize weird unicode spaces
    clean = re.sub(r"[\u2000-\u206F\u00A0]", " ", line)
    clean = re.sub(r"\s+", " ", clean).strip()

    headers = clean.split(" ")

    # Expected header items
    expected = {"sl","tr","a","b","c","d","w","l"}

    # Must contain at least 4 valid headers
    matched = sum(h.lower() in expected for h in headers)

    if matched >= 4:
        return headers

    return None

def extract_common_variants(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Filter out numeric garbage (page numbers, "10,000", etc.)
    cleaned = []
    for l in lines:
        # skip pure numbers or numbers with comma
        if re.fullmatch(r"[0-9,.\-]+", l):
            continue
        cleaned.append(l)

    lines = cleaned

    # Step 1: Find the header block: 6–12 uppercase short tokens (SL, TR, A, B…)
    header = []
    start_idx = None

    for i in range(len(lines)):
        if re.fullmatch(r"[A-Z]{1,3}", lines[i]):
            # potential header start
            header_candidate = [lines[i]]
            j = i + 1

            # collect following uppercase tokens
            while j < len(lines) and re.fullmatch(r"[A-Z]{1,3}", lines[j]):
                header_candidate.append(lines[j])
                j += 1

            # A valid header must have at least 6 columns
            if len(header_candidate) >= 6:
                header = header_candidate
                start_idx = j
                break

    if not header:
        print("⚠️ Could not detect vertical header block (after garbage cleanup)")
        return []

    num_cols = len(header)

    # Step 2: Read the values block after header
    values = []
    row = []

    for l in lines[start_idx:]:
        # must be numeric or "-"
        if re.fullmatch(r"[0-9.,\-]+", l):
            row.append(l)

            if len(row) == num_cols:
                values.append(row)
                row = []
        else:
            # stop when non-numeric encountered (end of table)
            if values:
                break

    # Step 3: Build variant rows
    variants = []
    for v in values:
        entry = {h.lower(): val for h, val in zip(header, v)}
        variants.append(entry)

    return variants

def extract_detailed_specs_en(text):
    """Extract detailed specs from full text using English patterns."""
    specs = {}
    
    # Core specifications
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
    
    # Features
    specs['features'] = re.search(r"Features\n(.+?)(?=\nTechnical Drawing)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None
    
    # Materials
    specs['main_material'] = re.search(r"Main Material[:\s]+(.+?)(?=\nBall|Retainer|Finish)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None
    
    specs['ball_material'] = re.search(r"Ball Material[:\s]+(.+?)(?=\nRetainer|Finish)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None
    
    specs['retainer_material'] = re.search(r"Retainer Material[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None
    
    specs['finish'] = re.search(r"Finish[:\s]+(.+?)(?=\nFixing|Additional)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None
    
    # Additional sections
    specs['fixing'] = re.search(r"Fixing\n(.+?)(?=\nNotes)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None
    
    specs['notes'] = re.search(r"Notes\n(.+?)(?=\nRecommended Accessories|End)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None
    
    # Related products from notes
    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []
    
    specs['accessories'] = re.search(r"Recommended Accessories\n(.+?)(?=\nSpare Parts|End)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None
    
    specs['spare_parts'] = re.search(r"Spare Parts\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None
    
    # Variants
    specs['variants'] = extract_common_variants(text)
    
    return {k: v for k, v in specs.items() if v is not None}

def extract_detailed_specs_fr(text):
    """Extract detailed specs from full text using French patterns."""
    specs = {}
    
    # Core specifications (French terms)
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
    
    # Features
    specs['features'] = re.search(r"Fonctions\n(.+?)(?=\nDessin Technique)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None
    
    # Materials
    specs['main_material'] = re.search(r"Matériau principal[:\s]+(.+?)(?=\nMatériau des billes|Finish)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None
    
    specs['ball_material'] = re.search(r"Matériau des billes[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None
    
    specs['retainer_material'] = re.search(r"Matériau du support[:\s]+(.+?)(?=\nFinish)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None
    
    specs['finish'] = re.search(r"Finish[:\s]+(.+?)(?=\nFixation)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None
    
    # Additional sections
    specs['fixing'] = re.search(r"Fixation\n(.+?)(?=\nNotes)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None
    
    specs['notes'] = re.search(r"Notes\n(.+?)(?=\nAccessoires Recommandés|Fin)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None
    
    # Related products from notes
    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []
    
    specs['accessories'] = re.search(r"Accessoires Recommandés\n(.+?)(?=\nPièces de Rechange|Fin)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None
    
    specs['spare_parts'] = re.search(r"Pièces de Rechange\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None
    
    # Variants
    specs['variants'] = extract_common_variants(text)
    
    return {k: v for k, v in specs.items() if v is not None}

def extract_detailed_specs_de(text):
    """Extract detailed specs from full text using German patterns."""
    specs = {}
    
    # Core specifications (German terms)
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
    
    # Features
    specs['features'] = re.search(r"Funktionen\n(.+?)(?=\nTechnische Zeichnung)", text, re.IGNORECASE | re.DOTALL)
    specs['features'] = specs['features'].group(1).strip() if specs['features'] else None
    
    # Materials
    specs['main_material'] = re.search(r"Hauptmaterial[:\s]+(.+?)(?=\nKugelmaterial|Kugelkäfigmaterial)", text, re.IGNORECASE)
    specs['main_material'] = specs['main_material'].group(1).strip() if specs['main_material'] else None
    
    specs['ball_material'] = re.search(r"Kugelmaterial[:\s]+(.+?)(?=\nKugelkäfigmaterial)", text, re.IGNORECASE)
    specs['ball_material'] = specs['ball_material'].group(1).strip() if specs['ball_material'] else None
    
    specs['retainer_material'] = re.search(r"Kugelkäfigmaterial[:\s]+(.+?)(?=\nOberflächenbeschichtung)", text, re.IGNORECASE)
    specs['retainer_material'] = specs['retainer_material'].group(1).strip() if specs['retainer_material'] else None
    
    specs['finish'] = re.search(r"Oberflächenbeschichtung[:\s]+(.+?)(?=\nBefestigung)", text, re.IGNORECASE | re.DOTALL)
    specs['finish'] = specs['finish'].group(1).strip() if specs['finish'] else None
    
    # Additional sections
    specs['fixing'] = re.search(r"Befestigung\n(.+?)(?=\nHinweise)", text, re.IGNORECASE | re.DOTALL)
    specs['fixing'] = specs['fixing'].group(1).strip() if specs['fixing'] else None
    
    specs['notes'] = re.search(r"Hinweise\n(.+?)(?=\nEmpfohlenes Zubehör)", text, re.IGNORECASE | re.DOTALL)
    specs['notes'] = specs['notes'].group(1).strip() if specs['notes'] else None
    
    # Related products from notes
    if specs['notes']:
        related_match = re.findall(r"(DS|DZ)\d+[A-Z0-9-]*", specs['notes'])
        specs['related_products'] = list(set(related_match))
    else:
        specs['related_products'] = []
    
    specs['accessories'] = re.search(r"Empfohlenes Zubehör\n(.+?)(?=\nErsatzteile)", text, re.IGNORECASE | re.DOTALL)
    specs['accessories'] = specs['accessories'].group(1).strip() if specs['accessories'] else None
    
    specs['spare_parts'] = re.search(r"Ersatzteile\n(.+?)$", text, re.DOTALL | re.IGNORECASE)
    specs['spare_parts'] = specs['spare_parts'].group(1).strip() if specs['spare_parts'] else None
    
    # Variants
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
        # Infer SKU, with fallback for "manual.pdf"
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
        
        # Extract full text
        full_text = extract_text_from_pdf(pdf_path)
        if not full_text:
            continue
        
        # Separate for raw output
        lang_split = separate_languages(full_text)
        
        # Save raw
        raw_output_file = os.path.join(raw_output_folder, f"{sku}_manual.json")
        raw_data = {"sku": sku, **lang_split}
        with open(raw_output_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved raw text to {raw_output_file}")
        
        # Initialize specs as empty dicts
        specs_en = {}
        specs_fr = {}
        specs_de = {}
        
        # Extract for each detected language
        if 'en' in lang_split and lang_split['en']:
            specs_en = extract_detailed_specs_en(lang_split['en'])
            specs_en['product_id'] = sku
            specs_en['language'] = 'en'
            all_specs_en.append(specs_en)
        
        if 'fr' in lang_split and lang_split['fr']:
            specs_fr = extract_detailed_specs_fr(lang_split['fr'])
            specs_fr['product_id'] = sku
            specs_fr['language'] = 'fr'
            all_specs_fr.append(specs_fr)
        
        if 'de' in lang_split and lang_split['de']:
            specs_de = extract_detailed_specs_de(lang_split['de'])
            specs_de['product_id'] = sku
            specs_de['language'] = 'de'
            all_specs_de.append(specs_de)
        
        # Yield check using only defined specs
        defined_specs = [s for s in [specs_en, specs_fr, specs_de] if s]
        total_fields = sum(len(s) for s in defined_specs)
        if total_fields < 12:
            print(f"⚠️ Low yield for {sku} ({total_fields} fields); review manual.")
    
    # Save detected languages' specs
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