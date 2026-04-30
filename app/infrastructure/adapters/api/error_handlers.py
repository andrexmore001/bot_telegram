from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import traceback

from app.infrastructure.logging.logger import logger

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str

class ErrorResponse(BaseModel):
    status: str = "error"
    code: int
    message: str
    details: Optional[List[ErrorDetail]] = None

async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para excepciones no controladas (HTTP 500).
    Registra el error real internamente, pero devuelve un mensaje genérico
    para evitar el Information Disclosure.
    """
    logger.error(
        f"Error interno no controlado en {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}"
    )
    
    error_response = ErrorResponse(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Ocurrió un error interno en el servidor. Por favor, inténtelo de nuevo más tarde."
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response.model_dump())

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador para excepciones HTTP controladas.
    Asegura que siempre sigan el estándar ErrorResponse.
    """
    # Evitar registrar errores 401/403 como errores críticos, pero sí como advertencias si es útil
    if exc.status_code >= 500:
        logger.error(f"Error HTTP {exc.status_code} en {request.method} {request.url.path}: {exc.detail}")
    
    error_response = ErrorResponse(
        code=exc.status_code,
        message=str(exc.detail)
    )
    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump(), headers=exc.headers)

def register_error_handlers(app):
    """
    Registra los manejadores de excepciones en la aplicación FastAPI.
    """
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
