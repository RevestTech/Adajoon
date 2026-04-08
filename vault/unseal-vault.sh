#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Unseal Vault after a Railway container restart.
#
# Vault seals itself on every restart (by design).
# Run this script whenever the Vault container restarts.
#
# Usage:
#   export VAULT_ADDR="https://vault-production-xxxx.up.railway.app"
#   bash vault/unseal-vault.sh
#
# Or provide keys as arguments:
#   bash vault/unseal-vault.sh <key1> <key2>
# ─────────────────────────────────────────────────────────────
set -euo pipefail

echo "=== Unseal Vault ==="
echo "Vault address: ${VAULT_ADDR}"
echo ""

# Check current seal status
STATUS=$(vault status -format=json 2>/dev/null || echo '{"sealed": true}')
SEALED=$(echo "$STATUS" | jq -r '.sealed')

if [ "$SEALED" = "false" ]; then
    echo "Vault is already unsealed."
    exit 0
fi

echo "Vault is sealed. Providing unseal keys..."

if [ $# -ge 2 ]; then
    # Keys provided as arguments
    vault operator unseal "$1"
    vault operator unseal "$2"
else
    # Load from init keys file if available
    if [ -f vault-init-keys.json ]; then
        KEY1=$(jq -r '.unseal_keys_b64[0]' vault-init-keys.json)
        KEY2=$(jq -r '.unseal_keys_b64[1]' vault-init-keys.json)
        vault operator unseal "$KEY1"
        vault operator unseal "$KEY2"
    else
        # Interactive
        read -rsp "Unseal Key 1: " KEY1
        echo ""
        vault operator unseal "$KEY1"
        read -rsp "Unseal Key 2: " KEY2
        echo ""
        vault operator unseal "$KEY2"
    fi
fi

echo ""
echo "Vault unsealed successfully."
vault status
