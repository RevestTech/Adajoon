#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Vault Initialization Script for Adajoon
#
# Run this ONCE after deploying Vault to Railway.
# It initializes Vault, unseals it, enables KV + AppRole,
# and stores all application secrets.
#
# Prerequisites:
#   - vault CLI installed (brew install hashicorp/tap/vault)
#   - Vault service running on Railway
#
# Usage:
#   export VAULT_ADDR="https://vault-production-xxxx.up.railway.app"
#   bash vault/init-vault.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

echo "=== Adajoon Vault Initialization ==="
echo "Vault address: ${VAULT_ADDR}"
echo ""

# ── Step 1: Initialize Vault ──
echo "Step 1: Initializing Vault..."
INIT_OUTPUT=$(vault operator init -key-shares=3 -key-threshold=2 -format=json)

# Save the init output (KEEP THIS SAFE!)
echo "$INIT_OUTPUT" > vault-init-keys.json
chmod 600 vault-init-keys.json

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  CRITICAL: Save vault-init-keys.json somewhere safe!    ║"
echo "║  It contains your unseal keys and root token.           ║"
echo "║  You need 2 of 3 unseal keys to unseal Vault.          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

UNSEAL_KEY_1=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[1]')
ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

# ── Step 2: Unseal Vault ──
echo "Step 2: Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"
echo "Vault unsealed."
echo ""

# ── Step 3: Authenticate ──
export VAULT_TOKEN="$ROOT_TOKEN"
echo "Step 3: Authenticated as root."
echo ""

# ── Step 4: Enable KV v2 secrets engine ──
echo "Step 4: Enabling KV v2 secrets engine..."
vault secrets enable -version=2 -path=secret kv 2>/dev/null || echo "  (KV engine already enabled)"
echo ""

# ── Step 5: Write secrets ──
echo "Step 5: Writing Adajoon secrets..."
echo "  Enter each secret value when prompted (or press Enter to skip):"
echo ""

read -rp "  DATABASE_URL: " DB_URL
read -rp "  REDIS_URL: " REDIS_URL_VAL
read -rp "  JWT_SECRET (min 32 chars): " JWT_SEC
read -rp "  GOOGLE_CLIENT_ID: " GOOGLE_CID
read -rp "  APPLE_CLIENT_ID: " APPLE_CID
read -rp "  SYNC_API_KEY: " SYNC_KEY
read -rp "  ANTHROPIC_API_KEY: " ANTHROPIC_KEY
read -rp "  STRIPE_SECRET_KEY: " STRIPE_SK
read -rp "  STRIPE_WEBHOOK_SECRET: " STRIPE_WH
read -rp "  STRIPE_PUBLISHABLE_KEY: " STRIPE_PK
read -rp "  WEBAUTHN_RP_ID [adajoon.com]: " WA_RPID
read -rp "  WEBAUTHN_ORIGIN [https://adajoon.com]: " WA_ORIGIN
read -rp "  CORS_ORIGINS [https://adajoon.com,https://www.adajoon.com]: " CORS

WA_RPID="${WA_RPID:-adajoon.com}"
WA_ORIGIN="${WA_ORIGIN:-https://adajoon.com}"
CORS="${CORS:-https://adajoon.com,https://www.adajoon.com}"

vault kv put secret/adajoon \
  DATABASE_URL="${DB_URL}" \
  REDIS_URL="${REDIS_URL_VAL}" \
  JWT_SECRET="${JWT_SEC}" \
  GOOGLE_CLIENT_ID="${GOOGLE_CID}" \
  APPLE_CLIENT_ID="${APPLE_CID}" \
  SYNC_API_KEY="${SYNC_KEY}" \
  ANTHROPIC_API_KEY="${ANTHROPIC_KEY}" \
  STRIPE_SECRET_KEY="${STRIPE_SK}" \
  STRIPE_WEBHOOK_SECRET="${STRIPE_WH}" \
  STRIPE_PUBLISHABLE_KEY="${STRIPE_PK}" \
  WEBAUTHN_RP_ID="${WA_RPID}" \
  WEBAUTHN_ORIGIN="${WA_ORIGIN}" \
  CORS_ORIGINS="${CORS}"

echo ""
echo "Secrets written to secret/adajoon"
echo ""

# ── Step 6: Enable AppRole auth ──
echo "Step 6: Setting up AppRole auth..."
vault auth enable approle 2>/dev/null || echo "  (AppRole already enabled)"

# Create policy
vault policy write adajoon-backend - <<EOF
path "secret/data/adajoon" {
  capabilities = ["read"]
}
path "secret/metadata/adajoon" {
  capabilities = ["read"]
}
EOF

# Create the role
vault write auth/approle/role/adajoon-backend \
  token_policies="adajoon-backend" \
  token_ttl=1h \
  token_max_ttl=24h \
  secret_id_ttl=0

# Fetch credentials
ROLE_ID=$(vault read -field=role_id auth/approle/role/adajoon-backend/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/adajoon-backend/secret-id)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  AppRole Credentials — set these on your Railway        ║"
echo "║  backend service as environment variables:              ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                         ║"
echo "║  VAULT_ADDR     = ${VAULT_ADDR}"
echo "║  VAULT_ROLE_ID  = ${ROLE_ID}"
echo "║  VAULT_SECRET_ID= ${SECRET_ID}"
echo "║                                                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "=== Initialization complete! ==="
echo ""
echo "Next steps:"
echo "  1. Store vault-init-keys.json in a SECURE location (password manager, etc.)"
echo "  2. Set VAULT_ADDR, VAULT_ROLE_ID, VAULT_SECRET_ID on your Railway backend"
echo "  3. Remove all other secret env vars from Railway backend"
echo "  4. Redeploy the backend"
echo ""
echo "To verify: curl \${VAULT_ADDR}/v1/sys/health"
