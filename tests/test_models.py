import json
from copy import deepcopy

import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from app.models.articles import ArticleResponse
from app.models.faqs import FAQ, FAQList
from app.models.keywords import KeywordResponse
from app.models.metadata import MetadataResponse, MetaDescription, MetaTitle
from app.models.social import SocialResponse, TwitterContent
from app.services.structured import UNSUPPORTED, provider_model
from tests.test_api import ARTICLE, KEYWORDS


@pytest.mark.parametrize("model,limit", [(MetaTitle, 60), (MetaDescription, 160)])
def test_metadata_boundaries(model, limit):
    assert model(text="x" * limit, char_count=0).char_count == limit
    with pytest.raises(ValidationError):
        model(text="x" * (limit + 1), char_count=0)


@pytest.mark.parametrize("count,valid", [(49, False), (50, True), (150, True), (151, False)])
def test_faq_word_boundaries(count, valid):
    if valid:
        assert FAQ(question="¿Cómo?", answer="palabra " * count)
    else:
        with pytest.raises(ValidationError):
            FAQ(question="¿Cómo?", answer="palabra " * count)


def test_h3_cannot_start_article():
    data = deepcopy(ARTICLE)
    data["sections"][0]["heading_level"] = "H3"
    with pytest.raises(ValidationError):
        ArticleResponse.model_validate(data)


def test_classification_must_cover_all_terms():
    data = deepcopy(KEYWORDS)
    data["intent_classification"].pop()
    with pytest.raises(ValidationError):
        KeywordResponse.model_validate(data)


def test_x_counts_complete_post():
    tail = " Guarda. #SEO"
    assert TwitterContent(text="a" * (280 - len(tail)) + tail, hashtags=["#SEO"], call_to_action="Guarda.")
    with pytest.raises(ValidationError):
        TwitterContent(text="a" * (281 - len(tail)) + tail, hashtags=["#SEO"], call_to_action="Guarda.")
    with pytest.raises(ValidationError):
        TwitterContent(text="😀" * 140 + tail, hashtags=["#SEO"], call_to_action="Guarda.")


@pytest.mark.parametrize("model", [KeywordResponse, ArticleResponse, MetadataResponse, FAQList, SocialResponse])
def test_strict_sdk_schema(model):
    schema = to_strict_json_schema(provider_model(model))
    json.dumps(schema)

    def visit(node):
        if isinstance(node, dict):
            assert not (set(node) & UNSUPPORTED)
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)


def test_x_short_url_budget():
    tail = " https://a.co Guarda. #SEO"
    with pytest.raises(ValidationError):
        TwitterContent(text="a" * (280 - len(tail)) + tail, hashtags=["#SEO"], call_to_action="Guarda.")


def test_public_schema_keeps_constraints():
    schema = MetaTitle.model_json_schema()
    assert schema["properties"]["text"]["maxLength"] == 60
