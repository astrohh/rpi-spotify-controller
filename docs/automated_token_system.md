# Automated Spotify Token Management System

## Overview

This system provides **fully automated** Spotify token management for your LoFi Pi, eliminating the need for manual token refresh operations. Once set up, your device will maintain Spotify connectivity indefinitely without user intervention.

## 🚀 Quick Setup

### 1. Install the System

```bash
./setup_auto_tokens.sh
```

### 2. Initial Authentication (One-time)

```bash
python3 headless_spotify_auth.py
```

Follow the instructions to authenticate using any device with a browser.

### 3. Start Automatic Management

```bash
sudo systemctl enable lofi-pi-token-manager
sudo systemctl start lofi-pi-token-manager
```

**That's it!** Your tokens will now be managed automatically.

## 🔧 How It Works

### Automatic Token Refresh

- **Proactive refresh**: Tokens are refreshed 10 minutes before expiry
- **Multiple retry strategies**: Uses exponential backoff and fallback methods
- **Session persistence**: Maintains connection state across restarts
- **Error recovery**: Automatically recovers from network and API errors

### Background Services

#### 1. Auto Token Manager (`auto_token_manager.py`)

- Runs continuously as a systemd service
- Monitors token health every 5 minutes
- Automatically refreshes tokens before expiry
- Logs all activities for debugging

#### 2. Health Check Cron Job (`check_token_health.sh`)

- Runs every 30 minutes via cron
- Provides redundant monitoring
- Creates notifications when manual intervention is needed
- Optional email alerts

#### 3. Enhanced SpotifyAPI

- Persistent HTTP sessions for better reliability
- Multiple authentication fallback strategies
- Client credentials flow for basic functionality
- Backup token system

### Recovery Strategies

When refresh tokens expire (rare, but happens after weeks/months):

1. **Automatic Fallback**: System tries client credentials for basic functionality
2. **Backup Tokens**: Attempts to use backup token files
3. **Device Discovery**: Looks for active Spotify sessions
4. **Graceful Degradation**: Continues running with limited functionality
5. **Clear Instructions**: Provides specific steps to restore full functionality

## 📊 Monitoring and Status

### Check Token Status

```bash
python3 auto_token_manager.py --status
```

### View Service Logs

```bash
journalctl -u lofi-pi-token-manager -f
```

### Manual Token Check

```bash
python3 auto_token_manager.py --check
```

### View Auto-generated Status

```bash
cat auto_token_status.json
```

## 🛠️ Configuration

### Service Management

```bash
# Start/stop the service
sudo systemctl start lofi-pi-token-manager
sudo systemctl stop lofi-pi-token-manager

# Enable/disable auto-start on boot
sudo systemctl enable lofi-pi-token-manager
sudo systemctl disable lofi-pi-token-manager

# Check service status
sudo systemctl status lofi-pi-token-manager
```

### Timing Configuration

Edit `auto_token_manager.py` to adjust timing:

```python
self.check_interval = 300  # Check every 5 minutes
self.refresh_early_seconds = 600  # Refresh 10 minutes before expiry
```

### Cron Job Configuration

Edit crontab to change health check frequency:

```bash
crontab -e
# Change from every 30 minutes to every hour:
# 0 * * * * /home/pi/lofi-pi/check_token_health.sh
```

## 🔍 Troubleshooting

### Service Not Starting

```bash
# Check service status
sudo systemctl status lofi-pi-token-manager

# View detailed logs
journalctl -u lofi-pi-token-manager --no-pager
```

### Authentication Failures

1. Check if initial authentication was completed:

   ```bash
   ls -la spotify_tokens.json
   ```

2. Test token validity:

   ```bash
   python3 auto_token_manager.py --status
   ```

3. Re-authenticate if needed:
   ```bash
   python3 headless_spotify_auth.py
   ```

### High CPU/Memory Usage

The service is designed to be lightweight, but if you notice issues:

```bash
# Check resource usage
systemctl status lofi-pi-token-manager
```

Adjust check intervals in `auto_token_manager.py` if needed.

## 📁 Generated Files

The system creates several files for monitoring and state management:

- `spotify_tokens.json` - Main token file
- `spotify_tokens_backup.json` - Backup tokens
- `spotify_session.json` - Session state
- `auto_token_status.json` - Current status
- `auto_token.log` - Service logs
- `token_health.log` - Health check logs
- `auth_failure_notice.txt` - Created when manual auth needed

## 🔒 Security Considerations

- Token files contain sensitive data - ensure proper file permissions
- The systemd service runs with restricted privileges
- Logs may contain authentication details - rotate regularly
- Consider encrypting token files for added security

## 🆘 Emergency Recovery

If everything fails and you need to start fresh:

1. **Stop the service**:

   ```bash
   sudo systemctl stop lofi-pi-token-manager
   ```

2. **Clear all tokens**:

   ```bash
   rm -f spotify_tokens*.json spotify_session.json
   ```

3. **Re-authenticate**:

   ```bash
   python3 headless_spotify_auth.py
   ```

4. **Restart the service**:
   ```bash
   sudo systemctl start lofi-pi-token-manager
   ```

## 📈 Benefits of This System

✅ **Zero manual intervention** - Tokens refresh automatically
✅ **Redundant monitoring** - Multiple layers of health checks
✅ **Graceful degradation** - Continues working even with auth issues
✅ **Comprehensive logging** - Full audit trail of all activities
✅ **Easy recovery** - Clear instructions when manual action is needed
✅ **Production ready** - Designed for 24/7 operation
✅ **Headless friendly** - No GUI or browser required on the Pi

This system transforms your LoFi Pi from requiring periodic manual token management to a fully autonomous music controller that maintains its Spotify connection indefinitely.
