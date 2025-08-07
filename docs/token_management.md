# Automated Spotify Token Management

This document explains how LoFi Pi handles Spotify authentication tokens automatically to minimize manual intervention on your headless Raspberry Pi.

## Overview

Spotify access tokens expire every hour and need to be refreshed using a refresh token. The refresh token itself can also expire (typically after some weeks/months), requiring manual re-authentication. This system provides multiple layers of automation to handle these scenarios.

## Components

### 1. Enhanced SpotifyAPI (`spotify_api.py`)

- **Automatic token refresh**: Automatically refreshes expired access tokens
- **Token validation**: Tests tokens before use to catch invalid tokens early
- **Backup token system**: Maintains backup copies of working tokens
- **Graceful degradation**: Provides helpful error messages when authentication fails

### 2. Headless Authentication (`headless_spotify_auth.py`)

Run this script when refresh tokens expire:

```bash
python headless_spotify_auth.py
```

This generates a URL you can open on ANY device (phone, computer, etc.) to re-authenticate. No browser needed on the Raspberry Pi itself.

### 3. Token Monitor (`token_monitor.py`)

Proactive monitoring service with two modes:

**Single Check:**

```bash
python token_monitor.py --check
```

**Continuous Monitoring:**

```bash
python token_monitor.py --monitor
```

### 4. Automated Health Checks (`check_token_health.sh`)

Bash script for cron jobs that:

- Runs token health checks
- Logs results
- Creates notification files when manual intervention is needed
- Optionally sends email notifications

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initial Authentication

If you haven't already, run the initial setup:

```bash
python headless_spotify_auth.py
```

### 3. Set Up Automated Monitoring (Optional)

Add to your crontab to check tokens every hour:

```bash
crontab -e
```

Add this line:

```
0 * * * * /home/pi/lofi-pi/check_token_health.sh
```

### 4. Configure Email Notifications (Optional)

Set environment variable for email notifications:

```bash
export ADMIN_EMAIL="your-email@example.com"
```

## How It Works

### Normal Operation

1. LoFi Pi starts and loads existing tokens
2. If tokens are expired, they're automatically refreshed
3. If refresh fails, the system continues with limited functionality
4. Periodic health checks ensure tokens stay valid

### When Refresh Tokens Expire

1. System detects refresh token failure
2. Creates `auth_failure_notice.txt` file
3. LoFi Pi continues running but shows "Auth Required" message
4. Automated retries attempt re-authentication periodically
5. Admin can run `headless_spotify_auth.py` to fix authentication

### Recovery Process

1. Run `python headless_spotify_auth.py`
2. Open the provided URL on any device with a browser
3. Complete Spotify authorization
4. Copy the authorization code back to the Pi
5. System automatically resumes normal operation

## File Structure

```
spotify_tokens.json           # Main token file
spotify_tokens_backup.json    # Backup token file
auth_failure_notice.txt       # Created when manual auth needed
token_monitor.log            # Token monitoring logs
token_health.log             # Health check logs
```

## Troubleshooting

### "Auth Failed" on Display

1. Check if `auth_failure_notice.txt` exists
2. Run `python headless_spotify_auth.py`
3. Follow the re-authentication process

### Tokens Keep Expiring

- Ensure your Spotify app credentials are correct
- Check that your redirect URI matches exactly
- Verify system clock is accurate (important for token expiry)

### Cron Job Not Working

- Check cron logs: `grep CRON /var/log/syslog`
- Ensure script has execute permissions
- Verify Python path in script

## Manual Recovery

If all else fails, you can always manually re-authenticate:

1. On a computer, run the original `setup_spotify_auth.py`
2. Copy the generated `spotify_tokens.json` to your Raspberry Pi
3. Restart LoFi Pi

## Security Notes

- Token files contain sensitive authentication data
- Keep backup tokens secure
- Consider encrypting tokens if storing on shared systems
- Regularly rotate your Spotify app credentials

## Advanced Configuration

### Custom Refresh Intervals

Edit `token_monitor.py` to change check frequency:

```python
schedule.every(30).minutes.do(self.run_check)  # Default: 30 minutes
```

### Custom Retry Logic

Edit `main.py` to adjust retry behavior:

```python
max_retries = 10  # Number of retry cycles
retry_interval = 2400  # Retry every 2 minutes (2400 * 0.05s)
```
