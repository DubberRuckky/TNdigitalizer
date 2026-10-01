#!/usr/bin/env bash
# ==============================================================================
# One-Click Deployment Script for Netcup 8GB RAM / 160GB SSD Linux VPS (Ubuntu/Debian)
# ==============================================================================

set -e

echo "=== [1/5] Updating Netcup Server Packages ==="
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl nginx tesseract-ocr fonts-dejavu-core

echo "=== [2/5] Setting up Virtual Environment & Dependencies ==="
PROJECT_DIR="$(pwd)"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [3/5] Generating Samples & Seeding 300 Baked-in Land Records ==="
python3 -m app.generate_samples
python3 -m app.seed_data

echo "=== [4/5] Setting up Systemd Service for 24/7 Autorestart ==="
sudo cp deploy/land-digitizer.service /etc/systemd/system/
sudo sed -i "s|/home/user/land-digitizer|${PROJECT_DIR}|g" /etc/systemd/system/land-digitizer.service
sudo sed -i "s|User=ubuntu|User=${USER}|g" /etc/systemd/system/land-digitizer.service
sudo systemctl daemon-reload
sudo systemctl enable land-digitizer
sudo systemctl restart land-digitizer

echo "=== [5/5] Configuring Nginx Reverse Proxy ==="
if [ -d "/etc/nginx/sites-available" ]; then
    sudo cp deploy/nginx.conf /etc/nginx/sites-available/land-digitizer
    sudo ln -sf /etc/nginx/sites-available/land-digitizer /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default || true
    sudo nginx -t && sudo systemctl restart nginx
fi

echo "=============================================================================="
echo " SUCCESS! Land Record Digitization System is running on your Netcup VPS!"
echo " Access UI: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')"
echo " Presentation: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')/presentation"
echo "=============================================================================="
