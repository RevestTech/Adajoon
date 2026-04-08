# HashiCorp Vault Setup for Adajoon

Vault runs as its own Railway service and manages all application secrets. The backend connects to Vault on startup, fetches secrets, and caches them in memory. If Vault is temporarily unavailable, it falls back to environment variables.

## Architecture

```
Railway Project
├── vault       ← HashiCorp Vault (this guide)
│   ├── Raft storage on Railway volume
│   ├── Auto-unseal on container restart
│   └── KV v2: secret/adajoon (all secrets)
│
├── backend     ← FastAPI (connects to Vault via private network)
│   ├── VAULT_ADDR = http://vault.railway.internal:8080
│   ├── VAULT_ROLE_ID = ...
│   └── VAULT_SECRET_ID = ...
│
├── frontend    ← Nginx + React (no secrets needed)
├── postgres    ← PostgreSQL
└── redis       ← Redis
```

## Deploying Vault on Railway

### Step 1: Create the Vault service

In the Railway dashboard:

1. Click **New Service** → **GitHub Repo** (or "Empty Service" + connect repo)
2. Set the **Root Directory** to `vault/`
3. Under **Settings → Networking**, add a private domain: `vault` (this makes it accessible at `vault.railway.internal:8080`)
4. Under **Settings → Volumes**, mount a volume at `/vault/data` (for Raft storage persistence)
5. Don't set a public domain unless you need external CLI access during setup

### Step 2: Deploy and initialize

After the first deploy, Vault will be running but uninitialized.

**Temporarily add a public domain** to the Vault service (e.g., `vault-adajoon.up.railway.app`), then from your local machine:

```bash
# Install vault CLI if you haven't
brew install hashicorp/tap/vault

# Point to your Railway Vault
export VAULT_ADDR="https://vault-adajoon.up.railway.app"

# Run the initialization script
bash vault/init-vault.sh
```

The script will:
- Initialize Vault (generates 3 unseal keys, needs 2 to unseal)
- Unseal Vault
- Enable KV v2 secrets engine
- Prompt you for every secret value
- Enable AppRole auth
- Create a read-only policy for the backend
- Print the `VAULT_ROLE_ID` and `VAULT_SECRET_ID`

**Save the `vault-init-keys.json` file** in a secure location (password manager, not Git).

### Step 3: Configure auto-unseal

Vault re-seals itself on every container restart. To handle this automatically, set this env var on the Vault Railway service:

```
VAULT_UNSEAL_KEYS=<key1>,<key2>
```

Use 2 of the 3 unseal keys from `vault-init-keys.json`.

> **Note:** Storing unseal keys in env vars is a practical trade-off for Railway. For maximum security, use Vault's KMS auto-unseal (AWS KMS, GCP KMS, etc.) instead.

### Step 4: Configure the backend

Set these env vars on your **backend** Railway service:

| Variable | Value |
|---|---|
| `VAULT_ADDR` | `http://vault.railway.internal:8080` |
| `VAULT_ROLE_ID` | *(from init script output)* |
| `VAULT_SECRET_ID` | *(from init script output)* |

Then **remove all other secret env vars** from the backend (DATABASE_URL, JWT_SECRET, STRIPE_*, etc.) — they're now in Vault.

Keep only non-secret env vars:

| Keep on backend | Purpose |
|---|---|
| `VAULT_ADDR` | Vault connection |
| `VAULT_ROLE_ID` | Vault auth |
| `VAULT_SECRET_ID` | Vault auth |
| `ENV` | Environment name |
| `AI_SEARCH_ENABLED` | Feature toggle |
| `AI_MODEL` | Model selection |
| `ENABLE_INITIAL_SYNC` | Sync toggle |
| `LOG_LEVEL` | Logging |
| `PORT` | Railway port |

### Step 5: Remove the temporary public domain

Go back to the Vault Railway service settings and remove the public domain. Vault should only be accessible via Railway's private network (`vault.railway.internal:8080`).

### Step 6: Redeploy the backend

Redeploy the backend. You should see in the logs:

```
INFO  Vault authenticated via AppRole
INFO  Loaded 13 secrets from Vault (mount=secret, path=adajoon)
INFO  Vault active — 13 secrets loaded: DATABASE_URL, REDIS_URL, JWT_SECRET, ...
```

