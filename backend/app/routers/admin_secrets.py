"""Admin UI for writing app secrets into the shared vault.

Write-only: a secret's value is never returned once set, only whether it's
configured. Restricted to the fixed MANAGED_SECRETS whitelist - this is not
a general vault browser/editor.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.csrf import verify_csrf_token
from app.middleware.admin_required import require_admin
from app.models import User
from app.services import vault_admin_service
from app.vault_client import VaultSealed

VAULT_SEALED_DETAIL = "Vault is temporarily unavailable (sealed) - try again shortly"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/secrets", tags=["admin", "secrets"])


class SecretSetRequest(BaseModel):
    value: str


@router.get("")
async def admin_list_secrets(admin_user: User = Depends(require_admin)):
    return vault_admin_service.get_secret_status()


@router.put("/{key}")
async def admin_set_secret(
    key: str,
    payload: SecretSetRequest,
    admin_user: User = Depends(require_admin),
    _csrf: None = Depends(verify_csrf_token),
):
    value = payload.value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Value must not be blank")
    try:
        vault_admin_service.set_secret(key, value)
    except vault_admin_service.SecretNotManaged:
        raise HTTPException(status_code=404, detail="Unknown secret key")
    except VaultSealed:
        raise HTTPException(status_code=503, detail=VAULT_SEALED_DETAIL)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        logger.exception("Vault write failed for key %s", key)
        raise HTTPException(status_code=502, detail="Vault write failed")

    # Never log the value.
    logger.info("Admin %s set vault secret adajoon:%s", admin_user.email, key)
    return {"success": True}


@router.delete("/{key}")
async def admin_clear_secret(
    key: str,
    admin_user: User = Depends(require_admin),
    _csrf: None = Depends(verify_csrf_token),
):
    try:
        vault_admin_service.delete_secret(key)
    except vault_admin_service.SecretNotManaged:
        raise HTTPException(status_code=404, detail="Unknown secret key")
    except VaultSealed:
        raise HTTPException(status_code=503, detail=VAULT_SEALED_DETAIL)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        logger.exception("Vault delete failed for key %s", key)
        raise HTTPException(status_code=502, detail="Vault delete failed")

    logger.info("Admin %s cleared vault secret adajoon:%s", admin_user.email, key)
    return {"success": True}
