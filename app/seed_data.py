import os
import hashlib
import random
import json
import time
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import math

from app.security_stamp import generate_base30_security_id, stamp_patta_image, compute_document_hash
from app.database import init_db, insert_record, get_db_connection

# Seed data templates
DISTRICT_CLUSTERS = [
    {
        "district": "Coimbatore",
        "taluks": ["Pollachi", "Kinathukadavu", "Anamalai", "Sulur"],
        "villages": ["Anamalai", "Negamam", "Zamin Uthukuli", "Kottur", "Somandurai"],
        "base_lat": 10.6609,
        "base_lng": 77.0048
    },
    {
        "district": "Thanjavur",
        "taluks": ["Kumbakonam", "Thiruvaiyaru", "Papanasam", "Orathanadu"],
        "villages": ["Swamimalai", "Dharasuram", "Tirunageswaram", "Ganapathi Agraharam", "Papanasam"],
        "base_lat": 10.9602,
        "base_lng": 79.3845
    },
    {
        "district": "Kanchipuram",
        "taluks": ["Sriperumbudur", "Walajabad", "Kundrathur", "Uthiramerur"],
        "villages": ["Sunguvarchatram", "Mambakkam", "Padappai", "Perungalathur", "Salavakkam"],
        "base_lat": 12.8342,
        "base_lng": 79.7036
    },
    {
        "district": "Madurai",
        "taluks": ["Melur", "Thirumangalam", "Vadipatti", "Alanganallur"],
        "villages": ["Alanganallur", "Palamedu", "Kallandhiri", "Kappalur", "Sholavandan"],
        "base_lat": 9.9252,
        "base_lng": 78.1198
    },
    {
        "district": "Salem",
        "taluks": ["Attur", "Omalur", "Sankari", "Mettur"],
        "villages": ["Mallur", "Tharamangalam", "Mecheri", "Karipatti", "Theevattipatti"],
        "base_lat": 11.6643,
        "base_lng": 78.1460
    },
    {
        "district": "Tiruchirappalli",
        "taluks": ["Srirangam", "Lalgudi", "Manapparai", "Musiri"],
        "villages": ["Srirangam", "Samayapuram", "Poovalur", "Pudur", "Valanadu"],
        "base_lat": 10.7905,
        "base_lng": 78.7047
    }
]

FIRST_NAMES = [
    ("Ramasamy", "ராமசாமி"), ("Kandasamy", "கந்தசாமி"), ("Murugan", "முருகன்"),
    ("Subramanian", "சுப்பிரமணியன்"), ("Lakshmi", "லட்சுமி"), ("Palaniappan", "பழனியப்பன்"),
    ("Kavitha", "கவிதா"), ("Natarajan", "நடராஜன்"), ("Meenakshi", "மீனாட்சி"),
    ("Muthuvel", "முத்துவேல்"), ("Annamalai", "அண்ணாமலை"), ("Marimuthu", "மாரிமுத்து"),
    ("Gomathi", "கோமதி"), ("Valliammai", "வள்ளியம்மை"), ("Velusamy", "வேலுசாமி"),
    ("Rajendran", "ராஜேந்திரன்"), ("Sivakumar", "சிவக்குமார்"), ("Dhandapani", "தண்டபாணி"),
    ("Arumugam", "ஆறுமுகம்"), ("Saraswathi", "சரஸ்வதி"), ("Selvi", "செல்வி"),
    ("Saravanan", "சரவணன்"), ("Balasubramaniam", "பாலசுப்ரமணியம்"), ("Thangavel", "தங்கவேல்"),
    ("Sundararajan", "சுந்தரராஜன்"), ("Alagarsamy", "அழகர்சாமி"), ("Shenbagam", "செண்பகம்"),
    ("Krishnamoorthy", "கிருஷ்ணமூர்த்தி"), ("Devaraj", "தேவராஜ்"), ("Bhoopathi", "பூபதி")
]

CASTES_OR_TITLES = [
    "Gounder", "Pillai", "Chettiar", "Nadar", "Thevar", "Naicker", "Mudaliar",
    "Udayar", "Reddiar", "Ammal", "Achi", "Kounder"
]

RELATIONS = ["S/o", "W/o", "D/o", "H/o"]


