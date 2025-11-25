import re
from pathlib import Path
import json
import spacy

# ---------- REGEX PATTERNS ----------
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"\b(\+?\d{1,3}[- ]?)?\d{10}\b"

# ---------- LOAD NLP MODEL ----------
# Make sure you run: python -m spacy download en_core_web_sm (locally once)
nlp = spacy.load("en_core_web_sm")

def extract_from_text(text: str) -> dict:
    emails = re.findall(EMAIL_REGEX, text)
    phones = re.findall(PHONE_REGEX, text)

    doc = nlp(text)

    # Simple heuristic: collect location-like entities as possible address parts
    possible_address_bits = [
        ent.text for ent in doc.ents 
        if ent.label_ in ["GPE", "LOC", "FAC", "ORG"]
    ]

    return {
        "emails": sorted(set(emails)),
        "phones": sorted(set([p[0] if isinstance(p, tuple) else p for p in phones])),
        "possible_address_parts": sorted(set(possible_address_bits)),
    }

def process_all_txt_files(input_folder: str = "."):
    results = []

    for path in Path(input_folder).rglob("*.pdf.txt"):
        try:
            text = path.read_text(errors="ignore")
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue

        extracted = extract_from_text(text)
        results.append({
            "file": str(path),
            "extracted": extracted
        })

    # Save JSON output in repo root
    out_path = Path("extracted_contacts.json")
    out_path.write_text(json.dumps(results, indent=4, ensure_ascii=False))
    print(f"✅ Extraction completed. Saved to {out_path}")

if __name__ == "__main__":
    process_all_txt_files(".")
