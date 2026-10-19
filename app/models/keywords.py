"""Keywords y su intención de búsqueda."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.common import Model, Text, unique


class KeywordRequest(Model):
    topic: Text = Field(max_length=200, examples=["café de especialidad"])
    industry: Text = Field(default="general", max_length=200)
    language: Text = Field(default="español", max_length=50)


class KeywordIntent(Model):
    keyword: Text
    intent: Literal["informacional", "transaccional"]


class KeywordResponse(Model):
    seed_keywords: list[Text] = Field(min_length=3, max_length=10)
    long_tail_keywords: list[Text] = Field(min_length=5, max_length=15)
    questions: list[Text] = Field(min_length=3, max_length=10)
    intent_classification: list[KeywordIntent]

    @model_validator(mode="after")
    def complete_classification(self):
        terms = self.seed_keywords + self.long_tail_keywords + self.questions
        classified = [item.keyword for item in self.intent_classification]
        if not unique(terms) or not unique(classified):
            raise ValueError("No se permiten keywords ni clasificaciones duplicadas")
        if {t.casefold() for t in terms} != {t.casefold() for t in classified}:
            raise ValueError("Clasifica exactamente todas las keywords y preguntas")
        return self
