#!/bin/sh
# NO set -e — vault status returns non-zero when uninitialized/sealed

PORT="${PORT:-8200}"

export VAULT_API_ADDR="http://0.0.0.0:${PORT}"
export VAULT_CLUSTER_ADDR="http://0.0.0.0:${PORT}"
export VAULT_ADDR="http://127.0.0.1:${PORT}"
export SKIP_SETCAP=1

mkdir -p /vault/data

# Update listener address to match Railway's PORT
sed -i "s/0.0.0.0:8200/0.0.0.0:${PORT}/g" /vault/config/vault-config.hcl

echo "Starting Vault on port ${PORT}..."

# Start Vault in background
vault server -config=/vault/config/vault-config.hcl &
VAULT_PID=$!

# Wait for Vault to be reachable (vault status exits 2 when not init, 1 when sealed — both mean "running")
echo "Waiting for Vault to start..."
RETRIES=0
while [ $RETRIES -lt 30 ]; do
    # Use curl to check if Vault is listening, since vault status returns non-zero when uninitialized
    if curl -s -o /dev/null http://127.0.0.1:${PORT}/v1/sys/health 2>/dev/null; then
        break
    fi
    # Also check with any HTTP response (Vault returns 501 when not initialized)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${PORT}/v1/sys/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        break
    fi
    RETRIES=$((RETRIES + 1))
    sleep 1
done

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${PORT}/v1/sys/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "000" ]; then
    echo "ERROR: Vault did not start within 30 seconds"
    wait $VAULT_PID
    exit 1
fi

echo "Vault is up (health HTTP $HTTP_CODE)."

# Check if initialized
INIT_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.initialized' 2>/dev/null || echo "false")

if [ "$INIT_STATUS" = "false" ]; then
    echo "============================================"
    echo "  Vault is NOT initialized."
    echo "  Run init-vault.sh to set up secrets."
    echo "  Vault is listening and waiting..."
    echo "============================================"
    wait $VAULT_PID
    exit 0
fi

# Auto-unseal if keys provided
SEAL_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.sealed' 2>/dev/null || echo "true")

if [ "$SEAL_STATUS" = "true" ] && [ -n "${VAULT_UNSEAL_KEYS:-}" ]; then
    echo "Auto-unsealing Vault..."
    KEY1=$(echo "$VAULT_UNSEAL_KEYS" | cut -d',' -f1)
    KEY2=$(echo "$VAULT_UNSEAL_KEYS" | cut -d',' -f2)

    if [ -n "$KEY1" ]; then
        vault operator unseal "$KEY1" >/dev/null 2>&1 && echo "  Key 1 applied." || echo "  Key 1 failed."
    fi
    if [ -n "$KEY2" ]; then
        vault operator unseal "$KEY2" >/dev/null 2>&1 && echo "  Key 2 applied." || echo "  Key 2 failed."
    fi

    NEW_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.sealed' 2>/dev/null || echo "unknown")
    if [ "$NEW_STATUS" = "false" ]; then
        echo "Vault unsealed successfully."
    else
        echo "WARNING: Vault is still sealed. Check your unseal keys."
    fi
elif [ "$SEAL_STATUS" = "true" ]; then
    echo "WARNING: Vault is sealed. Set VAULT_UNSEAL_KEYS env var to auto-unseal."
elif [ "$SEAL_STATUS" = "false" ]; then
    echo "Vault is already unsealed."
fi

vault status 2>/dev/null || true
echo "Vault is ready."

# Wait for vault process (keep container alive)
wait $VAULT_PID
