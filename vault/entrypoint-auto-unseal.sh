#!/bin/sh
# ─────────────────────────────────────────────────────────────
# Auto-unseal entrypoint for Railway deployment.
#
# Since Railway containers restart and Vault re-seals on restart,
# this entrypoint automatically unseals Vault using keys stored
# in the VAULT_UNSEAL_KEYS env var (comma-separated).
#
# Set on Railway:
#   VAULT_UNSEAL_KEYS="key1,key2"
#
# NOTE: Storing unseal keys in env vars is a trade-off.
# For higher security, use Vault's Transit auto-unseal or
# cloud KMS auto-unseal (AWS KMS, GCP KMS, Azure Key Vault).
# ─────────────────────────────────────────────────────────────
set -e

export VAULT_API_ADDR="http://0.0.0.0:${PORT:-8200}"
export VAULT_CLUSTER_ADDR="http://0.0.0.0:${PORT:-8200}"
export VAULT_ADDR="http://127.0.0.1:${PORT:-8200}"

mkdir -p /vault/data

# Start Vault in background
vault server -config=/vault/config/vault-config.hcl &
VAULT_PID=$!

# Wait for Vault to start
echo "Waiting for Vault to start..."
for i in $(seq 1 30); do
    if vault status -format=json >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Check if Vault needs initialization
INIT_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.initialized' 2>/dev/null || echo "false")

if [ "$INIT_STATUS" = "false" ]; then
    echo "Vault is not initialized. Run init-vault.sh first."
    echo "Keeping Vault running for initialization..."
    wait $VAULT_PID
    exit 0
fi

# Auto-unseal if keys are provided
SEAL_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.sealed' 2>/dev/null || echo "true")

if [ "$SEAL_STATUS" = "true" ] && [ -n "${VAULT_UNSEAL_KEYS:-}" ]; then
    echo "Auto-unsealing Vault..."
    IFS=',' read -r KEY1 KEY2 REST <<EOF
${VAULT_UNSEAL_KEYS}
EOF

    if [ -n "$KEY1" ]; then
        vault operator unseal "$KEY1" >/dev/null 2>&1 || true
    fi
    if [ -n "$KEY2" ]; then
        vault operator unseal "$KEY2" >/dev/null 2>&1 || true
    fi

    NEW_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.sealed' 2>/dev/null || echo "unknown")
    if [ "$NEW_STATUS" = "false" ]; then
        echo "Vault unsealed successfully."
    else
        echo "WARNING: Vault is still sealed. Check unseal keys."
    fi
elif [ "$SEAL_STATUS" = "true" ]; then
    echo "WARNING: Vault is sealed and no VAULT_UNSEAL_KEYS provided."
    echo "Set VAULT_UNSEAL_KEYS env var or unseal manually."
fi

# Wait for Vault process
wait $VAULT_PID
