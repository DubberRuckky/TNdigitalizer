# Intelligent Land Record Digitization and Validation System
### Smart India Hackathon (SIH 2026) | Software Category

> **A production-ready GovTech prototype uniting Multilingual OCR, Adaptive 50+ Year Document Intelligence, Tamper-Evident Base-30 Security Watermarking, and Spatial GIS Cadastral Parcel Integration.**

---

## 🌟 Executive Summary

Physical land records in India (Pattas, Chittas, Inam registers, Ryotwari grants) suffer from parchment degradation, brittle edges, iron-gall ink fading, and handwritten cursive regional scripts (Tamil, Hindi, Marathi, etc.).

This system provides an end-to-end sovereign solution:
1. **Adaptive Ingestion**:
   - **Older Patta (> 50 Years Old)**: Scanned exclusively by authorized Documentation Officers. The local AI reconstructs torn/missing statutory boilerplate text using historical revenue gazettes, while keeping **Citizen Names, Village/Places, and Land Extents strictly under Human-in-the-Loop officer decision control**.
   - **Recent Patta (≤ 50 Years Old)**: Automated AI-first high-speed extraction with exception flagging.
2. **Tamper-Evident Base-30 Security Stamp**:
   - Every digitized deed receives a unique 30-character identifier using an unambiguous character set (omitting easily confused glyphs like `0, 1, I, O, B, S`):
     ```
     7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM
     ```
   - Cryptographically bound to the document's SHA-256 digest and QR code, stamped directly onto the deed image, and archived in the database for **Civil Court Subpoena Verification**.
3. **Spatial GIS Cadastral Parcel Mapping**:
   - Verified records are linked to interactive polygon boundaries on an OpenStreetMap / Cadastral layer.
4. **Infinite Queries Open-Source AI Architecture**:
   - Runs 100% locally with zero external API fees.
   - Compatible with local Ollama vision models (`llama3.2-vision`, `qwen2-vl`) while providing a resilient built-in fallback engine.
   - Tailored specifically to run comfortably on a **Netcup Linux VPS (8GB RAM / 160GB SSD)** using under 300MB RAM.

---

## 🚀 The User Workflow (Matches Prompt Steps)

1. **Step 1: Document Acquisition**:
   - The citizen or officer brings a document (e.g. 1948 Ryotwari deed, 1968 Inam settlement, or 2022 Computerized Patta).
2. **Step 2: Upload via Top "+" Button**:
   - Click the prominent **`+ Upload New Patta / Deed`** button on the navbar.
   - Drag & drop any scanned image or select one of the 3 instant test presets:
     * **1948 Madras Presidency Ryotwari Patta** (78 yrs old → Triggers 50+ yr Human-in-the-Loop review)
     * **1968 Inam Settlement Patta** (58 yrs old → Triggers statutory boilerplate repair)
     * **2022 Digital Patta** (4 yrs old → AI-first automated verification)
3. **Step 3: AI Processing & Netcup Database Ingestion**:
   - The local AI analyzes degradation, checks age, generates candidate fields, matches statutory clauses, and renders the Base-30 Security Stamp.
   - The record is committed to the Netcup SQLite database (pre-seeded with **300 realistic baked-in records**).
4. **Step 4: Instant Search & GIS Map Lookup**:
   - Citizens and officers can search by **Name** (e.g. *"Ramasamy"*, *"Kavitha"*, *"Murugan"*), **Survey No** (e.g. *"142/3A"*), **Patta No**, or **Base-30 Security ID**.
   - Clicking any result pans the interactive GIS map directly to the land parcel polygon and opens the high-resolution stamped deed certificate!

---

## 🖥️ Local Quickstart (Windows or Linux)

### 1. Requirements
- Python 3.10+
- Dependencies: `pip install -r requirements.txt`

### 2. Start the System
```bash
python run_server.py
```

