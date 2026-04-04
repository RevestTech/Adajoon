# OAuth Authentication Flow Analysis

**Date:** April 3, 2026  
**Codebase:** Adajoon (TV/Radio Streaming Platform)

---

## Executive Summary

The authentication system implements a **hybrid approach** using both **localStorage-based JWT tokens** and **httpOnly cookies**, but there is a **critical inconsistency** between what the backend sets and what it expects to receive. This creates a potential authentication failure scenario.

### Key Findings:
1. ✅ Google OAuth integration is properly implemented
2. ⚠️ **Critical Gap:** Backend sets httpOnly cookies but expects Bearer tokens in Authorization header
3. ⚠️ Frontend stores tokens in localStorage but authenticatedFetch doesn't use them
4. ⚠️ Public API endpoints don't use authenticatedFetch (potential CORS/cookie issues)
5. ✅ CSRF protection is properly implemented for mutating requests

---

## 1. Complete OAuth Flow Mapping

### Frontend to Backend Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Google OAuth Initiation                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 1. User clicks "Sign in with Google"
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LoginModal.jsx (lines 9-14)                                    │
│  - Google Sign-In SDK initialized with client ID                │
│  - User authenticates with Google                               │
│  - Google returns JWT credential                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 2. Credential passed to handler
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  App.jsx: handleGoogleLogin (line 249)                          │
│  - Calls auth.loginWithGoogle(credential)                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 3. useAuth hook processes login
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  useAuth.jsx: loginWithGoogle (lines 35-48)                     │
│  - POST to /api/auth/google                                     │
│  - Uses authenticatedFetch                                      │
│  - Sends: { credential: "<google-jwt>" }                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 4. HTTP POST with CSRF protection
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: auth.py: google_login (lines 177-210)                 │
│  - Verifies Google token with Google API                        │
│  - Extracts: email, name, picture, google_id                    │
│  - Creates/updates User in database                             │
│  - Generates internal JWT token                                 │
│  - Calls _set_auth_cookies()                                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 5. Cookies set in response
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: _set_auth_cookies (lines 77-106)                      │
│  ✅ Sets auth_token (httpOnly, secure, samesite=lax, 30 days)  │
│  ✅ Sets csrf_token (readable, secure, samesite=lax, 1 hour)   │
│  ✅ Returns: { user: { id, email, name, picture } }            │
│  ⚠️  NO TOKEN IN RESPONSE BODY                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ 6. Response processed
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  useAuth.jsx: _saveSession (lines 27-32)                        │
│  ⚠️  PROBLEM: Saves response.token to localStorage              │
│  ⚠️  BUT: Backend doesn't return token in response body!        │
│  - localStorage.setItem(TOKEN_KEY, data.token)  ❌ undefined   │
│  - localStorage.setItem(USER_KEY, JSON.stringify(data.user)) ✅ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Analysis

### 2.1 Google Login Trigger (`LoginModal.jsx`)

```jsx
// frontend/src/components/LoginModal.jsx (lines 6-23)
```

**Implementation:**
- Uses Google Sign-In JavaScript SDK
- Google button rendered via `google.accounts.id.renderButton()`
- Callback receives JWT credential from Google
- Credential passed to parent via `onGoogleLogin(response.credential)`

**Status:** ✅ Properly implemented

### 2.2 Authentication Hook (`useAuth.jsx`)

```jsx
// frontend/src/hooks/useAuth.jsx
```

**Key Functions:**

1. **loginWithGoogle (lines 35-48)**
   - Uses `authenticatedFetch` to POST credential
   - Endpoint: `/api/auth/google`
   - Calls `_saveSession` on success

2. **_saveSession (lines 27-32)**
   - ⚠️ **ISSUE:** Attempts to save `data.token` to localStorage
   - Backend doesn't return token in body (only sets cookies)
   - User data is saved correctly

3. **authHeaders (lines 22-25)**
   - Returns `{ Authorization: Bearer ${token} }` from localStorage
   - ⚠️ **UNUSED:** This function is never called by authenticatedFetch!

**Status:** ⚠️ Contains inconsistencies

