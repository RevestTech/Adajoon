FROM hashicorp/vault:1.17

# Install jq for JSON parsing in entrypoint
RUN apk add --no-cache jq curl

# Switch to root to set up files
USER root

# Copy Vault server config (paths relative to vault/ build context)
COPY vault-config.hcl /vault/config/vault-config.hcl
COPY entrypoint-auto-unseal.sh /vault/entrypoint.sh

RUN chmod +x /vault/entrypoint.sh && \
    mkdir -p /vault/data && \
    chown -R vault:vault /vault/config /vault/data /vault/entrypoint.sh

# Vault listens on 8200 — Railway maps its PORT env var
EXPOSE 8200

# Run as root so we can bind to any port Railway assigns
ENTRYPOINT ["/vault/entrypoint.sh"]
