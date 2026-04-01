#!/bin/sh
export PORT=${PORT:-80}
export BACKEND_URL=${BACKEND_URL:-http://backend:8000}
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
