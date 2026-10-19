"""Errores públicos estables; nunca exponer claves ni respuestas internas."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from app.config import ConfigurationError
from app.services.seo_service import ContentRefusedError, GenerationError

logger = logging.getLogger(__name__)
ERROR_RESPONSES = {
    code: {"description": text}
    for code, text in {
        422: "Entrada inválida o contenido rechazado",
        429: "Límite del proveedor",
        502: "Respuesta del proveedor inválida",
        503: "Servicio no disponible",
        504: "Tiempo de espera agotado",
    }.items()
}


async def service_error_handler(request: Request, error: Exception) -> JSONResponse:
    status, detail = 502, "El proveedor no pudo generar una respuesta válida. Inténtalo de nuevo."
    if isinstance(error, ContentRefusedError):
        status, detail = 422, "El modelo ha rechazado el contenido solicitado."
    elif isinstance(error, ConfigurationError):
        status, detail = 503, "Falta configurar el proveedor de IA. Revisa las variables de entorno."
    elif isinstance(error, APITimeoutError):
        status, detail = 504, "Se agotó el tiempo de espera del proveedor de IA."
    elif isinstance(error, RateLimitError):
        status, detail = 429, "Límite de peticiones o cuota del proveedor alcanzado."
    elif isinstance(error, (AuthenticationError, PermissionDeniedError)):
        status, detail = 503, "Credenciales o permisos del proveedor incorrectos."
    elif isinstance(error, APIConnectionError):
        status, detail = 503, "No se pudo conectar con el proveedor de IA."
    logger.warning("generation_failed path=%s error_type=%s status=%s", request.url.path, type(error).__name__, status)
    return JSONResponse(status_code=status, content={"detail": detail})


def install_error_handlers(app):
    for error_type in (OpenAIError, ConfigurationError, GenerationError):
        app.add_exception_handler(error_type, service_error_handler)
