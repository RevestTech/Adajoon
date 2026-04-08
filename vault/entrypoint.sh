#!/bin/sh
set -e

# Railway provides PORT env var — default to 8200
export VAULT_API_ADDR="http://0.0.0.0:${PORT:-8200}"
export VAULT_CLUSTER_ADDR="http://0.0.0.0:${PORT:-8200}"

# Ensure data directory exists
mkdir -p /vault/data

# Start Vault server
exec vault server -config=/vault/config/vault-config.hcl