### 2.3 CSRF Utility (`csrf.js`)

```javascript
// frontend/src/utils/csrf.js
```

**authenticatedFetch Implementation (lines 35-62):**
```javascript
export async function authenticatedFetch(url, options = {}) {
  const csrfToken = getCsrfToken();
  
  const method = options.method?.toUpperCase() || 'GET';
  const isMutating = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  
  if (isMutating && !csrfToken) {
    const newToken = await fetchCsrfToken();
    if (!newToken) {
      throw new Error('Failed to get CSRF token');
    }
  }
  
  const headers = {
    ...options.headers,
    ...(csrfToken && isMutating ? { 'X-CSRF-Token': csrfToken } : {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include', // ✅ Sends cookies
  });
}
```

**Status:** ✅ Properly sends cookies with `credentials: 'include'`

### 2.4 API Call Patterns

**Files using `authenticatedFetch`:**
- ✅ `hooks/useAuth.jsx` - All auth operations
- ✅ `hooks/useVotes.js` - Voting operations
- ✅ `hooks/useSubscription.js` - Subscription status/checkout
- ✅ `api/channels.js` - Only `runHealthCheck` function

**Files using plain `fetch` (NOT authenticatedFetch):**
- ⚠️ `api/channels.js` - fetchChannels, fetchCategories, fetchCountries, fetchStats, fetchStreams
- ⚠️ `api/radio.js` - fetchRadioStations, fetchRadioTags, fetchRadioCountries
- ⚠️ `api/recommendations.js` - fetchRecommendations
- ⚠️ `api/languages.js` - Language fetching
- ⚠️ `utils/csrf.js` - fetchCsrfToken (intentional for bootstrap)

**Analysis:**
- Public read-only endpoints don't need authentication (channels, categories, etc.)
- These are likely public APIs that don't require auth
- **Potential Issue:** If these endpoints need cookies for any reason (e.g., rate limiting by user), they won't send them

---

## 3. Backend Analysis

### 3.1 Google Token Verification (`auth.py`)

```python
# backend/app/routers/auth.py (lines 177-210)
```

**Flow:**
1. Receives POST with `{ credential: "<google-jwt>" }`
2. Verifies token with Google's API using `id_token.verify_oauth2_token()`
3. Extracts user info: email, name, picture, sub (Google ID)
4. Creates or updates User in database
5. Generates internal JWT with `create_token(user.id, user.email)`
6. Sets cookies via `_set_auth_cookies(response, user, token)`
7. Returns user data (NO TOKEN IN BODY)

**Status:** ✅ Properly implemented, secure verification

### 3.2 Cookie Setting (`_set_auth_cookies`)

```python
# backend/app/routers/auth.py (lines 77-106)
```

**Cookies Set:**

1. **auth_token (JWT)**
   - `httponly=True` - ✅ Protected from XSS
   - `secure=True` - ✅ HTTPS only
   - `samesite="lax"` - ✅ CSRF protection
   - `max_age=30 days`
   - `domain=".adajoon.com"` (production) or None (dev)

2. **csrf_token**
   - `httponly=False` - ✅ Readable by JS (required)
   - `secure=True`
   - `samesite="lax"`
   - `max_age=1 hour`
   - Same domain as auth_token

**Status:** ✅ Secure cookie configuration

### 3.3 Authentication Dependency (`get_current_user`)

```python
# backend/app/routers/auth.py (lines 124-136)
```

**⚠️ CRITICAL ISSUE:**

```python
async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, ...)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
    # ... fetch user from DB
```

**Problem:**
- Uses `HTTPBearer` security scheme (line 46: `security = HTTPBearer(auto_error=False)`)
- Expects `Authorization: Bearer <token>` header
- **Does NOT read from cookies!**
- Frontend's `authenticatedFetch` sends cookies via `credentials: 'include'`
- **Mismatch:** Backend sets cookies but doesn't read them for auth

**Impact:**
- If localStorage token is missing/invalid, all authenticated requests fail
- The httpOnly cookie is set but never used
- System relies on localStorage which is less secure than httpOnly cookies

