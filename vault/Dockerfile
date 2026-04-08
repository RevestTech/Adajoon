FROM hashicorp/vault:1.17

# Install jq for JSON parsing in entrypoint
RUN apk add --no-cache jq

# Copy Vault server config
COPY vault-config.hcl /vault/config/vault-config.hcl
COPY entrypoint-auto-unseal.sh /vault/entrypoint.sh

RUN chmod +x /vault/entrypoint.sh

# Vault listens on 8200 — Railway maps its PORT env var
EXPOSE 8200

# Railway health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD vault status -format=json 2>/dev/null | jq -e '.sealed == false' >/dev/null 2>&1 || exit 1

ENTRYPOINT ["/vault/entrypoint.sh"]
