---
name: adajoon-frontend
description: Enforce Adajoon frontend React patterns including custom hooks with Context API, authenticatedFetch for mutations, CSRF token handling, OAuth integration (Google/Apple), error handling, loading states, and localStorage patterns. Use when creating or editing React components, custom hooks, or API client modules in the Adajoon frontend.
---

# Adajoon Frontend React Patterns

**Version**: 1.0.0 (Updated: 2026-04-04)

## Changelog
- v1.0.0 (2026-04-04): Initial versioning - established baseline frontend patterns

## Custom Hooks Pattern

### Context + Hook Pattern

Use Context API with a custom hook wrapper:

```javascript
import { createContext, useContext, useState, useCallback, useMemo } from "react";

const MyContext = createContext(null);

export function MyProvider({ children }) {
  const [state, setState] = useState(initialValue);
  const [loading, setLoading] = useState(false);

  const someAction = useCallback(async () => {
    setLoading(true);
    try {
      // action logic
    } finally {
      setLoading(false);
    }
  }, [dependencies]);

  const value = useMemo(() => ({
    state,
    loading,
    someAction,
  }), [state, loading, someAction]);

  return (
    <MyContext.Provider value={value}>
      {children}
    </MyContext.Provider>
  );
}

export function useMyHook() {
  return useContext(MyContext);
}
```

### Key Requirements

- Export both Provider and hook from the same file
- Use `useCallback` for all functions exposed in context
- Use `useMemo` for the context value object
- Always include a `loading` state for async operations
- Use `try/finally` blocks to ensure loading state is cleared

## API Client Patterns

### GET Requests (Public Data)

Use regular `fetch` for GET requests that don't require authentication:

```javascript
export async function fetchData() {
  const res = await fetch(`${BASE}/endpoint`);
  if (!res.ok) throw new Error("Failed to fetch data");
  return res.json();
}
```

### Mutations (POST/PUT/DELETE)

**ALWAYS use `authenticatedFetch`** for mutations:

```javascript
import { authenticatedFetch } from '../utils/csrf';

export async function createItem(data) {
  const res = await authenticatedFetch(`${BASE}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create item");
  return res.json();
}

