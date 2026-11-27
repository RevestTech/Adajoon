#!/bin/sh
export PORT=${PORT:-80}
export BACKEND_URL=${BACKEND_URL:-http://backend.railway.internal:8080}

# nginx's proxy_pass resolves a literal hostname once, at config-load time,
# and then keeps using that IP for the life of the worker process. When
# Railway redeploys the backend service, its container gets a new internal
# IP - this nginx process has no way to find out, so it keeps sending
# requests into the void (connection refused/reset, or a hung connection
# until the proxy's own read timeout) until something restarts nginx.
# Fixing this for real means making nginx re-resolve on a short TTL instead
# of caching forever, which needs an explicit `resolver` directive pointing
# at a real DNS server - read the one this container's own network
# namespace already uses, so this works on Railway or any other host
# without hardcoding a provider-specific resolver IP.
DNS_RESOLVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)
case "$DNS_RESOLVER" in
  *:*) DNS_RESOLVER="[$DNS_RESOLVER]" ;; # nginx requires brackets around IPv6
esac
export DNS_RESOLVER=${DNS_RESOLVER:-127.0.0.11}

envsubst '${PORT} ${BACKEND_URL} ${DNS_RESOLVER}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