### 3.4 Protected Endpoints Usage

Endpoints using `require_user` or `get_current_user`:
- ✅ `/api/auth/me` (GET current user)
- ✅ `/api/auth/favorites` (GET, POST, DELETE)
- ✅ `/api/auth/votes` (POST, GET)
- ✅ `/api/auth/passkey/*` (all passkey operations)
- ✅ Subscription endpoints
- ✅ Parental controls
- ✅ Playlists
- ✅ History

**All of these expect Bearer token in Authorization header!**

---

## 4. Cookie Flow Analysis

### 4.1 Cookie Setting (After Login)

**Successful Login Response:**
```
HTTP/1.1 200 OK
Set-Cookie: auth_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000; Domain=.adajoon.com; Path=/
Set-Cookie: csrf_token=<csrf>; Secure; SameSite=Lax; Max-Age=3600; Domain=.adajoon.com; Path=/
Content-Type: application/json

{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "User Name",
    "picture": "https://..."
  }
}
```

**Note:** Token is NOT in response body, only in cookies

### 4.2 Cookie Usage in Subsequent Requests

**Frontend Request (via authenticatedFetch):**
```javascript
fetch('/api/auth/favorites', {
  method: 'GET',
  credentials: 'include',  // ✅ Sends cookies
  headers: {
    // ❌ NO Authorization header!
  }
})
```

**Backend Expectation:**
```
GET /api/auth/favorites
Authorization: Bearer <token>  // ❌ Expected but not sent!
Cookie: auth_token=<jwt>; csrf_token=<csrf>  // ✅ Sent but not read!
```

**Result:** Authentication fails unless localStorage has valid token

---

## 5. Identified Gaps and Inconsistencies

### 5.1 ⚠️ CRITICAL: Authentication Mechanism Mismatch

**Problem:**
- Backend sets JWT in httpOnly cookie
- Backend expects JWT in Authorization header
- Frontend sends cookies but no Authorization header
- Frontend tries to save token to localStorage but backend doesn't send it

**Current State:**
```
Backend Login → Sets httpOnly cookie (secure) ✅
              → Returns user data only ✅
              → Does NOT return token in body ✅ (security best practice)

Frontend Login → Tries to save response.token to localStorage ❌ (undefined)
               → Saves user data ✅
               → authHeaders() creates Bearer token from localStorage ❌ (never used)

Frontend API Calls → Uses authenticatedFetch ✅
                   → Sends cookies via credentials: 'include' ✅
                   → Does NOT send Authorization header ❌

Backend Auth Check → Reads HTTPBearer from Authorization header ❌
                   → Does NOT read cookies ❌
                   → Returns null (unauthorized) ❌
```

**Impact:**
- **Authentication currently broken** if localStorage doesn't persist token
- httpOnly cookies are set but never validated
- System falls back to localStorage-based auth (less secure)

### 5.2 ⚠️ Session Persistence Issue

**Problem:**
```javascript
// frontend/src/hooks/useAuth.jsx (lines 27-32)
const _saveSession = useCallback((data) => {
  localStorage.setItem(TOKEN_KEY, data.token);  // ❌ data.token is undefined!
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  setUser(data.user);
  return data.user;
}, []);
```

**Issue:** Backend response doesn't include `token` field, so localStorage gets `undefined`

### 5.3 ⚠️ Unused Auth Header Function

```javascript
// frontend/src/hooks/useAuth.jsx (lines 22-25)
const authHeaders = useCallback(() => {
  const t = localStorage.getItem(TOKEN_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}, []);
```

**Issue:** This function is never used by `authenticatedFetch`. It's returned in the context but never called.

### 5.4 ⚠️ Public Endpoints Not Using authenticatedFetch

**Files with plain fetch:**
- `api/channels.js` - fetchChannels, fetchCategories, fetchCountries, fetchStats
- `api/radio.js` - fetchRadioStations, fetchRadioTags, fetchRadioCountries
- `api/recommendations.js` - fetchRecommendations

