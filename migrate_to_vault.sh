#!/bin/bash
set -euo pipefail

# Adajoon Secrets Migration to railway-vault
# This script helps you migrate secrets from Railway env vars to the centralized vault

echo "═══════════════════════════════════════════════════════════"
echo "  Adajoon → railway-vault Migration"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Vault configuration
export VAULT_URL="${VAULT_URL:-https://kmac-vault-production.up.railway.app}"
export VAULT_TOKEN="${VAULT_TOKEN:-$(cat ~/railway-vault-token.txt 2>/dev/null || echo '')}"

if [ -z "$VAULT_TOKEN" ]; then
    echo "❌ Error: VAULT_TOKEN not found"
    echo ""
    echo "Please set it:"
    echo "  export VAULT_TOKEN=\"MC/0uklic3axGOpOPlWaXhnxz+eSeKuHnS+dudoEt+8=\""
    echo ""
    exit 1
fi

echo "✅ Vault URL: $VAULT_URL"
echo "✅ Vault Token: ${VAULT_TOKEN:0:10}..."
echo ""

# Function to add secret to vault
add_secret() {
    local key="$1"
    local value="$2"
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $key (empty value)"
        return
    fi
    
    echo -n "  Adding adajoon:$key... "
    
    response=$(curl -s -X POST "$VAULT_URL/set" \
        -H "Authorization: Bearer $VAULT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"key\":\"adajoon:$key\",\"value\":\"$value\"}")
    
    if echo "$response" | grep -q '"ok":true'; then
        echo "✅"
    else
        echo "❌"
        echo "  Error: $response"
    fi
}

echo "📝 Step 1: Get Your Current Secrets from Railway"
echo ""
echo "Go to Railway Dashboard → Adajoon Backend → Variables"
echo "Copy the values and paste them when prompted below."
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Enter Your Secrets (or press Enter to skip)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# JWT Secret
echo -n "JWT_SECRET (min 32 chars): "
read -r JWT_SECRET
if [ -n "$JWT_SECRET" ]; then
    add_secret "jwt_secret" "$JWT_SECRET"
fi

# OAuth
echo -n "GOOGLE_CLIENT_ID: "
read -r GOOGLE_CLIENT_ID
if [ -n "$GOOGLE_CLIENT_ID" ]; then
    add_secret "google_client_id" "$GOOGLE_CLIENT_ID"
fi

echo -n "APPLE_CLIENT_ID: "
read -r APPLE_CLIENT_ID
if [ -n "$APPLE_CLIENT_ID" ]; then
    add_secret "apple_client_id" "$APPLE_CLIENT_ID"
fi

# AI
echo -n "ANTHROPIC_API_KEY: "
read -r ANTHROPIC_API_KEY
if [ -n "$ANTHROPIC_API_KEY" ]; then
    add_secret "anthropic_api_key" "$ANTHROPIC_API_KEY"
fi

# Stripe
echo -n "STRIPE_SECRET_KEY: "
read -r STRIPE_SECRET_KEY
if [ -n "$STRIPE_SECRET_KEY" ]; then
    add_secret "stripe_secret_key" "$STRIPE_SECRET_KEY"
fi

echo -n "STRIPE_WEBHOOK_SECRET: "
read -r STRIPE_WEBHOOK_SECRET
if [ -n "$STRIPE_WEBHOOK_SECRET" ]; then
    add_secret "stripe_webhook_secret" "$STRIPE_WEBHOOK_SECRET"
fi

echo -n "STRIPE_PUBLISHABLE_KEY: "
read -r STRIPE_PUBLISHABLE_KEY
if [ -n "$STRIPE_PUBLISHABLE_KEY" ]; then
    add_secret "stripe_publishable_key" "$STRIPE_PUBLISHABLE_KEY"
fi

# Internal API
echo -n "SYNC_API_KEY: "
read -r SYNC_API_KEY
if [ -n "$SYNC_API_KEY" ]; then
    add_secret "sync_api_key" "$SYNC_API_KEY"
fi

# WebAuthn
echo -n "WEBAUTHN_RP_ID (e.g., adajoon.com): "
read -r WEBAUTHN_RP_ID
if [ -n "$WEBAUTHN_RP_ID" ]; then
    add_secret "webauthn_rp_id" "$WEBAUTHN_RP_ID"
fi

echo -n "WEBAUTHN_ORIGIN (e.g., https://www.adajoon.com): "
read -r WEBAUTHN_ORIGIN
if [ -n "$WEBAUTHN_ORIGIN" ]; then
    add_secret "webauthn_origin" "$WEBAUTHN_ORIGIN"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Verifying Secrets in Vault"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Secrets stored in vault:"
curl -s -H "Authorization: Bearer $VAULT_TOKEN" "$VAULT_URL/list" | \
    python3 -m json.tool | grep "adajoon:" | sed 's/"//g' | sed 's/,//g' | sed 's/^[[:space:]]*/  /'

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Migration Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Update Railway environment variables:"
echo "   railway variables set VAULT_URL=\"http://kmac-vault.railway.internal:9999\""
echo "   railway variables set VAULT_TOKEN=\"$VAULT_TOKEN\""
echo ""
echo "2. Remove old secret env vars from Railway dashboard"
echo "   (Keep: DATABASE_URL, REDIS_URL, CORS_ORIGINS, ENV, etc.)"
echo ""
echo "3. Deploy:"
echo "   git add -A"
echo "   git commit -m \"feat: migrate to railway-vault for secrets\""
echo "   git push"
echo ""
echo "4. Monitor deployment:"
echo "   railway logs -f"
echo ""
