#!/bin/bash
# ============================================================
# UAE PINT AE E-Invoice Engine — AWS EC2 Auto-Deploy Script
# Run this ONCE on a fresh Ubuntu 22.04 EC2 instance
# ============================================================
set -e

REPO_URL="https://github.com/ManasDevHub/pint_uae_einvoice_poc.git"
APP_DIR="/home/ubuntu/uae_invoice"
APP_PORT=8000

echo "========================================"
echo " UAE Invoice Engine — Server Setup"
echo "========================================"

# 1. System updates
echo ">>> [1/7] Updating system..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -qq

# 2. Install Python 3.11
echo ">>> [2/7] Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip git curl -qq

# 3. Install Node.js 20
echo ">>> [3/7] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - -qq
sudo apt-get install -y nodejs -qq
echo "Node: $(node --version) | npm: $(npm --version)"

# 4. Clone the repository
echo ">>> [4/7] Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "Repo already exists — pulling latest..."
    cd "$APP_DIR" && git pull
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
cd "$APP_DIR"

# 5. Setup Python virtual environment and install dependencies
echo ">>> [5/7] Installing Python dependencies..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 6. Build the React frontend
echo ">>> [6/7] Building React frontend..."
cd frontend
npm install --silent
npm run build
cd ..
echo "Frontend built. Contents of /static:"
ls -la static/

# 7. Create systemd service for auto-start on reboot
echo ">>> [7/7] Setting up systemd service..."
sudo bash -c "cat > /etc/systemd/system/uae-invoice.service" <<EOF
[Unit]
Description=UAE PINT AE E-Invoice Engine
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
Environment="API_KEYS=demo-key-123"
Environment="ENVIRONMENT=production"
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable uae-invoice
sudo systemctl restart uae-invoice

echo ""
echo "========================================"
echo " ✅ DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
# Get the public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo " 🌐 Your app is live at:"
echo "    http://${PUBLIC_IP}:${APP_PORT}"
echo ""
echo " 📋 API Endpoints:"
echo "    http://${PUBLIC_IP}:${APP_PORT}/docs"
echo "    http://${PUBLIC_IP}:${APP_PORT}/health/live"
echo ""
echo " 🔄 Service commands:"
echo "    sudo systemctl status uae-invoice   (check status)"
echo "    sudo systemctl restart uae-invoice  (restart)"
echo "    sudo journalctl -u uae-invoice -f   (live logs)"
echo "========================================"
