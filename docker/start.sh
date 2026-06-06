#!/bin/bash
set -e

# Railway injects $PORT; default to 80 locally
export PORT=${PORT:-80}

# Generate nginx config with the actual port
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Write app env vars to a file cron can source
# (cron does not inherit the container's process environment)
for var in ENRICH_MODE LOCAL_MODEL ANTHROPIC_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHANNEL_ID; do
    val="${!var:-}"
    [ -n "$val" ] && echo "export $var='$val'"
done > /app/.docker-env

# Write browser-facing Supabase config (anon key is safe to expose)
cat > /app/assets/data/config.js <<EOF
window.__VELUGO_CONFIG__ = {
  supabaseUrl: "${SUPABASE_URL:-}",
  supabaseAnonKey: "${SUPABASE_ANON_KEY:-}"
};
EOF

# Start cron daemon
service cron start

# On first boot (volume empty), seed data so the site is not blank
if [ ! -f /app/assets/data/india-headlines.js ]; then
    echo "=== First boot: running initial pipeline ==="
    source /app/.docker-env 2>/dev/null || true
    bash scripts/run-daily.sh || echo "Seed failed — site will update at next cron run"
fi

# Hand off to nginx (foreground, keeps container alive)
exec nginx -g 'daemon off;'
