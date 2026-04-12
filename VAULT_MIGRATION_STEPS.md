# Adajoon railway-vault Migration - Next Steps

**Status:** ✅ Code changes complete and committed  
**Time to complete:** 15-20 minutes  
**Risk:** Low (easy rollback)

---

## ✅ What's Done

- ✅ Vault client copied to `backend/app/vault_client.py`
- ✅ Config updated to fetch secrets from railway-vault
- ✅ Migration script created at `migrate_to_vault.sh`
- ✅ Changes committed to git

---

## 🎯 What You Need to Do (3 Steps)

### Step 1: Migrate Your Secrets to Vault (5 min)

Run the migration script to copy your current Railway secrets to the vault:

```bash
cd ~/Projects/Adajoon

# Run interactive migration
./migrate_to_vault.sh
```

**What it will ask for:**
1. JWT_SECRET
2. GOOGLE_CLIENT_ID
3. APPLE_CLIENT_ID
4. ANTHROPIC_API_KEY
5. STRIPE_SECRET_KEY
6. STRIPE_WEBHOOK_SECRET
7. STRIPE_PUBLISHABLE_KEY
8. SYNC_API_KEY
9. WEBAUTHN_RP_ID
10. WEBAUTHN_ORIGIN

**Where to get these values:**
- Railway Dashboard → Adajoon Project → Backend Service → Variables tab
- Copy/paste each value when prompted

**Don't have secrets yet?** Press Enter to skip each one (for development).

---

### Step 2: Update Railway Environment Variables (5 min)

**Add vault connection variables:**

```bash
# Link to Adajoon backend service
cd ~/Projects/Adajoon
railway link

# Add vault connection
railway variables set VAULT_URL="http://kmac-vault.railway.internal:9999"
railway variables set VAULT_TOKEN="MC/0uklic3axGOpOPlWaXhnxz+eSeKuHnS+dudoEt+8="
```

**Keep these existing variables:**
- ✅ `DATABASE_URL` (Railway service reference)
- ✅ `REDIS_URL` (Railway service reference)
- ✅ `CORS_ORIGINS` (not a secret)
- ✅ `ENV` (not a secret)
- ✅ `JSON_LOGS` (not a secret)
- ✅ `AI_SEARCH_ENABLED` (not a secret)
- ✅ `AI_MODEL` (not a secret)
- ✅ `WEBAUTHN_RP_NAME` (not a secret)

**Remove these (now in vault):**
```bash
# After confirming vault works, remove these
railway variables delete JWT_SECRET
railway variables delete GOOGLE_CLIENT_ID
railway variables delete APPLE_CLIENT_ID
railway variables delete ANTHROPIC_API_KEY
railway variables delete STRIPE_SECRET_KEY
railway variables delete STRIPE_WEBHOOK_SECRET
railway variables delete STRIPE_PUBLISHABLE_KEY
railway variables delete SYNC_API_KEY
railway variables delete WEBAUTHN_RP_ID
railway variables delete WEBAUTHN_ORIGIN
```

**⚠️ Wait!** Delete these AFTER confirming the vault works (Step 3).

---

### Step 3: Deploy and Test (10 min)

**Deploy to Railway:**

```bash
cd ~/Projects/Adajoon

# Push changes (Railway auto-deploys)
git push origin main

# Monitor deployment
railway logs -f
```

**What to look for in logs:**
- ✅ "Connected to vault" or successful startup
- ✅ No errors about missing secrets
- ✅ Application starts normally

**Test the API:**

```bash
# Health check
curl https://your-adajoon-backend.railway.app/health

# Test an endpoint that uses secrets
# (e.g., login, Stripe payment, AI search)
```

**If everything works:**
- ✅ Remove old secret env vars (commands above)
- ✅ Celebrate! 🎉

**If something fails:**
- See "Rollback Plan" below

---

## 🔄 Worker Service (Optional)

If you have a worker service, update it too:

```bash
# Add vault connection (references backend)
railway variables set VAULT_URL='${backend.VAULT_URL}' --service worker
railway variables set VAULT_TOKEN='${backend.VAULT_TOKEN}' --service worker
```

