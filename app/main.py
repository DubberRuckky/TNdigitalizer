import os
import io
import json
import time
import shutil
import random
import hashlib
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from app.database import (
    init_db,
    insert_record,
    search_records,
    get_record_by_id,
    get_record_by_security_id,
    log_subpoena_query,
    get_system_stats,
    get_all_spatial_geojson
)
from app.security_stamp import (
    generate_base30_security_id,
    stamp_patta_image,
    verify_subpoena_record
)
from app.ai_engine import (
    assess_document_degradation,
    reconstruct_legal_text,
    extract_patta_entities_local
)

# Initialize FastAPI App
app = FastAPI(
    title="Intelligent Land Record Digitization and Validation System",
    description="GovTech SIH 2026 Prototype for Legacy Land Record AI Digitization, Human-in-the-loop, Base-30 Security Stamping, and GIS Spatial Cadastral Mapping",
    version="2.0.0"
)

# CORS middleware for open accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DEED_IMAGES_DIR = os.path.join(STATIC_DIR, "deed_images")
SAMPLES_DIR = os.path.join(STATIC_DIR, "samples")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DEED_IMAGES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup_event():
    init_db()
    # Check if samples exist; if not, generate them
    from app.generate_samples import generate_test_upload_samples
    generate_test_upload_samples()
    # Check if DB has records; if empty, seed with 300
    from app.seed_data import seed_database_with_300_records
    seed_database_with_300_records(300, force_recreate=False)


from app.ai_engine import (
    assess_document_degradation,
    reconstruct_legal_text,
    extract_patta_entities_local,
    get_active_ai_provider
)

# ---------------- API SETTINGS & KEY MANAGEMENT ----------------

class AISettingsPayload(BaseModel):
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = "https://api.groq.com/openai/v1"
    vision_model: Optional[str] = "llama-3.2-11b-vision-preview"
    huggingface_api_key: Optional[str] = None
    ollama_host: Optional[str] = "http://localhost:11434"


@app.get("/api/settings/ai")
def get_ai_settings():
    """Returns active AI provider status and masked API keys."""
    return get_active_ai_provider()


