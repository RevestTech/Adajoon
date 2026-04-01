#!/bin/sh
export PORT=${PORT:-80}
export BACKEND_URL=${BACKEND_URL:-http://backend:8000}
export RESOLVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf || echo "8.8.8.8")
echo "Using DNS resolver: $RESOLVER"
echo "Backend URL: $BACKEND_URL"
envsubst '${PORT} ${BACKEND_URL} ${RESOLVER}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
cat /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
