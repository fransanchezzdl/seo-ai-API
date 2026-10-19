"""Preguntas, respuestas y JSON-LD listo para integrar."""

import json

from pydantic import Field, field_validator, model_validator

from app.models.common import Model, Text, unique, words


class FAQRequest(Model):
    article_content: Text = Field(min_length=100, max_length=50000)
    max_questions: int = Field(default=5, ge=1, le=10, strict=True)


class FAQ(Model):
    question: Text
    answer: Text

    @field_validator("answer")
    @classmethod
    def answer_length(cls, value):
        if not 50 <= len(words(value)) <= 150:
            raise ValueError("Cada respuesta debe tener entre 50 y 150 palabras")
        return value


class FAQList(Model):
    faqs: list[FAQ] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def distinct(self):
        if not unique([f.question for f in self.faqs]):
            raise ValueError("Las preguntas deben ser distintas")
        return self


class FAQResponse(FAQList):
    json_ld_schema: str

    @model_validator(mode="after")
    def schema_matches(self):
        expected = faq_schema(self.faqs)
        if json.loads(self.json_ld_schema) != expected:
            raise ValueError("JSON-LD no coincide con las FAQs")
        return self


def faq_schema(faqs: list[FAQ]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": faq.question, "acceptedAnswer": {"@type": "Answer", "text": faq.answer}}
            for faq in faqs
        ],
    }
