"""revest-vault AppRole client.

Adajoon never holds a long-lived vault credential. It holds a
VAULT_ROLE_ID/VAULT_SECRET_ID pair (from the one-time enrollment -
see scripts/admin_enroll.py and examples/enroll.py in RevestTech/revest-vault)
scoped to the `adajoon:*` key prefix, exchanges that for a short-lived
(15 min) access token at runtime, and refreshes before it expires. Only
that short-lived token ever touches /get, /set, /has.

Follows RevestTech/revest-vault's AGENTS.md contract exactly:
- Never log role_id/secret_id or any secret value, including in exceptions.
- Treat a 503 ("vault is sealed") as retryable, not fatal - VaultSealedError
  lets callers show a clear "try again shortly" state instead of crashing
  or silently falling back to a stale value.
- Never call /list, /history, /admin/* - those are admin-token-only and
  out of scope for app code.
"""

from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)


class VaultSealed(Exception):
    """The vault itself is sealed (mid-unseal after a restart) - retryable,
    unrelated to whether the requested key exists."""


class VaultAuthError(Exception):
    """role_id/secret_id was rejected (invalid or revoked)."""


class VaultClient:
    def __init__(
        self,
        addr: str,
        role_id: str,
        secret_id: str,
        timeout: float = 10.0,
    ):
        self.addr = addr.rstrip("/")
        self._role_id = role_id
        self._secret_id = secret_id
        self.timeout = timeout
        self._token: str | None = None
        self._expires_at = 0.0

    def _is_sealed(self) -> bool:
        """revest-vault's /health is unauthenticated and reports `sealed`
        accurately. Used as a fallback when an endpoint returns a plain 500
        instead of 503 while sealed (a known vault-api quirk on /has) -
        this app never guesses, it asks the vault directly."""
        try:
            resp = httpx.get(f"{self.addr}/health", timeout=self.timeout)
            return bool(resp.json().get("sealed"))
        except Exception:
            return False

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 503:
            raise VaultSealed()
        if resp.status_code >= 500 and self._is_sealed():
            raise VaultSealed()
        resp.raise_for_status()

    def _ensure_token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token

        try:
            resp = httpx.post(
                f"{self.addr}/auth/token",
                json={"role_id": self._role_id, "secret_id": self._secret_id},
                timeout=self.timeout,
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot reach vault: {e}") from None

        if resp.status_code == 503:
            raise VaultSealed()
        if resp.status_code == 401:
            raise VaultAuthError("role_id/secret_id rejected by vault")
        resp.raise_for_status()

        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        return self._token

    def get(self, key: str) -> str:
        """Raises KeyError if not found, VaultSealed if sealed,
        ConnectionError if unreachable."""
        token = self._ensure_token()
        try:
            resp = httpx.get(
                f"{self.addr}/get/{key}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot reach vault: {e}") from None

        if resp.status_code == 404:
            raise KeyError(f"Secret not found: {key}")
        self._raise_for_status(resp)
        return resp.json()["value"]

    def set(self, key: str, value: str) -> None:
        token = self._ensure_token()
        try:
            resp = httpx.post(
                f"{self.addr}/set",
                headers={"Authorization": f"Bearer {token}"},
                json={"key": key, "value": value},
                timeout=self.timeout,
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot reach vault: {e}") from None

        self._raise_for_status(resp)

    def delete(self, key: str) -> None:
        token = self._ensure_token()
        try:
            resp = httpx.post(
                f"{self.addr}/delete/{key}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot reach vault: {e}") from None

        self._raise_for_status(resp)

    def has(self, key: str) -> bool:
        token = self._ensure_token()
        try:
            resp = httpx.get(
                f"{self.addr}/has/{key}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot reach vault: {e}") from None

        self._raise_for_status(resp)
        return bool(resp.json().get("exists"))