export async function updateItem(id, data) {
  const res = await authenticatedFetch(`${BASE}/items/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update item");
  return res.json();
}

export async function deleteItem(id) {
  const res = await authenticatedFetch(`${BASE}/items/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete item");
  return res.json();
}
```

### Query Parameters

Use `URLSearchParams` for building query strings:

```javascript
export async function fetchWithFilters({ query, category, page = 1 }) {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  if (category) params.set("category", category);
  params.set("page", page);

  const res = await fetch(`${BASE}/endpoint?${params}`);
  if (!res.ok) throw new Error("Failed to fetch");
  return res.json();
}
```

## CSRF Token Handling

### Automatic CSRF Protection

`authenticatedFetch` automatically handles CSRF tokens:

- Reads token from `csrf_token` cookie
- Adds `X-CSRF-Token` header for POST/PUT/DELETE requests
- Fetches new token if missing
- Always includes `credentials: 'include'` for cookies

**Never manually add CSRF headers** - `authenticatedFetch` does this automatically.

### Usage in Hooks

```javascript
import { authenticatedFetch } from "../utils/csrf";

const addItem = useCallback(async (data) => {
  try {
    await authenticatedFetch(`${API_BASE}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch (error) {
    console.error("Failed to add item:", error);
  }
}, []);
```

## OAuth Integration Patterns

### Google Sign-In

```javascript
import { useEffect, useRef, useCallback } from "react";

let gsiInitialized = false;

function Component({ onGoogleLogin, googleClientId }) {
  const googleBtnRef = useRef(null);
  const callbackRef = useRef(onGoogleLogin);
  callbackRef.current = onGoogleLogin;

  const initGsi = useCallback(() => {
    if (!googleClientId || !window.google?.accounts?.id || !googleBtnRef.current) return false;
    if (!gsiInitialized) {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: (response) => callbackRef.current(response.credential),
        use_fedcm_for_prompt: true,
      });
      gsiInitialized = true;
    }
    googleBtnRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(googleBtnRef.current, {
      theme: "filled_black",
      size: "large",
      width: 320,
      text: "signin_with",
      shape: "pill",
    });
    return true;
  }, [googleClientId]);

  useEffect(() => {
    if (initGsi()) return;
    const interval = setInterval(() => {
      if (initGsi()) clearInterval(interval);
    }, 300);
    return () => clearInterval(interval);
  }, [initGsi]);

  return <div ref={googleBtnRef} />;
}
```

### Apple Sign-In

```javascript
useEffect(() => {
  const handler = (event) => {
    if (event.origin !== window.location.origin) return;
    if (event.data?.type !== "apple-signin") return;
    const { idToken, userData } = event.data;
    if (!idToken) return;
    let userName = "";
    if (userData?.name) {
      userName = [userData.name.firstName, userData.name.lastName].filter(Boolean).join(" ");
    }
    onAppleLogin(idToken, userName);
  };
  window.addEventListener("message", handler);
  return () => window.removeEventListener("message", handler);
}, [onAppleLogin]);

const handleAppleLogin = () => {
  const params = new URLSearchParams({
    client_id: appleClientId,
    redirect_uri: `${window.location.origin}/api/auth/apple/callback`,
    response_type: "code id_token",
    response_mode: "form_post",
    scope: "name email",
  });
  window.open(
    `https://appleid.apple.com/auth/authorize?${params}`,
    "apple-signin",
    "width=500,height=700,left=200,top=100"
  );
};
```

## Error Handling in Components

### Try/Catch with User Feedback

```javascript
const [error, setError] = useState("");
const [loading, setLoading] = useState(false);

const handleAction = async () => {
  setError("");
  setLoading(true);
  try {
    await someAsyncAction();
  } catch (err) {
    // Handle specific error types
    if (err.name !== "NotAllowedError") {
      setError("Action failed. Please try again.");
    }
  } finally {
    setLoading(false);
  }
};
```

### Error Display

```jsx
{error && <div className="error-message">{error}</div>}
```

### Silent Errors (Non-Critical)

For non-critical operations, log and continue:

```javascript
try {
  await nonCriticalAction();
} catch (error) {
  console.error("Non-critical action failed:", error);
}
```

## Loading States and User Feedback

### Pattern in Hooks

```javascript
const [loading, setLoading] = useState(false);

const performAction = useCallback(async (data) => {
  setLoading(true);
  try {
    const res = await authenticatedFetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Action failed");
    return await res.json();
  } finally {
    setLoading(false);
  }
}, []);
```

### Pattern in Components

```jsx
function Component() {
  const { loading, performAction } = useMyHook();

  return (
    <button onClick={performAction} disabled={loading}>
      {loading ? "Processing..." : "Submit"}
    </button>
  );
}
```

## localStorage Usage Patterns

### Initialization with Error Handling

```javascript
const [state, setState] = useState(() => {
  try {
    const raw = localStorage.getItem('key');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
});
```

### Saving Data

```javascript
const saveData = useCallback((data) => {
  localStorage.setItem('key', JSON.stringify(data));
  setState(data);
}, []);
```

### Keys Convention

Use prefixed keys: `adajoon_token`, `adajoon_user`, etc.

```javascript
const TOKEN_KEY = "adajoon_token";
const USER_KEY = "adajoon_user";
```

### Clearing on Logout

```javascript
const logout = useCallback(() => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  setState(null);
}, []);
```

## Environment Variables

### Vite Pattern

Access environment variables via `import.meta.env`:

```javascript
const apiUrl = import.meta.env.VITE_API_URL;
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID;
```

### Naming Convention

- Prefix all variables with `VITE_`
- Use uppercase with underscores
- Examples: `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`

### Passing to Components

Pass as props rather than accessing directly in leaf components:

```jsx
function App() {
  return (
    <Component
      googleClientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}
      appleClientId={import.meta.env.VITE_APPLE_CLIENT_ID}
    />
  );
}
```

## Feature Detection

### Check Before Using

```javascript
const [supported, setSupported] = useState(false);

useEffect(() => {
  if (window.PublicKeyCredential) {
    PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable?.()
      .then((available) => setSupported(available))
      .catch(() => {});
  }
}, []);
```

### Conditional Rendering

```jsx
{supported && <FeatureComponent />}
```

## Checklist for New React Components

When creating a new component, verify:

- [ ] Uses `authenticatedFetch` for all mutations (POST/PUT/DELETE)
- [ ] Loading state implemented for async operations
- [ ] Error handling with user feedback
- [ ] Try/finally blocks to ensure loading state cleanup
- [ ] localStorage access wrapped in try/catch
- [ ] Environment variables accessed via `import.meta.env.VITE_*`
- [ ] OAuth callbacks use proper origin validation
- [ ] Feature detection before using browser APIs

## Checklist for New Custom Hooks

When creating a new hook, verify:

- [ ] Context + Provider + hook pattern used
- [ ] All functions wrapped in `useCallback`
- [ ] Context value wrapped in `useMemo`
- [ ] Loading state included for async operations
- [ ] Uses `authenticatedFetch` for mutations
- [ ] Try/finally blocks for loading state cleanup
- [ ] Proper error handling

## Checklist for New API Clients

When creating a new API client, verify:

- [ ] GET requests use regular `fetch`
- [ ] POST/PUT/DELETE use `authenticatedFetch`
- [ ] Query params built with `URLSearchParams`
- [ ] Consistent error throwing: `if (!res.ok) throw new Error("...")`
- [ ] Import `authenticatedFetch` from `'../utils/csrf'`
- [ ] Base URL stored in constant: `const BASE = "/api"`
