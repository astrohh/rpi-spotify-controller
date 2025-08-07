#!/bin/bash
# Spotify Token Health Check Script
# Run this as a cron job to automatically maintain token health

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file
LOG_FILE="$SCRIPT_DIR/token_health.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Running Spotify token health check..."

# Check if Python environment is activated
if command -v python3 &> /dev/null; then
    # Run token health check
    python3 token_monitor.py --check
    
    if [ $? -eq 0 ]; then
        log "Token health check completed successfully"
    else
        log "Token health check failed"
        
        # Check if authentication failure notice exists
        if [ -f "auth_failure_notice.txt" ]; then
            log "Authentication failure detected - manual intervention required"
            
            # Optionally send email notification (if sendmail is configured)
            if command -v sendmail &> /dev/null && [ ! -z "$ADMIN_EMAIL" ]; then
                {
                    echo "Subject: LoFi Pi Authentication Failure"
                    echo "To: $ADMIN_EMAIL"
                    echo ""
                    echo "Your LoFi Pi requires manual re-authentication with Spotify."
                    echo "Please run 'python headless_spotify_auth.py' to fix this."
                    echo ""
                    echo "Timestamp: $(date)"
                } | sendmail "$ADMIN_EMAIL"
                log "Notification email sent to $ADMIN_EMAIL"
            fi
        fi
    fi
else
    log "ERROR: Python3 not found in PATH"
    exit 1
fi

log "Token health check completed"