## Development Setup

For local development, you can either:

**Option A: Local Vault (recommended for testing Vault integration)**

```bash
# Start Vault dev server (in-memory, root token = "root")
vault server -dev -dev-root-token-id="root"

# In another terminal
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root"

vault kv put secret/adajoon \
  DATABASE_URL="postgresql+asyncpg://retv_user:retv_secret@localhost:5432/retv" \
  REDIS_URL="redis://localhost:6379" \
  JWT_SECRET="dev-jwt-secret-at-least-32-characters-long" \
  GOOGLE_CLIENT_ID="" \
  APPLE_CLIENT_ID="" \
  SYNC_API_KEY="" \
  ANTHROPIC_API_KEY="" \
  STRIPE_SECRET_KEY="" \
  STRIPE_WEBHOOK_SECRET="" \
  STRIPE_PUBLISHABLE_KEY="" \
  WEBAUTHN_RP_ID="localhost" \
  WEBAUTHN_ORIGIN="http://localhost:5173" \
  CORS_ORIGINS="http://localhost:5173,http://localhost:3000"

# Run backend with Vault
VAULT_ADDR="http://127.0.0.1:8200" VAULT_TOKEN="root" uvicorn app.main:app --reload
```

**Option B: Plain env vars (no Vault)**

Just don't set `VAULT_ADDR` and the backend uses env vars as before. The Vault integration is completely opt-in.

## Secrets Reference

All secrets stored at `secret/adajoon`:

| Key | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET` | JWT signing secret (min 32 chars) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `APPLE_CLIENT_ID` | Apple Sign-In client ID |
| `SYNC_API_KEY` | API key for sync/vault-refresh endpoints |
| `ANTHROPIC_API_KEY` | Claude API key for AI search |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
| `WEBAUTHN_RP_ID` | WebAuthn relying party ID |
| `WEBAUTHN_ORIGIN` | WebAuthn expected origin |
| `CORS_ORIGINS` | Comma-separated allowed origins |

## API Endpoints

### Check Vault status
```bash
curl https://adajoon.com/api/health/vault
```
Response when active:
```json
{"status": "active", "source": "vault", "secrets_loaded": 13, "keys": ["DAT***", "RED***", ...]}
```

### Refresh secrets after rotation
```bash
curl -X POST https://adajoon.com/api/vault/refresh \
  -H "X-Sync-Key: your-sync-key"
```

## Rotating Secrets

1. Update the secret in Vault (from your machine with CLI access):
   ```bash
   export VAULT_ADDR="https://vault-temp-domain.up.railway.app"
   export VAULT_TOKEN="<root-token>"
   vault kv patch secret/adajoon ANTHROPIC_API_KEY="sk-ant-new-key..."
   ```
2. Refresh the backend cache (no restart needed):
   ```bash
   curl -X POST https://adajoon.com/api/vault/refresh \
     -H "X-Sync-Key: your-sync-key"
   ```

## File Structure

```
vault/
├── Dockerfile                  # Vault container image
├── vault-config.hcl            # Vault server configuration (Raft storage)
├── entrypoint-auto-unseal.sh   # Main entrypoint with auto-unseal
├── entrypoint.sh               # Simple entrypoint (manual unseal)
├── init-vault.sh               # One-time initialization script
└── unseal-vault.sh             # Manual unseal helper
```

## Troubleshooting

**Backend logs "Vault not active — using environment variables"**
- Check that `VAULT_ADDR` is set on the backend
- Verify Vault is running: `curl http://vault.railway.internal:8080/v1/sys/health`
- Check `VAULT_ROLE_ID` and `VAULT_SECRET_ID` are correct

**Vault is sealed after restart**
- Verify `VAULT_UNSEAL_KEYS` env var is set on the Vault service
- Check Vault logs for unseal errors
- Manually unseal: `bash vault/unseal-vault.sh`

**"Failed to read secrets from Vault"**
- Check the Vault path: `vault kv get secret/adajoon`
- Verify the AppRole policy allows read access to `secret/data/adajoon`

**Volume data lost**
- Ensure a Railway volume is mounted at `/vault/data`
- If Raft data is lost, you need to re-initialize Vault
