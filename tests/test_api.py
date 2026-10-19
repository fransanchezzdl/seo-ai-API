"""Pruebas HTTP con SDK simulado: cero llamadas ni consumo de crédito."""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, RateLimitError

from app.config import ConfigurationError
from app.main import app
from app.services import seo_service as service

client = TestClient(app)

FAQ_ANSWER = (
    "Para preparar café en casa, empieza seleccionando granos frescos y agua limpia. "
    "Ajusta la molienda al método que utilices y pesa las cantidades para repetir "
    "el resultado. Prueba la bebida antes de cambiar una variable cada vez. "
    "Limpia el equipo después de usarlo y conserva los granos en un recipiente "
    "cerrado, lejos de la luz y del calor."
)
TERMS = [
    "café",
    "granos",
    "molienda",
    "comprar café fresco",
    "cómo moler café",
    "café para preparar en casa",
    "comprar granos tostados",
    "mejor agua para café",
    "¿Cómo preparar café?",
    "¿Qué molienda utilizar?",
    "¿Cómo conservar granos?",
]
KEYWORDS = {
    "seed_keywords": TERMS[:3],
    "long_tail_keywords": TERMS[3:8],
    "questions": TERMS[8:],
    "intent_classification": [
        {"keyword": t, "intent": "transaccional" if t.startswith("comprar") else "informacional"} for t in TERMS
    ],
}
ARTICLE = {
    "title": "Café en casa: guía práctica",
    "keyword_density": 99,
    "sections": [
        {"heading_level": "H2", "title": "Preparación", "content": FAQ_ANSWER + " " + FAQ_ANSWER},
        {"heading_level": "H3", "title": "Ajustes", "content": FAQ_ANSWER + " " + FAQ_ANSWER},
        {"heading_level": "H2", "title": "Siguiente paso", "content": FAQ_ANSWER + " Prueba estos pasos hoy."},
    ],
    "call_to_actions": ["Prueba estos pasos hoy."],
}
METADATA = {
    "meta_titles": [
        {"text": t, "char_count": -1}
        for t in ["Café: aprende a prepararlo", "Café en casa: guía práctica", "Café: descubre cómo elegirlo"]
    ],
    "meta_descriptions": [
        {"text": t, "char_count": -1}
        for t in [
            "Prepara café con pasos sencillos. Descubre la guía.",
            "Elige tu café y mejora la molienda. Aprende cómo hacerlo.",
            "Disfruta del café en casa. Explora nuestros consejos.",
        ]
    ],
}
SOCIAL = {
    p: {
        "caption" if p == "instagram" else "text": "Aprende a preparar café. Guarda esta guía. #Café",
        "hashtags": ["#Café"],
        "call_to_action": "Guarda esta guía.",
    }
    for p in ["twitter", "linkedin", "instagram", "facebook"]
}
CASES = [
    ("/api/keywords/generate", {"topic": "café"}, KEYWORDS),
    ("/api/articles/generate", {"main_keyword": "café", "word_count": 300}, ARTICLE),
    (
        "/api/metadata/generate",
        {"article_title": "Café en casa", "main_keyword": "café", "article_excerpt": FAQ_ANSWER},
        METADATA,
    ),
    (
        "/api/faqs/extract",
        {"article_content": FAQ_ANSWER, "max_questions": 1},
        {"faqs": [{"question": "¿Cómo preparar café?", "answer": FAQ_ANSWER}]},
    ),
    ("/api/social/summaries", {"article_title": "Café", "article_content": FAQ_ANSWER}, SOCIAL),
]


@pytest.fixture
def sdk(monkeypatch):
    parse = Mock()
    monkeypatch.setattr(
        service, "get_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    )
    return parse


def respond(sdk, data):
    def parse(**kwargs):
        parsed = kwargs["response_format"].model_validate(deepcopy(data))
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(parsed=parsed, refusal=None))]
        )

    sdk.side_effect = parse