Worker will automatically use same vault configuration.

---

## 📊 Before vs After

### Before (Current)
```
Railway Dashboard → Backend Variables (visible to anyone)
├── DATABASE_URL = postgresql://... ❌ Visible
├── JWT_SECRET = abc123... ❌ Visible
├── STRIPE_SECRET_KEY = sk_live_... ❌ Visible
└── 10+ more secrets ❌ All visible
```

### After (Target)
```
Railway Dashboard → Backend Variables
├── VAULT_URL = http://kmac-vault... ✅
├── VAULT_TOKEN = MC/0ukl... ✅ (only secret)
├── DATABASE_URL = ${POSTGRES_URL} ✅ (reference)
└── CORS_ORIGINS = ... ✅ (not secret)

railway-vault Service → Encrypted Storage
├── adajoon:jwt_secret ✅ Encrypted, not visible
├── adajoon:stripe_secret_key ✅ Encrypted
└── 10+ secrets ✅ All encrypted
```

---

## 🚨 Rollback Plan

If deployment fails:

```bash
# 1. Revert code changes
cd ~/Projects/Adajoon
git revert HEAD
git push

# 2. Re-add secrets to Railway (if you deleted them)
railway variables set JWT_SECRET="..."
railway variables set STRIPE_SECRET_KEY="..."
# ...etc

# 3. Railway auto-deploys reverted code

# Time to rollback: < 5 minutes
```

---

## ✅ Success Checklist

- [ ] Ran `./migrate_to_vault.sh` and migrated secrets
- [ ] Verified secrets in vault: `curl -H "Authorization: Bearer $VAULT_TOKEN" https://kmac-vault-production.up.railway.app/list`
- [ ] Added `VAULT_URL` to Railway
- [ ] Added `VAULT_TOKEN` to Railway
- [ ] Pushed code to Railway
- [ ] Deployment successful (no errors in logs)
- [ ] Health endpoint works
- [ ] API endpoints work
- [ ] Removed old secret env vars from Railway
- [ ] Tested secret rotation (optional)

---

## 🎓 Pro Tips

### Test Secret Rotation

```bash
# Update a secret in vault
export VAULT_TOKEN="MC/0uklic3axGOpOPlWaXhnxz+eSeKuHnS+dudoEt+8="
export VAULT_URL="https://kmac-vault-production.up.railway.app"

curl -X POST $VAULT_URL/set \
  -H "Authorization: Bearer $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"adajoon:jwt_secret","value":"new-secret-value"}'

# Restart service to pick up new secret
railway restart

# No code changes needed!
```

### View All Your Secrets

```bash
curl -H "Authorization: Bearer $VAULT_TOKEN" \
  https://kmac-vault-production.up.railway.app/list | jq
```

### Development Setup

For local development, secrets work from `.env` file:

```bash
# backend/.env (local only)
JWT_SECRET=dev-jwt-secret-min-32-chars
ANTHROPIC_API_KEY=sk-ant-dev-key
# ...etc
```

Config automatically falls back to env vars if vault not configured.

---

## 📞 Need Help?

**Vault not connecting?**
- Check `VAULT_URL` and `VAULT_TOKEN` are set in Railway
- Verify vault is running: `curl https://kmac-vault-production.up.railway.app/health`
- Check logs: `railway logs`

**Secrets not found?**
- List vault keys: `curl -H "Authorization: Bearer $VAULT_TOKEN" $VAULT_URL/list`
- Verify secret names match: `adajoon:jwt_secret` not `JWT_SECRET`

**Still have issues?**
- Check railway-vault docs: `~/Projects/railway-vault/ADAJOON_MIGRATION.md`
- Review comparison guide: `~/Projects/railway-vault/COMPARISON.md`

---

## 🚀 Ready?

**Next command:**

```bash
cd ~/Projects/Adajoon
./migrate_to_vault.sh
```

Then follow the 3 steps above!

**Estimated time:** 15-20 minutes  
**You've got this! 💪**
