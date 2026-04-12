# Railway Secrets Configuration

All secrets are managed via Railway's built-in environment variables. No external vault needed.

## Why Railway Env Vars?

Railway provides enterprise-grade secrets management out of the box:
- ✅ **Encrypted at rest** - AES-256 encryption
- ✅ **Encrypted in transit** - TLS everywhere
- ✅ **Access control** - Team permissions
- ✅ **Audit logs** - Track all changes
- ✅ **Service sharing** - Share variables between services
- ✅ **Zero maintenance** - No additional service to run
- ✅ **Zero cost** - Included in Railway pricing

## Required Environment Variables

### Backend Service

Set these in Railway dashboard → Backend service → Variables:

```bash
# Database (provided by Railway PostgreSQL service)
DATABASE_URL=${POSTGRES_URL}  # Railway reference variable

# Redis (provided by Railway Redis service)
REDIS_URL=${REDIS_URL}  # Railway reference variable

# JWT Authentication (generate with: openssl rand -hex 32)
JWT_SECRET=<64-character-hex-string>

# OAuth Providers
GOOGLE_CLIENT_ID=<your-google-client-id>
APPLE_CLIENT_ID=<your-apple-client-id>

# WebAuthn (Passkeys)
WEBAUTHN_RP_ID=adajoon.com
WEBAUTHN_ORIGIN=https://www.adajoon.com

# AI Search (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-...
AI_SEARCH_ENABLED=true
AI_MODEL=claude-sonnet-4-20250514

# Stripe Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Internal API Key (generate with: openssl rand -hex 32)
SYNC_API_KEY=<64-character-hex-string>

# CORS (comma-separated)
CORS_ORIGINS=https://adajoon.com,https://www.adajoon.com

# Environment
ENV=production
LOG_LEVEL=INFO
JSON_LOGS=true
```

### Worker Service

Worker shares all variables with backend via Railway's "Reference" feature:
1. Go to Worker service → Variables
2. Click "Add Reference" for each variable
3. Select `backend` service and the variable name

This ensures both services use identical secrets without duplication.

### Frontend Service

Frontend only needs non-secret configuration:

```bash
BACKEND_URL=http://backend.railway.internal:8080
PORT=80
```

## Variable References (Railway Feature)

Railway's **variable references** eliminate duplication:

```bash
# Backend service defines:
DATABASE_URL=${POSTGRES_URL}

# Worker service references it:
DATABASE_URL=${backend.DATABASE_URL}
```

Benefits:
- Single source of truth
- Automatic updates when backend variable changes
- No secrets duplication

## Generating Secrets

```bash
# JWT Secret (64 hex characters = 256 bits)
openssl rand -hex 32

# Sync API Key (64 hex characters)
openssl rand -hex 32

# Stripe Webhook Secret
# Get from Stripe Dashboard → Webhooks → Add endpoint
```

## Development Setup

For local development, create `.env` file:

```bash
# backend/.env
ENV=development
DATABASE_URL=postgresql+asyncpg://retv:retv_secret@localhost:5432/retv
REDIS_URL=redis://localhost:6379
JWT_SECRET=dev-jwt-secret-change-in-production-min-32-chars
GOOGLE_CLIENT_ID=
APPLE_CLIENT_ID=
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PUBLISHABLE_KEY=
WEBAUTHN_RP_ID=localhost
WEBAUTHN_ORIGIN=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Never commit `.env` to git (already in `.gitignore`).

## Security Best Practices

1. **Rotate secrets regularly** - Change JWT_SECRET, API keys quarterly
2. **Use different secrets per environment** - Dev/staging/prod should have unique keys
3. **Never log secrets** - Already handled by FastAPI
4. **Monitor access** - Check Railway audit logs monthly
5. **Principle of least privilege** - Only grant team members necessary access

## Migration from Vault

If migrating from the old Vault setup:

1. **Extract secrets from Vault**:
   ```bash
   export VAULT_ADDR="https://vault-temp.up.railway.app"
   export VAULT_TOKEN="<root-token>"
   vault kv get -format=json secret/adajoon | jq .data.data
   ```

2. **Add each secret to Railway**:
   - Railway Dashboard → Backend service → Variables
   - Copy values from Vault output
   - Click "Add" for each variable

3. **Remove Vault service**:
   - Railway Dashboard → Vault service → Settings → Delete service

4. **Deploy updated backend** (already done in this commit)

## Troubleshooting

**Backend fails to start with "JWT_SECRET must be set"**
- Check Railway dashboard → Backend → Variables
- Ensure JWT_SECRET exists and is at least 32 characters

**Backend connects to wrong database**
- Verify DATABASE_URL uses `${POSTGRES_URL}` reference
- Check PostgreSQL service is running

**CORS errors on frontend**
- Add your domain to CORS_ORIGINS
- Format: `https://domain1.com,https://domain2.com` (no spaces)

**Stripe webhooks fail**
- Verify STRIPE_WEBHOOK_SECRET matches Stripe dashboard
- Check webhook URL is `https://www.adajoon.com/api/webhooks/stripe`
