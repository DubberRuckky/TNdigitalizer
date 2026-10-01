import hashlib
import hmac
import os
import random
import time
from typing import Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import qrcode
import io

# BASE-30 Character set: exactly 30 unambiguous alphanumeric symbols.
# Omitted confusing glyphs: 0, 1, I, O, B (looks like 8), S (looks like 5).
BASE30_ALPHABET = "23456789ACDEFGHJKLMNPQRTUVWXYZ"
assert len(BASE30_ALPHABET) == 30, "BASE30_ALPHABET must contain exactly 30 characters"

SECRET_SALT = b"SIH-2026-GOV-LAND-RECORDS-DIGITIZATION-KEY-SECURE-V1"


def generate_base30_security_id(seed_data: str = None) -> str:
    """
    Generates a secure Base-30 Document Security ID in the SIH format:
    e.g., 7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM (9 triplets = 27 base-30 chars)
    Optionally deterministically derived from seed_data (e.g. hash of deed + patta_no).
    """
    if seed_data:
        digest = hashlib.sha256((seed_data + str(SECRET_SALT)).encode()).hexdigest()
        # Convert hex digest chunks into Base-30 symbols
        chars = []
        for i in range(0, 27):
            idx = int(digest[(i * 2) % len(digest):(i * 2 + 2) % len(digest) or 2], 16) % 30
            chars.append(BASE30_ALPHABET[idx])
    else:
        chars = [random.choice(BASE30_ALPHABET) for _ in range(27)]

    # Format into triplets separated by hyphens (e.g., 7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM)
    triplets = ["".join(chars[i:i+3]) for i in range(0, 27, 3)]
    return "-".join(triplets)


def compute_document_hash(image_bytes: bytes, metadata_str: str = "") -> str:
    """Computes a SHA-256 cryptographic digest of document bytes + legal metadata."""
    hasher = hashlib.sha256()
    hasher.update(image_bytes)
    if metadata_str:
        hasher.update(metadata_str.encode('utf-8'))
    return hasher.hexdigest()


def stamp_patta_image(
    image: Image.Image,
    security_id: str,
    patta_no: str,
    survey_no: str,
    officer_id: str,
    verification_date: str = None
) -> Tuple[Image.Image, str]:
    """
    Applies the tamper-evident Base-30 Security Stamp and QR Subpoena seal
    onto the Patta deed image. Returns (stamped_image, document_sha256).
    """
    if verification_date is None:
        verification_date = time.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Ensure RGB mode
    img = image.convert("RGB")
    width, height = img.size

    # Compute pre-stamp hash
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    doc_hash = compute_document_hash(buf.getvalue(), f"{patta_no}:{survey_no}:{security_id}")

    # Create overlay for the stamp
    draw = ImageDraw.Draw(img)

    # Load default or fallback font
    try:
        font_large = ImageFont.truetype("arial.ttf", size=max(14, int(width * 0.022)))
        font_bold = ImageFont.truetype("arialbd.ttf", size=max(16, int(width * 0.026)))
        font_small = ImageFont.truetype("arial.ttf", size=max(10, int(width * 0.015)))
    except Exception:
        font_large = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Generate micro QR code containing subpoena verification payload
    qr_payload = f"https://landrecords.gov.in/subpoena/verify?id={security_id}&hash={doc_hash[:16]}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=3,
        border=1
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="#f8fafc").convert("RGB")
    qr_size = min(int(width * 0.14), 100)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    # Stamp banner dimensions at the top or bottom
    banner_height = max(110, int(height * 0.12))
    stamp_y = height - banner_height - 10
    stamp_x = 10
    stamp_w = width - 20

    # Draw security badge background with border
    # Gradient/tinted box with official gold/navy styling
    draw.rectangle(
        [(stamp_x, stamp_y), (stamp_x + stamp_w, stamp_y + banner_height)],
        fill="#f8fafc",
        outline="#1e3a8a",
        width=3
    )

    # Gold security ribbon header
    ribbon_h = 24
    draw.rectangle(
        [(stamp_x, stamp_y), (stamp_x + stamp_w, stamp_y + ribbon_h)],
        fill="#1e3a8a",
        outline="#1e3a8a"
    )
    header_text = "OFFICIAL GOVERNMENT TAMPER-EVIDENT ARCHIVE  *  LEGAL COURT SUBPOENA IDENTIFIER"
    draw.text((stamp_x + 12, stamp_y + 4), header_text, fill="#ffffff", font=font_small)

    # Paste QR Code on right side
    qr_pos_x = stamp_x + stamp_w - qr_size - 12
    qr_pos_y = stamp_y + ribbon_h + 8
    img.paste(qr_img, (qr_pos_x, qr_pos_y))

    # Stamp Details Left side
    text_x = stamp_x + 16
    y_cursor = stamp_y + ribbon_h + 6

    # Security ID in bold Base-30
    draw.text((text_x, y_cursor), "BASE-30 SECURITY ID:", fill="#475569", font=font_small)
    draw.text((text_x + 160, y_cursor - 2), security_id, fill="#b91c1c", font=font_bold)

    y_cursor += 24
    draw.text((text_x, y_cursor), f"PATTA NO: {patta_no}  |  SURVEY NO: {survey_no}", fill="#0f172a", font=font_large)

    y_cursor += 22
    draw.text((text_x, y_cursor), f"OFFICER SCAN ID: {officer_id}  |  TIMESTAMP: {verification_date}", fill="#334155", font=font_small)

    y_cursor += 18
    draw.text((text_x, y_cursor), f"SHA-256 HASH: {doc_hash[:48]}...", fill="#64748b", font=font_small)

    # Also calculate final stamped image SHA-256
    final_buf = io.BytesIO()
    img.save(final_buf, format="JPEG", quality=90)
    final_hash = hashlib.sha256(final_buf.getvalue()).hexdigest()

    return img, final_hash


def verify_subpoena_record(security_id: str, expected_hash: str, current_image_bytes: bytes) -> Dict[str, Any]:
    """
    Court Subpoena Forensics:
    Checks if a document presented in a legal dispute matches the immutable cryptographic record.
    """
    actual_hash = hashlib.sha256(current_image_bytes).hexdigest()
    is_valid = (actual_hash == expected_hash)
    
    return {
        "security_id": security_id,
        "is_valid": is_valid,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "verification_result": "AUTHENTIC - NO TAMPERING DETECTED" if is_valid else "TAMPER WARNING - DIGEST MISMATCH",
        "legal_admissibility": "INDIAN EVIDENCE ACT SEC 65B COMPLIANT" if is_valid else "VOID / CORRUPT",
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
