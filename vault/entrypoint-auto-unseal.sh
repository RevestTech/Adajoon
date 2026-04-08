#!/bin/sh
set -e

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

# Wait for Vault to be reachable
echo "Waiting for Vault to start..."
RETRIES=0
while [ $RETRIES -lt 30 ]; do
    if vault status >/dev/null 2>&1; then
        break
    fi
    RETRIES=$((RETRIES + 1))
    sleep 1
done

if ! vault status >/dev/null 2>&1; then
    echo "ERROR: Vault did not start within 30 seconds"
    wait $VAULT_PID
    exit 1
fi

echo "Vault is up."

# Check if initialized
INIT_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.initialized' 2>/dev/null || echo "false")

if [ "$INIT_STATUS" = "false" ]; then
    echo "Vault is NOT initialized. Run init-vault.sh to initialize."
    echo "Vault is running and waiting for initialization..."
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

vault status
echo "Vault is ready."

# Wait for vault process (keep container alive)
wait $VAULT_PID