**Analysis:**
- These appear to be public endpoints (no auth required)
- **Good:** They don't send unnecessary cookies
- **Potential Issue:** If rate limiting or personalization needs user context, cookies won't be sent
- No CSRF tokens sent (GET requests don't need them)

### 5.5 ✅ CSRF Protection Working Correctly

**Implementation:**
- CSRF token stored in readable cookie
- `authenticatedFetch` reads token from cookie
- Sends `X-CSRF-Token` header for mutating requests (POST, PUT, DELETE)
- Backend validates token via `verify_csrf_token` dependency
- Token expires after 1 hour

**Status:** ✅ Properly implemented, no gaps

---

## 6. Consistency Check: authenticatedFetch Usage

### 6.1 Correctly Using authenticatedFetch ✅

**Auth Operations (`useAuth.jsx`):**
- ✅ loginWithGoogle
- ✅ loginWithApple
- ✅ loginWithPasskey
- ✅ registerPasskey
- ✅ fetchFavorites
- ✅ addFavorite
- ✅ removeFavorite
- ✅ syncFavorites
- ✅ /api/auth/me (in useEffect)

**Voting (`useVotes.js`):**
- ✅ loadMyVotes
- ✅ loadSummary
- ✅ submitVote

**Subscriptions (`useSubscription.js`):**
- ✅ loadStatus
- ✅ checkout
- ✅ openPortal

**Channels (`api/channels.js`):**
- ✅ runHealthCheck (requires auth)

### 6.2 Not Using authenticatedFetch (Intentional) ✅

**Public Read-Only Endpoints:**
- `fetchChannels` - Public channel list
- `fetchCategories` - Public categories
- `fetchCountries` - Public countries
- `fetchStats` - Public statistics
- `fetchRadioStations` - Public radio stations
- `fetchRadioTags` - Public tags
- `fetchRadioCountries` - Public countries
- `fetchRecommendations` - Public recommendations

**Reasoning:** These endpoints don't require authentication and shouldn't send credentials

### 6.3 Edge Cases

**fetchCsrfToken (`csrf.js`):**
- Uses plain `fetch` with `credentials: 'include'`
- **Correct:** Needs to bootstrap CSRF token before authenticatedFetch can use it

---

## 7. Recommendations

### 7.1 HIGH PRIORITY: Fix Authentication Mechanism

**Option A: Use Cookie-Based Auth (Recommended)**

**Backend Change:**
```python
# backend/app/routers/auth.py
from fastapi import Cookie

async def get_current_user(
    auth_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not auth_token:
        return None
    try:
        payload = jwt.decode(auth_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**Frontend Change:**
```javascript
// frontend/src/hooks/useAuth.jsx
const _saveSession = useCallback((data) => {
  // Remove localStorage token (use cookies only)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  setUser(data.user);
  return data.user;
}, []);
```

**Benefits:**
- More secure (httpOnly cookies prevent XSS)
- Consistent with current cookie-setting behavior
- No localStorage needed for tokens
- CSRF protection already in place

---

**Option B: Use Header-Based Auth**

**Backend Change:**
```python
# backend/app/routers/auth.py
def _user_response(user: User, token: str) -> dict:
    """Return user data WITH token in body"""
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
        "token": token,  # Add token to response
    }

