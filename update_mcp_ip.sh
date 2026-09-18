#!/bin/bash
# Updates OpenClaw config with current MCP server IP after Docker restart

IP=$(docker inspect peppi-mcp | grep '"IPAddress"' | grep -v '""' | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
echo "MCP IP: $IP"
python3 -c "
import json
with open('/home/vboxuser/.openclaw/openclaw.json', 'r') as f:
    config = json.load(f)
config['mcp']['servers']['tutor']['url'] = 'http://$IP:8000/sse'
with open('/home/vboxuser/.openclaw/openclaw.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Updated URL to http://$IP:8000/sse')
"
cd ~/openclaw && docker compose exec openclaw-gateway node dist/index.js mcp reload