@pytest.mark.parametrize("path,payload,data", CASES)
def test_all_endpoints_structured_response(sdk, path, payload, data):
    respond(sdk, data)
    result = client.post(path, json=payload)
    assert result.status_code == 200, result.text
    assert sdk.call_count == 1
    call = sdk.call_args.kwargs
    assert call["response_format"] is not None
    assert json.loads(call["messages"][1]["content"])
    body = result.json()
    if "keyword_density" in body:
        assert 0 < body["keyword_density"] <= 3
    if "meta_titles" in body:
        assert all(v["char_count"] == len(v["text"]) for v in body["meta_titles"] + body["meta_descriptions"])
    if "json_ld_schema" in body:
        schema = json.loads(body["json_ld_schema"])
        assert schema["@type"] == "FAQPage"
        assert schema["mainEntity"][0]["acceptedAnswer"]["text"] == body["faqs"][0]["answer"]


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/keywords/generate", {"topic": "   "}),
        ("/api/keywords/generate", {"topic": "café", "unknown": True}),
        ("/api/articles/generate", {"main_keyword": "café", "word_count": 299}),
        ("/api/articles/generate", {"main_keyword": "café", "word_count": 2501}),
        ("/api/faqs/extract", {"article_content": FAQ_ANSWER, "max_questions": 11}),
        ("/api/faqs/extract", {"article_content": FAQ_ANSWER, "max_questions": True}),
        ("/api/social/summaries", {"article_title": "a", "article_content": "b", "target_platforms": ["tiktok"]}),
        ("/api/social/summaries", {"article_title": "a", "article_content": "b", "target_platforms": []}),
        (
            "/api/social/summaries",
            {"article_title": "a", "article_content": "b", "target_platforms": ["twitter", "twitter"]},
        ),
    ],
)
def test_bad_input_never_calls_provider(sdk, path, payload):
    assert client.post(path, json=payload).status_code == 422
    sdk.assert_not_called()


@pytest.mark.parametrize("platform", ["twitter", "linkedin", "instagram", "facebook"])
def test_only_requested_platform(sdk, platform):
    respond(sdk, SOCIAL)
    body = client.post(CASES[4][0], json={**CASES[4][1], "target_platforms": [platform]}).json()
    assert body[platform]
    assert all(v is None for p, v in body.items() if p != platform)


def test_missing_requested_platform_fails(sdk):
    respond(sdk, {**SOCIAL, "twitter": None})
    assert client.post(CASES[4][0], json=CASES[4][1]).status_code == 502
    assert sdk.call_count == 2


def test_repair_invalid_output(sdk):
    calls = 0

    def parse(**kwargs):
        nonlocal calls
        calls += 1
        data = deepcopy(METADATA)
        if calls == 1:
            data["meta_titles"][0]["text"] = "x" * 61
        parsed = kwargs["response_format"].model_validate(data)
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(parsed=parsed, refusal=None))]
        )

    sdk.side_effect = parse
    assert client.post(CASES[2][0], json=CASES[2][1]).status_code == 200
    assert calls == 2


def test_missing_keyword_retries_and_fails(sdk):
    data = deepcopy(METADATA)
    data["meta_titles"][0]["text"] = "Guía de bebidas"
    respond(sdk, data)
    assert client.post(CASES[2][0], json=CASES[2][1]).status_code == 502
    assert sdk.call_count == 2


@pytest.mark.parametrize(
    "kind,status", [("timeout", 504), ("connection", 503), ("rate", 429), ("auth", 503), ("bad", 502)]
)
def test_provider_errors_are_sanitized(sdk, kind, status):
    req = httpx.Request("POST", "https://example.test")
    response = httpx.Response(400, request=req)
    errors = {
        "timeout": APITimeoutError(request=req),
        "connection": APIConnectionError(request=req),
        "rate": RateLimitError("SECRET", response=response, body=None),
        "auth": AuthenticationError("SECRET", response=response, body=None),
        "bad": BadRequestError("SECRET", response=response, body=None),
    }
    sdk.side_effect = errors[kind]
    result = client.post(CASES[0][0], json=CASES[0][1])
    assert result.status_code == status
    assert "SECRET" not in result.text


