import re
from pathlib import Path
import json


EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
MOBILE_REGEX = r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b"
LANDLINE_REGEX = r"\b0\d{2,4}[- ]?\d{6,8}\b"


def clean_text(text):
    # Remove zero-width and invisible chars
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

    # Replace unicode spaces with normal spaces
    text = text.replace("\u00A0", " ").replace("\u202F", " ").replace("\u2009", " ")

    # Keep only normal ASCII chars
    text = text.encode("ascii", "ignore").decode()

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text


def is_valid_name(line):
    """Return True if the line is a realistic name (no emails, no URLs, not numeric)."""
    if '@' in line:
        return False
    if '.' in line.lower():  # avoid domains like .com/.in/.org
        return False
    if 'http' in line.lower():
        return False
    if len(line.strip()) < 3:
        return False
    if re.search(r'\d', line):  # avoid numbers inside name
        return False
    return True


def extract_person_from_email(email, text):
    username = email.split("@")[0]
    username_clean = re.sub(r"[^a-zA-Z]", "", username).lower()

    # Avoid matching tiny usernames like "it", "hr", "ai"
    if len(username_clean) < 3:
        return ""

    for line in text.split("\n"):
        lower_line = line.lower()

        # Skip invalid lines
        if not is_valid_name(line):
            continue

        # Match username ONLY if inside a clean name line
        if username_clean in lower_line:
            return line.strip()

    return ""


def extract_company_from_email(email, text):
    domain = email.split("@")[1]
    keyword = domain.split(".")[0].lower()

    # Avoid matching very small domain parts (ex: "in", "me")
    if len(keyword) < 3:
        return ""

    for line in text.split("\n"):
        lower_line = line.lower()

        # Skip invalid company lines
        if '@' in lower_line or 'http' in lower_line:
            continue

        if keyword in lower_line:
            return line.strip()

    return ""


def extract_from_text(text: str) -> dict:
    text = clean_text(text)
    emails = sorted(set(re.findall(EMAIL_REGEX, text)))
    mobile_raw = re.findall(r"[0-9]{10,}", text)  # find digit sequences
    mobiles = [m for m in mobile_raw if len(m) == 10 and m[0] in "6789"]

    landlines = sorted(set(re.findall(LANDLINE_REGEX, text)))

    if len(emails) == 0 and len(mobiles) == 0 and len(landlines) == 0:
        return None

    primary_email = emails[0]

    person_name = extract_person_from_email(primary_email, text)
    company_name = extract_company_from_email(primary_email, text)

    return {
        "file_emails": emails,
        "file_phones": mobiles,
        "file_landline": landlines,

        "company_name": company_name,
        "person_name": person_name,

        "primary_email": primary_email
    }


def process_all_txt_files(input_folder: str = "."):
    results = []
    index = 1

    for path in Path(input_folder).rglob("*.pdf.txt"):
        text = path.read_text(errors="ignore")
        extracted = extract_from_text(text)

        if extracted is None:
            continue

        extracted["id"] = index
        extracted["file_name"] = path.name

        results.append(extracted)
        index += 1

    Path("extracted_contacts.json").write_text(
        json.dumps(results, indent=4, ensure_ascii=False)
    )

    print("✅ Extraction completed → extracted_contacts.json")


if __name__ == "__main__":
    process_all_txt_files()