### 3. Open in Browser
- **Main GovTech Web Application**: [http://localhost:8000](http://localhost:8000)
- **SIH 2026 Interactive 8-Slide Presentation**: [http://localhost:8000/presentation](http://localhost:8000/presentation)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 Deploying to Netcup Server (8GB RAM / 160GB SSD)

The codebase includes complete, production-hardened scripts configured for Netcup VPS:

### Option A: One-Click Automatic Script (Ubuntu / Debian)
SSH into your Netcup server and run:
```bash
git clone <your-repo-url> /home/ubuntu/land-digitizer
cd /home/ubuntu/land-digitizer
chmod +x deploy/deploy_netcup.sh
./deploy/deploy_netcup.sh
```
This automatically sets up Python venv, installs Tesseract, seeds 300 records, starts the **systemd service** (`land-digitizer.service`), and configures Nginx reverse proxy on port 80.

### Option B: Docker Compose
```bash
cd deploy
docker compose up -d --build
```
Resource limits are capped at 3GB RAM to keep your Netcup server light, snappy, and stable.

---

## 🛡️ Base-30 Security Identifier & Court Subpoenas

### Character Set:
```
BASE30 = 23456789ACDEFGHJKLMNPQRTUVWXYZ (Exactly 30 characters)
```
- **Excluded**: `0` (confused with O), `1` (confused with I/L), `B` (confused with 8), `S` (confused with 5), `I`, and `O`.
- **Format**: 9 triplets separated by hyphens (27 Base-30 symbols)
  ```
  7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM
  ```
- **Court Subpoena Forensics**:
  When a property title is contested in a civil court, the judge enters the stamped Base-30 Security ID at `/api/subpoena/verify?security_id=...`. The system performs a live cryptographic comparison against the archived SHA-256 deed hash, generating a Section 65B Indian Evidence Act validation certificate.

---

## 📊 Pre-Populated Database (300 Baked-in Records)

The SQLite database (`land_records.db`) comes pre-seeded with 300 realistic Tamil Nadu cadastral records across 6 major revenue districts:
- **Coimbatore** (Pollachi, Anamalai, Negamam)
- **Thanjavur** (Kumbakonam, Swamimalai, Dharasuram)
- **Kanchipuram** (Sriperumbudur, Sunguvarchatram, Mambakkam)
- **Madurai** (Melur, Alanganallur, Palamedu)
- **Salem** (Attur, Mallur, Omalur)
- **Tiruchirappalli** (Srirangam, Lalgudi, Musiri)

Each record contains:
- Bilingual English & Tamil Owner Names
- Extents in Acres & Cents and metric Hectares
- High-fidelity generated deed certificates stamped with QR & Base-30 security ribbons
- GeoJSON cadastral survey polygons mapped on Leaflet GIS
- Full chain-of-custody audit logs

---

## 📽️ SIH 2026 Presentation Slides Guide (Judges Pitch)

Navigate to **`/presentation`** to present the 8 high-impact slides matching your hackathon guidelines:

1. **Slide 1 - Title Page**: Overview of problem statement, team roles, and SCAN • CHECK • VERIFY • MAP pipeline.
2. **Slide 2 - 01 / Problem**: The 4 bottlenecks: Degraded physical registers, regional handwritten scripts, manual verification fatigue, and missing spatial GIS links.
3. **Slide 3 - 02 / Proposed Solution**: 4-step workflow: Official Scan → Local AI → Historical Validation → Human Review.
4. **Slide 4 - 03 / Adaptive Processing**: Older Patta (50+ yrs human scanned with legal repair) vs Recent Patta (automated AI-first extraction).
5. **Slide 5 - 04 / Document Intelligence**: Contextual reconstruction without hallucination — legal boilerplate repaired while names/places/extents are preserved for humans.
6. **Slide 6 - 05 / Security & Traceability**: Base-30 tamper-evident ID (`7KQ-4X9-M2R-8TZ-P6C-3NW-H5D-9VA-2LM`), physical image watermarking, and civil court subpoena verification.
7. **Slide 7 - 06 / Integration**: End-to-end linkage from physical paper to verified data, GIS parcel polygon, and secure multi-tier digital architecture.
8. **Slide 8 - 07 / Expected Impact**: Faster administration, higher accuracy, complete traceability, and seamless spatial empowerment for citizens and government.

---

## 🏆 Project Structure
```
├── app/
│   ├── main.py              # FastAPI server with all endpoints & Web UI
│   ├── database.py          # SQLite DB layer with spatial GeoJSON & search
│   ├── security_stamp.py    # Base-30 algorithm, watermark & subpoena validator
│   ├── ai_engine.py         # Adaptive workflow, degradation forensics & legal repair
│   ├── seed_data.py         # Seeds 300 realistic Tamil Nadu land records & deeds
│   └── generate_samples.py  # Creates test deeds (1948, 1968, 2022)
├── static/
│   ├── index.html           # GovTech web app with GIS map & upload workflow
│   ├── presentation.html    # Interactive SIH 2026 8-slide presentation
│   ├── deed_images/         # 300 generated stamped deed images
│   └── samples/             # 3 sample upload deeds
├── deploy/
│   ├── Dockerfile           # Optimized for Netcup 8GB VPS
│   ├── docker-compose.yml   # Multi-container orchestration
│   ├── deploy_netcup.sh     # One-click Ubuntu/Debian deployment script
│   ├── land-digitizer.service # Systemd unit file with memory caps
│   └── nginx.conf           # Production Nginx reverse proxy
├── run_server.py            # Local & server startup runner
├── requirements.txt         # Dependencies
└── README.md                # Documentation & Presentation Guide
```
