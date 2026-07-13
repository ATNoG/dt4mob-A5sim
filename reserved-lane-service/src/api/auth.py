import logging
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_oidc import IDToken, get_auth
from pydantic import BaseModel
from jose import jwt

from src.settings import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class RoleMapping(BaseModel):
    roles: list[str]


class KeycloakToken(IDToken):
    resource_access: dict[str, RoleMapping] = {}


auth: Callable = get_auth(
    client_id=settings.auth.client_id,
    audience=settings.auth.audience,
    base_authorization_server_uri=settings.auth.internal_server_uri.rstrip("/"),
    issuer=settings.auth.issuer,
    signature_cache_ttl=settings.auth.signature_cache_ttl,
    token_type=KeycloakToken,
)


def check_role(roles: list[str]) -> Callable:
    def check_role_inner(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> KeycloakToken:
        try:
        # This is where the 401 is happening behind the scenes
            token: KeycloakToken = auth(credentials.credentials)
        except HTTPException as http_exc:
            # Capture the OIDC package's built-in HTTP failures
            logger.error(f"OIDC Auth failed with status {http_exc.status_code}: {http_exc.detail}")
            unverified_payload = jwt.get_unverified_claims(credentials.credentials)
            token_issuer = unverified_payload.get("iss")
            
            logger.error(
                f"OIDC Mismatch Details:\n"
                f" -> Expected Issuer (Your Config): '{settings.auth.issuer}'\n"
                f" -> Actual Token Issuer (From Keycloak): '{token_issuer}'"
            )
            raise http_exc
        except Exception as e:
            # Capture any unexpected parsing/decoding crashes
            logger.error(f"Unexpected token validation crash: {str(e)}", exc_info=True)
            raise HTTPException(status_code=401, detail="Authentication failed")
        logger.warning(f"Token resource access: {token.resource_access}")
        if settings.auth.client_id not in token.resource_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Missing role"
            )

        token_roles = token.resource_access[settings.auth.client_id].roles
        logger.warning(f"Token roles: {token_roles}, required roles: {roles}")
        if not any(role in token_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Missing role"
            )

        return token

    return check_role_inner
