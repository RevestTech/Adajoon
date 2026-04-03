#!/bin/bash
set -e

echo "🚀 Railway Deployment Script for Adajoon"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    brew install railway
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo ""
echo "📦 Step 1: Initialize Railway project"
railway init --name adajoon || echo "Project already initialized"

echo ""
echo "🗄️ Step 2: Adding PostgreSQL database..."
railway add --plugin postgresql || echo "Database already added"

echo ""
echo "🔑 Step 3: Setting environment variables..."

# Generate JWT secret if not exists
JWT_SECRET=$(openssl rand -hex 32)
railway variables set JWT_SECRET="$JWT_SECRET"

# Set required variables
railway variables set ENV=production

echo "✅ JWT_SECRET generated and set"
echo ""
echo "⚠️  MANUAL STEPS REQUIRED:"
echo "1. Get DATABASE_URL from Railway dashboard (auto-injected)"
echo "2. Set OAuth credentials:"
echo "   railway variables set GOOGLE_CLIENT_ID=your-id"
echo "   railway variables set APPLE_CLIENT_ID=your-id"
echo ""
echo "3. Set WebAuthn domain (after first deploy):"
echo "   railway variables set WEBAUTHN_RP_ID=your-app.up.railway.app"
echo "   railway variables set WEBAUTHN_ORIGIN=https://your-app.up.railway.app"
echo ""
echo "4. Optional - Set Stripe keys:"
echo "   railway variables set STRIPE_SECRET_KEY=sk_..."
echo "   railway variables set STRIPE_WEBHOOK_SECRET=whsec_..."
echo "   railway variables set STRIPE_PUBLISHABLE_KEY=pk_..."
echo ""

read -p "Press Enter when environment variables are set..."

echo ""
echo "🚀 Step 4: Deploying backend..."
railway up

echo ""
echo "🗄️ Step 5: Running database migrations..."
railway run alembic upgrade head

echo ""
echo "✅ Backend deployed successfully!"
echo ""
echo "📊 Get your deployment URL:"
railway domain
echo ""
echo "📝 Next steps:"
echo "1. Deploy worker service for stream validation (see RAILWAY_DEPLOYMENT.md)"
echo "2. Deploy frontend (separate Railway project or Vercel)"
echo "3. Monitor logs: railway logs -f"
echo ""