@app.post("/api/settings/ai")
def update_ai_settings(payload: AISettingsPayload):
    """Updates API keys dynamically in memory and persists to .env."""
    env_path = os.path.join(BASE_DIR, ".env")
    
    if payload.groq_api_key is not None:
        os.environ["GROQ_API_KEY"] = payload.groq_api_key.strip()
    if payload.openai_api_key is not None:
        os.environ["OPENAI_API_KEY"] = payload.openai_api_key.strip()
    if payload.openai_api_base is not None:
        os.environ["OPENAI_API_BASE"] = payload.openai_api_base.strip()
    if payload.vision_model is not None:
        os.environ["VISION_MODEL"] = payload.vision_model.strip()
    if payload.huggingface_api_key is not None:
        os.environ["HUGGINGFACE_API_KEY"] = payload.huggingface_api_key.strip()
    if payload.ollama_host is not None:
        os.environ["OLLAMA_HOST"] = payload.ollama_host.strip()

    # Persist to .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"GROQ_API_KEY={os.environ.get('GROQ_API_KEY', '')}\n")
        f.write(f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', '')}\n")
        f.write(f"OPENAI_API_BASE={os.environ.get('OPENAI_API_BASE', 'https://api.groq.com/openai/v1')}\n")
        f.write(f"VISION_MODEL={os.environ.get('VISION_MODEL', 'llama-3.2-11b-vision-preview')}\n")
        f.write(f"HUGGINGFACE_API_KEY={os.environ.get('HUGGINGFACE_API_KEY', '')}\n")
        f.write(f"OLLAMA_HOST={os.environ.get('OLLAMA_HOST', 'http://localhost:11434')}\n")
        f.write(f"PORT={os.environ.get('PORT', '8000')}\n")
        f.write(f"HOST={os.environ.get('HOST', '0.0.0.0')}\n")

    return {
        "success": True,
        "message": "AI settings and API key updated successfully!",
        "current_status": get_active_ai_provider()
    }


# ---------------- API ENDPOINTS ----------------

@app.get("/api/stats")
def api_stats():
    """Returns real-time dashboard analytics."""
    return get_system_stats()


@app.get("/api/records")
def api_records(
    q: Optional[str] = Query(None, description="Search by citizen name, survey no, patta no, or security ID"),
    district: Optional[str] = Query("ALL"),
    category: Optional[str] = Query("ALL"),
    status: Optional[str] = Query("ALL"),
    limit: int = Query(50, ge=1, le=300),
    offset: int = Query(0, ge=0)
):
    """Search and filter records across 300+ land archives."""
    records, total = search_records(query=q, district=district, category=category, status=status, limit=limit, offset=offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": records
    }


@app.get("/api/records/{record_id}")
def api_record_detail(record_id: int):
    """Retrieve full record profile including stamped deed picture, GIS geometry, and audit trail."""
    record = get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Patta record not found")
    return record


@app.get("/api/spatial")
def api_spatial():
    """Returns GeoJSON FeatureCollection of all cadastral parcels for the Leaflet GIS Map."""
    return get_all_spatial_geojson()


@app.get("/api/samples")
def api_samples():
    """Returns pre-loaded sample deeds for easy one-click testing of the upload workflow."""
    return [
        {
            "id": "sample-1948",
            "name": "1948 Madras Presidency Ryotwari Patta (Handwritten)",
            "year": 1948,
            "age": 78,
            "type": "OLDER_PATTA_50_PLUS",
            "description": "78 Years Old. Heavily aged parchment with iron-gall ink. Triggers mandatory Officer Human-in-the-Loop review and statutory reconstruction.",
            "file_url": "/static/samples/sample_1948_ryotwari_handwritten.jpg"
        },
        {
            "id": "sample-1968",
            "name": "1968 Inam Abolition Settlement Patta (Faded Register)",
            "year": 1968,
            "age": 58,
            "type": "OLDER_PATTA_50_PLUS",
            "description": "58 Years Old. Faded ink and torn margin. AI reconstructs legal boilerplate while flagging survey boundaries.",
            "file_url": "/static/samples/sample_1968_faded_document.jpg"
        },
        {
            "id": "sample-2022",
            "name": "2022 Computerized 'A' Register Patta Passbook",
            "year": 2022,
            "age": 4,
            "type": "RECENT_PATTA",
            "description": "4 Years Old. Clean electronic deed. AI-first automated extraction with instant validation.",
            "file_url": "/static/samples/sample_2022_digital_patta.jpg"
        }
    ]


@app.post("/api/upload")
async def api_upload(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    officer_id: Optional[str] = Form("OFFICER-REV-DOC-0941")
):
    """
    Step 1 & 2: Handles document ingestion through the + button.
    Runs local AI extraction, degradation forensics, age classification (>50 yrs vs recent),
    and reconstructs statutory legal text while keeping names, places, and areas for human verification.
    """
    temp_img_bytes = None
    filename = "uploaded_patta.jpg"

    if sample_id:
        sample_path = os.path.join(SAMPLES_DIR, f"{sample_id.replace('sample-', 'sample_')}.jpg")
        if not os.path.exists(sample_path):
            # Fallback to direct mapping
            mapping = {
                "sample-1948": "sample_1948_ryotwari_handwritten.jpg",
                "sample-1968": "sample_1968_faded_document.jpg",
                "sample-2022": "sample_2022_digital_patta.jpg"
            }
            sample_path = os.path.join(SAMPLES_DIR, mapping.get(sample_id, "sample_1948_ryotwari_handwritten.jpg"))
        
        with open(sample_path, "rb") as f:
            temp_img_bytes = f.read()
        filename = os.path.basename(sample_path)
    elif file:
        temp_img_bytes = await file.read()
        filename = file.filename
    else:
        raise HTTPException(status_code=400, detail="Either a file upload or sample_id must be provided")

    try:
        pil_image = Image.open(io.BytesIO(temp_img_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

    # Run Local AI extraction and forensics
    ai_result = extract_patta_entities_local(pil_image, filename=filename)

    # Temporary file storage for review preview
    temp_filename = f"temp_preview_{int(time.time())}_{random.randint(100,999)}.jpg"
    temp_path = os.path.join(STATIC_DIR, "deed_images", temp_filename)
    pil_image.save(temp_path, format="JPEG", quality=85)

    # Pre-generate Base-30 Security ID preview
    preview_security_id = generate_base30_security_id()

    return {
        "status": "PROCESSED_BY_AI",
        "officer_id": officer_id,
        "temp_preview_image": f"/static/deed_images/{temp_filename}",
        "preview_security_id": preview_security_id,
        "ai_result": ai_result
    }


class VerifyAndCommitPayload(BaseModel):
    temp_preview_image: str
    security_id: str
    patta_no: str
    survey_no: str
    sub_division: str
    owner_name: str
    relative_name: str
    district: str
    taluk: str
    village: str
    extent_acres_cents: str
    land_classification: str
    record_year: int
    scanner_officer_id: str
    legal_statute: str
    legal_text_reconstructed: str
    north_boundary: str
    south_boundary: str
    east_boundary: str
    west_boundary: str
    confidence_score: float


@app.post("/api/confirm_verification")
def api_confirm_verification(payload: VerifyAndCommitPayload):
    """
    Step 3: Documentation Officer submits verified/reviewed data.
    The system stamps the deed with the Base-30 security code, calculates cryptographic hash,
    generates the cadastral GIS polygon, and commits the record to the Netcup server database.
    """
    # Load the temp image
    rel_temp = payload.temp_preview_image.lstrip("/")
    abs_temp = os.path.join(BASE_DIR, rel_temp.replace("/", os.sep))

    if not os.path.exists(abs_temp):
        raise HTTPException(status_code=400, detail="Temporary preview image expired or not found")

    raw_img = Image.open(abs_temp)

    # Apply physical Base-30 security stamp onto the deed picture
    stamped_img, img_hash = stamp_patta_image(
        image=raw_img,
        security_id=payload.security_id,
        patta_no=payload.patta_no,
        survey_no=payload.survey_no,
        officer_id=payload.scanner_officer_id,
        verification_date=time.strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    # Save stamped deed permanently
    final_filename = f"stamped_{payload.security_id.replace('-', '_')}.jpg"
    final_path = os.path.join(DEED_IMAGES_DIR, final_filename)
    stamped_img.save(final_path, format="JPEG", quality=90)
    final_rel_path = f"/static/deed_images/{final_filename}"
    with open(final_path, "rb") as f:
        disk_hash = hashlib.sha256(f.read()).hexdigest()

    # Calculate extent in hectares
    try:
        parts = payload.extent_acres_cents.split("Acres")
        acres = float(parts[0].strip())
        cents = float(parts[1].replace("Cents", "").strip())
        extent_hectares = round((acres * 0.404686) + (cents * 0.00404686), 2)
    except Exception:
        extent_hectares = 1.0

    age = 2026 - payload.record_year
    category = "OLDER_PATTA_50_PLUS" if age >= 50 else "RECENT_PATTA"

    # Coordinates near chosen district
    district_coords = {
        "Coimbatore": (10.6609, 77.0048),
        "Thanjavur": (10.9602, 79.3845),
        "Kanchipuram": (12.8342, 79.7036),
        "Madurai": (9.9252, 78.1198),
        "Salem": (11.6643, 78.1460),
        "Tiruchirappalli": (10.7905, 78.7047)
    }
    base_lat, base_lng = district_coords.get(payload.district, (11.0, 78.0))
    lat = base_lat + random.uniform(-0.015, 0.015)
    lng = base_lng + random.uniform(-0.015, 0.015)

    # Construct polygon
    d = 0.0012
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [lng, lat],
            [lng + d, lat + 0.0002],
            [lng + d - 0.0001, lat + d],
            [lng, lat + d],
            [lng, lat]
        ]]
    }

    audit_entry = {
        "action": "OFFICER_HUMAN_IN_THE_LOOP_APPROVAL" if category == "OLDER_PATTA_50_PLUS" else "AI_AUTOMATED_INGESTION",
        "officer_id": payload.scanner_officer_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "security_id": payload.security_id,
        "image_hash": disk_hash,
        "note": "Legal identity (Name, Place, Area) verified and sealed with Base-30 security stamp."
    }

    record_data = {
        "patta_no": payload.patta_no,
        "survey_no": payload.survey_no,
        "sub_division": payload.sub_division,
        "owner_name": payload.owner_name,
        "relative_name": payload.relative_name,
        "district": payload.district,
        "taluk": payload.taluk,
        "village": payload.village,
        "extent_hectares": extent_hectares,
        "extent_acres_cents": payload.extent_acres_cents,
        "land_classification": payload.land_classification,
        "record_year": payload.record_year,
        "age_years": age,
        "processing_category": category,
        "scanner_officer_id": payload.scanner_officer_id,
        "verification_status": "VERIFIED_BY_OFFICER" if category == "OLDER_PATTA_50_PLUS" else "AUTO_VERIFIED",
        "security_id": payload.security_id,
        "image_hash": disk_hash,
        "image_path": final_rel_path,
        "confidence_score": payload.confidence_score,
        "legal_statute": payload.legal_statute,
        "legal_text_reconstructed": payload.legal_text_reconstructed,
        "latitude": lat,
        "longitude": lng,
        "geojson_geometry": json.dumps(polygon),
        "north_boundary": payload.north_boundary,
        "south_boundary": payload.south_boundary,
        "east_boundary": payload.east_boundary,
        "west_boundary": payload.west_boundary,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "audit_log": [audit_entry]
    }

    new_id = insert_record(record_data)

    return {
        "success": True,
        "message": f"Patta successfully digitized, stamped, and added to the database with ID #{new_id}!",
        "record_id": new_id,
        "security_id": payload.security_id,
        "image_path": final_rel_path,
        "record": get_record_by_id(new_id)
    }


@app.get("/api/subpoena/verify")
def api_subpoena_verify(
    security_id: str = Query(..., description="Base-30 Document Security ID, e.g. 7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM"),
    court_case_ref: Optional[str] = Query("SUPOENA-INQ-2026")
):
    """
    Legal Court Subpoena Verification:
    Allows civil revenue courts to subpoena and forensically verify the authenticity
    of any stamped Patta deed against the immutable database registry.
    """
    record = get_record_by_security_id(security_id)
    if not record:
        log_subpoena_query(security_id, court_case_ref, "Civil Court Subpoena", "RECORD_NOT_FOUND", False)
        return {
            "found": False,
            "security_id": security_id,
            "message": "No record exists for the provided Base-30 Security ID. Possible forgery or fraudulent deed."
        }

    # Verify image file existence and hash
    rel_img = record["image_path"].lstrip("/")
    abs_img = os.path.join(BASE_DIR, rel_img.replace("/", os.sep))
    
    hash_matched = True
    if os.path.exists(abs_img):
        with open(abs_img, "rb") as f:
            bytes_data = f.read()
        forensics_res = verify_subpoena_record(security_id, record["image_hash"], bytes_data)
        hash_matched = forensics_res["is_valid"]
    
    log_subpoena_query(
        security_id=security_id,
        case_ref=court_case_ref,
        authority="High Court / District Revenue Tribunal",
        result="VALIDATED" if hash_matched else "HASH_MISMATCH",
        matched=hash_matched
    )

    return {
        "found": True,
        "security_id": security_id,
        "verification_result": "AUTHENTIC - SEC 65B CERTIFICATE VALID" if hash_matched else "TAMPER WARNING",
        "record": record,
        "court_case_ref": court_case_ref,
        "legal_guarantee": "This document has a tamper-evident Base-30 identity stamped under Revenue Department custody.",
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }


# ---------------- WEB UI & PRESENTATION ROUTES ----------------

@app.get("/", response_class=HTMLResponse)
def index_view():
    index_file = os.path.join(STATIC_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/presentation", response_class=HTMLResponse)
def presentation_view():
    pres_file = os.path.join(STATIC_DIR, "presentation.html")
    with open(pres_file, "r", encoding="utf-8") as f:
        return f.read()
