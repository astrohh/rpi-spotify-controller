#!/bin/bash
# LoFi Pi Setup Script - Automated Spotify Token Management
# This script sets up the automated token management system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "LoFi Pi - Automated Token Management Setup"
echo "=========================================="

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a regular user (not root)"
    echo "Use: ./setup_auto_tokens.sh"
    exit 1
fi

log "Installing Python dependencies..."
pip3 install -r requirements.txt

log "Making scripts executable..."
chmod +x headless_spotify_auth.py
chmod +x auto_token_manager.py
chmod +x check_token_health.sh

log "Setting up systemd service for automatic token management..."

# Create the service file with correct paths
USER_HOME=$(eval echo ~$USER)
SERVICE_FILE="/tmp/lofi-pi-token-manager.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=LoFi Pi Automatic Spotify Token Manager
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/auto_token_manager.py --continuous
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

log "Installing systemd service..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload

log "Setting up cron job for periodic health checks..."
# Add cron job if it doesn't exist
CRON_JOB="*/30 * * * * $SCRIPT_DIR/check_token_health.sh"
(crontab -l 2>/dev/null | grep -v "check_token_health.sh"; echo "$CRON_JOB") | crontab -

log "Checking current authentication status..."
if [ -f "spotify_tokens.json" ]; then
    log "Existing tokens found, testing..."
    python3 auto_token_manager.py --status
else
    log "No tokens found. You'll need to authenticate first."
fi

echo ""
echo "Setup Complete!"
echo "=============="
echo ""
echo "Next Steps:"
echo "1. If you haven't authenticated yet, run:"
echo "   python3 headless_spotify_auth.py"
echo ""
echo "2. Start the automatic token manager:"
echo "   sudo systemctl enable lofi-pi-token-manager"
echo "   sudo systemctl start lofi-pi-token-manager"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status lofi-pi-token-manager"
echo ""
echo "4. View logs:"
echo "   journalctl -u lofi-pi-token-manager -f"
echo ""
echo "The system will now automatically:"
echo "- Refresh tokens before they expire"
echo "- Monitor token health every 30 minutes"
echo "- Attempt recovery from authentication failures"
echo "- Log all activities for debugging"
echo ""

# Check if tokens exist and are valid
if [ -f "spotify_tokens.json" ]; then
    echo "Testing automatic token management..."
    if python3 auto_token_manager.py --check; then
        echo "✅ Automatic token management is working!"
        
        # Prompt to start the service
        read -p "Would you like to start the automatic token manager service now? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl enable lofi-pi-token-manager
            sudo systemctl start lofi-pi-token-manager
            echo "✅ Service started and enabled for auto-start on boot"
            echo ""
            echo "Check status with: sudo systemctl status lofi-pi-token-manager"
        fi
    else
        echo "⚠️  Token check failed. You may need to re-authenticate:"
        echo "   python3 headless_spotify_auth.py"
    fi
else
    echo "⚠️  No tokens found. Please run the authentication first:"
    echo "   python3 headless_spotify_auth.py"
fi

echo ""
echo "Setup script completed successfully!"
