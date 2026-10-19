"""Adaptación del JSON Schema al subconjunto de Azure, sin perder validaciones.

El esquema público de FastAPI conserva todos los límites. Solo el esquema enviado
al proveedor omite restricciones no soportadas; Pydantic las valida al parsear.
"""

from functools import lru_cache

from pydantic import BaseModel

UNSUPPORTED = frozenset(
    {
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minItems",
        "maxItems",
        "uniqueItems",
        "default",
    }
)


def compatible_schema(node):
    if isinstance(node, dict):
        return {key: compatible_schema(value) for key, value in node.items() if key not in UNSUPPORTED}
    if isinstance(node, list):
        return [compatible_schema(value) for value in node]
    return node


@lru_cache
def provider_model(model: type[BaseModel]) -> type[BaseModel]:
    class ProviderModel(model):
        @classmethod
        def model_json_schema(cls, *args, **kwargs):
            return compatible_schema(super().model_json_schema(*args, **kwargs))

    ProviderModel.__name__ = model.__name__
    return ProviderModel