def generate_deed_visual_sample(
    patta_no: str,
    survey_no: str,
    owner_name: str,
    village: str,
    taluk: str,
    district: str,
    extent: str,
    year: int,
    security_id: str,
    officer_id: str,
    is_older: bool,
    out_path: str
) -> str:
    """
    Renders an authentic Patta deed certificate image with historical styling or modern tabular layout,
    and applies the official Base-30 Security Stamp.
    """
    img_w, img_h = 900, 1200
    
    if is_older:
        # Aged parchment background with vintage sepia tone
        bg_color = (244, 237, 218)
        border_color = (112, 72, 38)
        text_color = (55, 38, 25)
        seal_color = (139, 44, 34)
    else:
        # Modern official clean government paper style
        bg_color = (250, 252, 255)
        border_color = (30, 58, 138)
        text_color = (15, 23, 42)
        seal_color = (13, 148, 136)

    img = Image.new("RGB", (img_w, img_h), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative double border
    draw.rectangle([(20, 20), (img_w - 20, img_h - 20)], outline=border_color, width=3)
    draw.rectangle([(26, 26), (img_w - 26, img_h - 26)], outline=border_color, width=1)

    # Load fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 24)
        font_h2 = ImageFont.truetype("arialbd.ttf", 16)
        font_body = ImageFont.truetype("arial.ttf", 14)
        font_body_bold = ImageFont.truetype("arialbd.ttf", 14)
        font_watermark = ImageFont.truetype("arialbd.ttf", 54)
    except Exception:
        font_title = ImageFont.load_default()
        font_h2 = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_body_bold = ImageFont.load_default()
        font_watermark = ImageFont.load_default()

    # Draw faint Gov background watermark
    draw.text((160, 480), "GOVERNMENT ARCHIVES", fill=(225, 220, 205) if is_older else (226, 232, 240), font=font_watermark)

    # Top Header
    y = 50
    header_state = "REVENUE DEPARTMENT - GOVERNMENT OF TAMIL NADU"
    draw.text((img_w // 2 - 240, y), header_state, fill=border_color, font=font_h2)
    y += 30

    if is_older:
        sub_title = f"RYOTWARI SETTLEMENT RECORD OF RIGHTS - YEAR {year}"
    else:
        sub_title = f"COMPUTERIZED PATTA PASSBOOK & REGISTER (FASLI 1435 / {year})"
    draw.text((img_w // 2 - 270, y), sub_title, fill=text_color, font=font_title)
    y += 40

    # Official Seal circle simulation
    seal_x, seal_y = img_w - 140, 80
    draw.ellipse([(seal_x, seal_y), (seal_x + 90, seal_y + 90)], outline=seal_color, width=2)
    draw.text((seal_x + 12, seal_y + 35), "SEAL / முத்திரை", fill=seal_color, font=font_body)

    # Document details table
    draw.line([(40, y), (img_w - 40, y)], fill=border_color, width=2)
    y += 20

    rows = [
        ("Patta Number (பட்டா எண்):", patta_no),
        ("Survey / Sub-Division No (புல எண் / உட்பிரிவு):", survey_no),
        ("Registered Land Owner (நில உரிமையாளர்):", owner_name),
        ("District & Taluk (மாவட்டம் & வட்டம்):", f"{district} District, {taluk} Taluk"),
        ("Revenue Village (வருவாய் கிராமம்):", village),
        ("Total Extent (நிலத்தின் பரப்பளவு):", extent),
        ("Classification (நில வகைப்பாடு):", "Dry (Punjai / புஞ்சை)" if "Acres" in extent else "Wet (Nanjai / நஞ்சை)"),
        ("Original Registration Year:", str(year)),
        ("Preservation Class:", "HISTORICAL PERMANENT ARCHIVE (50+ YRS)" if is_older else "CURRENT REVENUE REGISTER")
    ]

    for label, val in rows:
        draw.text((60, y), label, fill=text_color, font=font_body_bold)
        draw.text((430, y), val, fill=text_color, font=font_body)
        y += 28

    y += 15
    draw.line([(40, y), (img_w - 40, y)], fill=border_color, width=1)
    y += 15

    # Statutory text
    draw.text((60, y), "STATUTORY DECLARATION / சட்டப்பூர்வ அறிவிப்பு:", fill=border_color, font=font_h2)
    y += 26
    if is_older:
        legal_blurb = (
            f"Under the Madras Estates (Abolition and Conversion into Ryotwari) Act, 1948, the ryot named\n"
            f"herein is granted permanent rights of possession over Survey Parcel {survey_no} in village {village}.\n"
            f"Subject to the conditions of settlement and payment of kist assessment to the Government."
        )
    else:
        legal_blurb = (
            f"Extracted from the computerized digital land database maintained under the Tamil Nadu Patta Pass\n"
            f"Book Act, 1983 (Act 4 of 1986). Any modification without Tahsildar approval is an offence under Law.\n"
            f"Digitally verifiable via the State Geo-Spatial Portal and Land Records Repository."
        )
    draw.multiline_text((60, y), legal_blurb, fill=text_color, font=font_body, spacing=6)
    y += 80

    # Boundaries box
    draw.rectangle([(60, y), (img_w - 60, y + 100)], outline=border_color, width=1)
    draw.text((70, y + 8), "FOUR BOUNDARIES (நான்கு எல்லைகள்):", fill=border_color, font=font_body_bold)
    draw.text((80, y + 35), f"North: Village Odai / Cart Track     South: Survey No {int(survey_no.split('/')[0]) + 1}", fill=text_color, font=font_body)
    draw.text((80, y + 65), f"East: PWD Irrigation Canal           West: Agricultural Field", fill=text_color, font=font_body)

    # Now stamp the official Base-30 Security Stamp and QR Code
    stamped_img, img_hash = stamp_patta_image(
        image=img,
        security_id=security_id,
        patta_no=patta_no,
        survey_no=survey_no,
        officer_id=officer_id,
        verification_date=f"{year}-06-15 10:00:00 UTC" if not is_older else "2026-09-12 09:30:00 UTC"
    )

    stamped_img.save(out_path, format="JPEG", quality=90)
    with open(out_path, "rb") as f:
        disk_hash = hashlib.sha256(f.read()).hexdigest()
    return disk_hash


def generate_parcel_polygon(center_lat: float, center_lng: float, index: int) -> Dict[str, Any]:
    """Generates a realistic cadastral land parcel polygon around the cluster center."""
    # Slight grid offset
    grid_x = (index % 10) * 0.0018
    grid_y = (index // 10) * 0.0018

    # Random slight irregular polygon mimicking cadastral survey parcels
    lat0 = center_lat + grid_y + random.uniform(-0.0003, 0.0003)
    lng0 = center_lng + grid_x + random.uniform(-0.0003, 0.0003)
    
    dlat = random.uniform(0.0008, 0.0014)
    dlng = random.uniform(0.0008, 0.0015)
    skew = random.uniform(0.0001, 0.0003)

    coords = [
        [lng0, lat0],
        [lng0 + dlng, lat0 + skew],
        [lng0 + dlng - skew, lat0 + dlat],
        [lng0, lat0 + dlat],
        [lng0, lat0]
    ]

    return {
        "type": "Polygon",
        "coordinates": [coords]
    }


def seed_database_with_300_records(total_records: int = 300, force_recreate: bool = False):
    """
    Populates the database with exactly 300 realistic Tamil Nadu land records
    spanning 1920 to 2025, with authentic Base-30 security stamps and images.
    """
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patta_records")
    existing_count = cursor.fetchone()[0]
    conn.close()

    if existing_count >= total_records and not force_recreate:
        print(f"[Seed] Database already has {existing_count} records. Skipping seeding.")
        return

    if force_recreate:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patta_records")
        cursor.execute("DELETE FROM subpoena_logs")
        conn.commit()
        conn.close()

    print(f"[Seed] Initializing 300 baked-in land records with Base-30 Security Stamps...")

    deeds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "deed_images")
    os.makedirs(deeds_dir, exist_ok=True)

    # 120 records > 50 years old (1920-1975), 180 records <= 50 years old (1976-2025)
    legacy_count = 120
    modern_count = total_records - legacy_count

    all_years = []
    # Legacy years (1920 - 1975)
    for _ in range(legacy_count):
        all_years.append(random.randint(1922, 1975))
    # Modern years (1976 - 2025)
    for _ in range(modern_count):
        all_years.append(random.randint(1976, 2025))
    
    random.shuffle(all_years)

    for i in range(total_records):
        year = all_years[i]
        age = 2026 - year
        is_older = (age >= 50)

        cluster = DISTRICT_CLUSTERS[i % len(DISTRICT_CLUSTERS)]
        district = cluster["district"]
        taluk = random.choice(cluster["taluks"])
        village = random.choice(cluster["villages"])

        first_en, first_ta = random.choice(FIRST_NAMES)
        caste = random.choice(CASTES_OR_TITLES)
        full_name = f"{first_en} {caste} ({first_ta})"
        rel_type = random.choice(RELATIONS)
        relative_first, _ = random.choice(FIRST_NAMES)
        relative_name = f"{rel_type} {relative_first} {caste}"

        survey_num = random.randint(12, 450)
        sub_div_letters = ["1", "2", "3A", "3B", "1A1", "2B2", "4C", "1B"]
        sub_div = random.choice(sub_div_letters)
        full_survey = f"{survey_num}/{sub_div}"

        patta_num = f"PATTA-{year}-{district[:3].upper()}-{1000 + i}"
        security_id = generate_base30_security_id(f"{patta_num}:{survey_num}:{year}:{i}")

        acres = random.randint(0, 4)
        cents = random.randint(5, 95)
        extent_acres_cents = f"{acres} Acres {cents} Cents"
        extent_hectares = round((acres * 0.404686) + (cents * 0.00404686), 2)

        officer_id = f"OFFICER-REV-0{random.randint(100, 999)}"
        processing_cat = "OLDER_PATTA_50_PLUS" if is_older else "RECENT_PATTA"
        verif_status = "VERIFIED_BY_OFFICER" if is_older else "AUTO_VERIFIED"
        conf_score = round(random.uniform(0.72, 0.85), 2) if is_older else round(random.uniform(0.94, 0.99), 2)

        # Generate visual stamped deed image
        image_filename = f"deed_{i + 1:04d}_{year}.jpg"
        image_abs_path = os.path.join(deeds_dir, image_filename)
        rel_image_path = f"/static/deed_images/{image_filename}"

        # Generate polygon
        polygon_geom = generate_parcel_polygon(cluster["base_lat"], cluster["base_lng"], i)
        coords = polygon_geom["coordinates"][0]
        parcel_lat = round(sum(c[1] for c in coords) / len(coords), 6)
        parcel_lng = round(sum(c[0] for c in coords) / len(coords), 6)

        # Generate stamped deed visual
        image_hash = generate_deed_visual_sample(
            patta_no=patta_num,
            survey_no=full_survey,
            owner_name=full_name,
            village=village,
            taluk=taluk,
            district=district,
            extent=extent_acres_cents,
            year=year,
            security_id=security_id,
            officer_id=officer_id,
            is_older=is_older,
            out_path=image_abs_path
        )

        legal_statute = (
            "Madras Estates (Abolition and Conversion into Ryotwari) Act XXVI of 1948"
            if is_older else "Tamil Nadu Patta Pass Book Act 1983 (Act 4 of 1986)"
        )
        legal_text = (
            f"Settlement entry confirmed under Section 11 of {legal_statute}. Boundary demarcations cross-verified with District Land Records Registry."
        )

        audit_trail = [
            {
                "action": "DOCUMENT_INGESTION",
                "officer_id": officer_id if is_older else "SYSTEM_AI_DAEMON",
                "timestamp": f"{year}-06-15 09:30:00 UTC",
                "details": f"Document scanned. Age: {age} yrs. Workflow: {processing_cat}"
            },
            {
                "action": "BASE30_SECURITY_STAMPING",
                "officer_id": officer_id,
                "timestamp": "2026-09-12 11:20:00 UTC",
                "security_id": security_id,
                "hash": image_hash[:32]
            },
            {
                "action": "GIS_PARCEL_LINKAGE",
                "officer_id": "GIS-ENGINE-V2",
                "timestamp": "2026-09-12 11:25:00 UTC",
                "coordinates": f"{parcel_lat}, {parcel_lng}"
            }
        ]

        record_data = {
            "patta_no": patta_num,
            "survey_no": full_survey,
            "sub_division": sub_div,
            "owner_name": full_name,
            "relative_name": relative_name,
            "district": district,
            "taluk": taluk,
            "village": village,
            "extent_hectares": extent_hectares,
            "extent_acres_cents": extent_acres_cents,
            "land_classification": "Wet (Nanjai / நஞ்சை)" if i % 3 == 0 else "Dry (Punjai / புஞ்சை)",
            "record_year": year,
            "age_years": age,
            "processing_category": processing_cat,
            "scanner_officer_id": officer_id,
            "verification_status": verif_status,
            "security_id": security_id,
            "image_hash": image_hash,
            "image_path": rel_image_path,
            "confidence_score": conf_score,
            "legal_statute": legal_statute,
            "legal_text_reconstructed": legal_text,
            "latitude": parcel_lat,
            "longitude": parcel_lng,
            "geojson_geometry": json.dumps(polygon_geom),
            "north_boundary": f"Survey No {survey_num - 1} / Odai",
            "south_boundary": f"Survey No {survey_num + 1} / Cart Track",
            "east_boundary": f"Survey No {survey_num} East Sub-division",
            "west_boundary": f"Public Irrigation Channel",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "audit_log": audit_trail
        }

        insert_record(record_data)

    print(f"[Seed] Successfully seeded {total_records} records with Base-30 stamped deed pictures and GIS parcels!")


if __name__ == "__main__":
    seed_database_with_300_records(300, force_recreate=True)
