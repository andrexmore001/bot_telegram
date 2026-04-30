import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.config.config import config
from app.infrastructure.logging.logger import logger

# Esquema simple para extraer el token Bearer inyectado por Kong
security = HTTPBearer()

class KeycloakAuth:
    def __init__(self):
        self.jwks = None
        self.issuer = f"{config.keycloak_url}realms/{config.keycloak_realm}"
        self.certs_url = f"{self.issuer}/protocol/openid-connect/certs"

    async def get_jwks(self):
        if self.jwks is None:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self.certs_url)
                    response.raise_for_status()
                    self.jwks = response.json()
                except Exception as e:
                    logger.error(f"Error obteniendo JWKS de Keycloak: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No se pudo validar el servicio de identidad."
                    )
        return self.jwks

    async def verify_token(self, auth: HTTPAuthorizationCredentials = Depends(security)):
        token = auth.credentials
        jwks = await self.get_jwks()
        
        try:
            # Obtener el header del token para saber qué llave usar
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if rsa_key:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=config.keycloak_audience,
                    issuer=self.issuer
                )
                
                # LOG DE DEPURACION PARA EL USUARIO
                logger.info(f"DEBUG TOKEN - Claims presentes: {list(payload.keys())}")
                logger.info(f"DEBUG TOKEN - Audience en token: {payload.get('aud')}")
                logger.info(f"DEBUG TOKEN - Esperado: {config.keycloak_audience}")

                # Verificación estricta manual
                token_aud = payload.get("aud")
                if not token_aud or (isinstance(token_aud, str) and token_aud != config.keycloak_audience) or (isinstance(token_aud, list) and config.keycloak_audience not in token_aud):
                    logger.warning(f"¡BLOQUEADO! Audiencia incorrecta o ausente.")
                    raise JWTError("Audience verification failed")

                return payload



        except JWTError as e:
            logger.warning(f"Token inválido: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Error inesperado validando token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar la autenticación",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo encontrar la llave de validación",
        )

auth_service = KeycloakAuth()
