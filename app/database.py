import sqlite3
import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "land_records.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patta_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patta_no TEXT UNIQUE NOT NULL,
        survey_no TEXT NOT NULL,
        sub_division TEXT DEFAULT '',
        owner_name TEXT NOT NULL,
        relative_name TEXT DEFAULT '',
        district TEXT NOT NULL,
        taluk TEXT NOT NULL,
        village TEXT NOT NULL,
        extent_hectares REAL DEFAULT 0.0,
        extent_acres_cents TEXT DEFAULT '',
        land_classification TEXT DEFAULT 'Dry (Punjai)',
        record_year INTEGER NOT NULL,
        age_years INTEGER NOT NULL,
        processing_category TEXT NOT NULL,
        scanner_officer_id TEXT NOT NULL,
        verification_status TEXT NOT NULL,
        security_id TEXT UNIQUE NOT NULL,
        image_hash TEXT NOT NULL,
        image_path TEXT NOT NULL,
        confidence_score REAL DEFAULT 0.95,
        legal_statute TEXT DEFAULT '',
        legal_text_reconstructed TEXT DEFAULT '',
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        geojson_geometry TEXT NOT NULL,
        north_boundary TEXT DEFAULT '',
        south_boundary TEXT DEFAULT '',
        east_boundary TEXT DEFAULT '',
        west_boundary TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        audit_log TEXT DEFAULT '[]'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subpoena_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        security_id TEXT NOT NULL,
        court_case_ref TEXT DEFAULT 'SUPOENA-INQ-2026',
        requesting_authority TEXT DEFAULT 'District Revenue Court / Sub-Collector',
        verification_result TEXT NOT NULL,
        hash_matched BOOLEAN NOT NULL,
        queried_at TEXT NOT NULL
    )
    """)

    # Indices for blazing fast search on Netcup server
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_owner_name ON patta_records (owner_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_survey_no ON patta_records (survey_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_village ON patta_records (village)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_id ON patta_records (security_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patta_no ON patta_records (patta_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON patta_records (processing_category)")

    conn.commit()
    conn.close()


def insert_record(data: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    audit_trail = data.get("audit_log", [])
    if isinstance(audit_trail, list):
        audit_trail_json = json.dumps(audit_trail)
    else:
        audit_trail_json = str(audit_trail)

    cursor.execute("""
    INSERT INTO patta_records (
        patta_no, survey_no, sub_division, owner_name, relative_name,
        district, taluk, village, extent_hectares, extent_acres_cents,
        land_classification, record_year, age_years, processing_category,
        scanner_officer_id, verification_status, security_id, image_hash,
        image_path, confidence_score, legal_statute, legal_text_reconstructed,
        latitude, longitude, geojson_geometry, north_boundary, south_boundary,
        east_boundary, west_boundary, created_at, audit_log
    ) VALUES (
        :patta_no, :survey_no, :sub_division, :owner_name, :relative_name,
        :district, :taluk, :village, :extent_hectares, :extent_acres_cents,
        :land_classification, :record_year, :age_years, :processing_category,
        :scanner_officer_id, :verification_status, :security_id, :image_hash,
        :image_path, :confidence_score, :legal_statute, :legal_text_reconstructed,
        :latitude, :longitude, :geojson_geometry, :north_boundary, :south_boundary,
        :east_boundary, :west_boundary, :created_at, :audit_log
    )
    """, {
        **data,
        "audit_log": audit_trail_json
    })
    rec_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rec_id


def search_records(
    query: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if query:
        q_wildcard = f"%{query.strip()}%"
        conditions.append("""(
            owner_name LIKE ? OR 
            patta_no LIKE ? OR 
            survey_no LIKE ? OR 
            village LIKE ? OR 
            taluk LIKE ? OR 
            security_id LIKE ?
        )""")
        params.extend([q_wildcard] * 6)

    if district and district != "ALL":
        conditions.append("district = ?")
        params.append(district)

    if category and category != "ALL":
        conditions.append("processing_category = ?")
        params.append(category)

    if status and status != "ALL":
        conditions.append("verification_status = ?")
        params.append(status)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count total
    count_sql = f"SELECT COUNT(*) FROM patta_records {where_clause}"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # Fetch page
    select_sql = f"""
    SELECT * FROM patta_records 
    {where_clause} 
    ORDER BY id DESC 
    LIMIT ? OFFSET ?
    """
    cursor.execute(select_sql, params + [limit, offset])
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        try:
            r["audit_log"] = json.loads(r["audit_log"])
        except Exception:
            r["audit_log"] = []
        try:
            r["geojson_geometry"] = json.loads(r["geojson_geometry"])
        except Exception:
            pass

    return rows, total_count


def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patta_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    try:
        data["audit_log"] = json.loads(data["audit_log"])
    except Exception:
        data["audit_log"] = []
    try:
        data["geojson_geometry"] = json.loads(data["geojson_geometry"])
    except Exception:
        pass
    return data


def get_record_by_security_id(security_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patta_records WHERE security_id = ?", (security_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    try:
        data["audit_log"] = json.loads(data["audit_log"])
    except Exception:
        data["audit_log"] = []
    try:
        data["geojson_geometry"] = json.loads(data["geojson_geometry"])
    except Exception:
        pass
    return data


def log_subpoena_query(security_id: str, case_ref: str, authority: str, result: str, matched: bool):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO subpoena_logs (security_id, court_case_ref, requesting_authority, verification_result, hash_matched, queried_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (security_id, case_ref, authority, result, matched, time.strftime("%Y-%m-%d %H:%M:%S UTC")))
    conn.commit()
    conn.close()


def get_system_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM patta_records")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patta_records WHERE processing_category = 'OLDER_PATTA_50_PLUS'")
    legacy_50_plus = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patta_records WHERE processing_category = 'RECENT_PATTA'")
    recent_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patta_records WHERE verification_status = 'VERIFIED_BY_OFFICER'")
    officer_verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patta_records WHERE verification_status = 'AUTO_VERIFIED'")
    auto_verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT village) FROM patta_records")
    village_count = cursor.fetchone()[0]

    conn.close()
    return {
        "total_records": total_records,
        "legacy_50_plus": legacy_50_plus,
        "recent_records": recent_records,
        "officer_verified": officer_verified,
        "auto_verified": auto_verified,
        "village_count": village_count,
        "spatial_parcels_mapped": total_records,
        "security_stamped_rate": "100%",
        "subpoena_readiness": "OPERATIONAL"
    }


def get_all_spatial_geojson() -> Dict[str, Any]:
    """Returns a GeoJSON FeatureCollection of all mapped land records for Leaflet GIS."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, patta_no, survey_no, owner_name, village, taluk, district,
           extent_acres_cents, processing_category, verification_status,
           security_id, image_path, latitude, longitude, geojson_geometry
    FROM patta_records
    """)
    rows = cursor.fetchall()
    conn.close()

    features = []
    for r in rows:
        row_dict = dict(r)
        geom = None
        try:
            geom = json.loads(row_dict["geojson_geometry"])
        except Exception:
            pass

        if geom:
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "id": row_dict["id"],
                    "patta_no": row_dict["patta_no"],
                    "survey_no": row_dict["survey_no"],
                    "owner_name": row_dict["owner_name"],
                    "village": row_dict["village"],
                    "taluk": row_dict["taluk"],
                    "district": row_dict["district"],
                    "extent": row_dict["extent_acres_cents"],
                    "category": row_dict["processing_category"],
                    "status": row_dict["verification_status"],
                    "security_id": row_dict["security_id"],
                    "image_path": row_dict["image_path"],
                    "lat": row_dict["latitude"],
                    "lng": row_dict["longitude"]
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }
