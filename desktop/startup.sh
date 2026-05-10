#!/bin/bash
set -e

echo "=== AI Agent Desktop Environment ==="
echo "VNC Port: ${VNC_PORT:-5900}"
echo "noVNC Port: ${NOVNC_PORT:-6080}"
echo "Code Server Port: 8443"
echo "Resolution: ${RESOLUTION:-1920x1080x24}"

# Create log directory
mkdir -p /var/log/supervisor

# Set up XFCE defaults for agent user
su - agent -c "mkdir -p ~/.config/xfce4/xfconf/xfce-perchannel-xml"

# Start supervisor (manages VNC, noVNC, code-server)
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