# Update all login endpoints to include token
```

**Frontend Change:**
```javascript
// frontend/src/utils/csrf.js
export async function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem('adajoon_token');
  const csrfToken = getCsrfToken();
  
  const headers = {
    ...options.headers,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(csrfToken && isMutating ? { 'X-CSRF-Token': csrfToken } : {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
}
```

**Drawbacks:**
- Less secure (localStorage vulnerable to XSS)
- Inconsistent with current cookie-setting
- More frontend changes needed

---

### 7.2 MEDIUM PRIORITY: Clean Up Unused Code

**Remove unused authHeaders function:**
```javascript
// frontend/src/hooks/useAuth.jsx
// Delete lines 22-25 (authHeaders function)
// Remove from context value (line 187)
```

### 7.3 LOW PRIORITY: Consider Authenticated Public Endpoints

**If personalization/rate limiting needed:**
- Change public fetch calls to use authenticatedFetch
- Backend can optionally check for user without requiring it
- Allows personalized content for logged-in users

**Example:**
```python
@router.get("/api/channels")
async def get_channels(
    user: User | None = Depends(get_current_user),  # Optional
    ...
):
    # Personalize based on user if available
    if user:
        # Apply user preferences, history, etc.
        pass
```

---

## 8. Testing Recommendations

### 8.1 Manual Testing Checklist

**Before Fix:**
- [ ] Clear localStorage and cookies
- [ ] Login with Google
- [ ] Check browser DevTools → Application → Cookies (should see auth_token and csrf_token)
- [ ] Check localStorage (should see adajoon_user, but token might be undefined)
- [ ] Try to fetch favorites (`/api/auth/favorites`)
- [ ] Expected: **Request fails or returns unauthorized**

**After Fix (Option A - Cookie Auth):**
- [ ] Clear localStorage and cookies
- [ ] Login with Google
- [ ] Check cookies are set correctly
- [ ] Try to fetch favorites
- [ ] Expected: **Request succeeds with user's favorites**
- [ ] Refresh page
- [ ] Expected: **User still logged in (cookies persist)**

### 8.2 Automated Test Cases

**Backend Tests:**
```python
# Test cookie-based authentication
async def test_get_current_user_from_cookie():
    token = create_token(user_id=1, email="test@example.com")
    response = client.get(
        "/api/auth/me",
        cookies={"auth_token": token}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

**Frontend Tests:**
```javascript
// Test authenticatedFetch sends cookies
test('authenticatedFetch includes credentials', async () => {
  await authenticatedFetch('/api/auth/favorites');
  expect(fetch).toHaveBeenCalledWith(
    expect.any(String),
    expect.objectContaining({
      credentials: 'include'
    })
  );
});
```

---

## 9. Security Considerations

### 9.1 Current Security Posture

**Strengths:**
- ✅ httpOnly cookies (XSS protection)
- ✅ Secure flag on cookies (HTTPS only)
- ✅ SameSite=Lax (CSRF protection)
- ✅ CSRF tokens for mutating requests
- ✅ Google OAuth token verification
- ✅ JWT expiry (30 days)

**Weaknesses:**
- ⚠️ Reliance on localStorage (if that's the fallback)
- ⚠️ Token might be exposed in localStorage

### 9.2 Post-Fix Security

**With Cookie-Based Auth (Option A):**
- ✅ All strengths maintained
- ✅ No localStorage exposure
- ✅ httpOnly prevents token theft via XSS
- ✅ CSRF tokens prevent cross-site attacks

---

## 10. Migration Path

### Phase 1: Immediate Fix (Cookie Auth)
1. Update `get_current_user` to read from cookie
2. Remove token from localStorage saving
3. Test all authenticated endpoints
4. Deploy to staging
5. Verify session persistence

### Phase 2: Cleanup
1. Remove unused `authHeaders` function
2. Update documentation
3. Add automated tests

### Phase 3: Consider Enhancements
1. Evaluate if public endpoints need user context
2. Consider refresh token mechanism
3. Add session management UI (view/revoke sessions)

---

## 11. Conclusion

The OAuth flow is **well-implemented** but suffers from a **critical authentication mechanism mismatch**:

- ✅ Google OAuth integration is secure and correct
- ✅ Cookie setting is properly configured (httpOnly, secure, SameSite)
- ✅ CSRF protection is working correctly
- ⚠️ **CRITICAL:** Backend sets cookies but expects Bearer tokens
- ⚠️ Frontend sends cookies but backend doesn't read them
- ⚠️ localStorage token saving fails (backend doesn't return token)

**Recommendation:** Implement **Option A (Cookie-Based Auth)** to align backend expectations with frontend behavior. This is:
- More secure (httpOnly cookies)
- Consistent with current cookie-setting
- Simpler frontend code
- Industry best practice for web applications

**Impact:** After fix, authentication will work reliably, sessions will persist across page refreshes, and the system will be more secure by eliminating localStorage token storage.