def test_missing_config(monkeypatch):
    def fail():
        raise ConfigurationError("private detail")

    monkeypatch.setattr(service, "get_client", fail)
    assert client.post(CASES[0][0], json=CASES[0][1]).status_code == 503


@pytest.mark.parametrize(
    "choices,status",
    [
        ([], 502),
        ([SimpleNamespace(finish_reason="stop", message=SimpleNamespace(parsed=None, refusal="no"))], 422),
        ([SimpleNamespace(finish_reason="length", message=SimpleNamespace(parsed=None, refusal=None))], 502),
    ],
)
def test_empty_refused_and_truncated(sdk, choices, status):
    sdk.return_value = SimpleNamespace(choices=choices)
    assert client.post(CASES[0][0], json=CASES[0][1]).status_code == status


def test_docs_and_health():
    assert client.get("/").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    for path, _, _ in CASES:
        assert "post" in schema["paths"][path]


def test_real_sdk_parsing_with_mock_transport(monkeypatch):
    """Ejercita serialización y parsing reales del SDK sin tocar la red."""
    from openai import AzureOpenAI

    from app.services.structured import UNSUPPORTED

    def transport(request):
        body = json.loads(request.content)
        assert "/deployments/class-demo/chat/completions" in str(request.url)
        assert body["response_format"]["json_schema"]["strict"] is True
        schema_text = json.dumps(body["response_format"]["json_schema"]["schema"])
        assert all(f'"{key}":' not in schema_text for key in UNSUPPORTED)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-4o-mini",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(KEYWORDS),
                            "refusal": None,
                        },
                    }
                ],
            },
        )

    with AzureOpenAI(
        api_key="fake",
        azure_endpoint="https://example.test",
        api_version="2024-10-21",
        http_client=httpx.Client(transport=httpx.MockTransport(transport)),
    ) as azure:
        monkeypatch.setattr(service, "get_client", lambda: azure)
        monkeypatch.setattr(service, "OPENAI_MODEL", "class-demo")
        result = client.post(CASES[0][0], json=CASES[0][1])
        assert result.status_code == 200, result.text
        assert result.json() == KEYWORDS


@pytest.mark.parametrize("failure", ["short", "missing_secondary", "missing_cta", "stuffing"])
def test_article_editorial_validation(sdk, failure):
    data = deepcopy(ARTICLE)
    payload = deepcopy(CASES[1][1])
    if failure == "short":
        data["sections"][0]["content"] = "Breve."
        data["sections"][1]["content"] = "Breve."
    elif failure == "missing_secondary":
        payload["secondary_keywords"] = ["espresso"]
    elif failure == "missing_cta":
        data["call_to_actions"] = ["Solicita información."]
    else:
        data["sections"][0]["content"] = "café " * 100
    respond(sdk, data)
    assert client.post(CASES[1][0], json=payload).status_code == 502
    assert sdk.call_count == 2


def test_faq_respects_requested_maximum(sdk):
    respond(
        sdk,
        {
            "faqs": [
                {"question": "¿Cómo preparar café?", "answer": FAQ_ANSWER},
                {"question": "¿Cómo conservarlo?", "answer": FAQ_ANSWER},
            ]
        },
    )
    assert client.post(CASES[3][0], json=CASES[3][1]).status_code == 502


def test_json_ld_is_safe_to_embed(sdk):
    respond(sdk, {"faqs": [{"question": "¿Qué significa </script>?", "answer": FAQ_ANSWER}]})
    result = client.post(CASES[3][0], json=CASES[3][1])
    assert result.status_code == 200
    body = result.json()
    assert "</script>" not in body["json_ld_schema"]
    assert json.loads(body["json_ld_schema"])["mainEntity"][0]["name"] == body["faqs"][0]["question"]
