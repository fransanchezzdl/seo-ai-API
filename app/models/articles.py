"""Artículo con un H1 y secciones H2/H3 ordenadas."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.common import Model, Text, unique


class ArticleRequest(Model):
    main_keyword: Text = Field(max_length=120)
    secondary_keywords: list[Text] = Field(default_factory=list, max_length=15)
    word_count: int = Field(default=800, ge=300, le=2500, strict=True)
    tone: Text = Field(default="profesional y cercano", max_length=120)


class ArticleSection(Model):
    heading_level: Literal["H2", "H3"]
    title: Text
    content: Text


class ArticleResponse(Model):
    title: Text = Field(description="Único H1 del artículo")
    sections: list[ArticleSection] = Field(min_length=3, max_length=25)
    keyword_density: float = Field(
        ge=0, le=100, description="Ocurrencias exactas / palabras × 100, calculado por el servidor"
    )
    call_to_actions: list[Text] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def hierarchy(self):
        if self.sections[0].heading_level != "H2":
            raise ValueError("El primer encabezado debe ser H2; cada H3 depende del H2 anterior")
        if not any(s.heading_level == "H3" for s in self.sections):
            raise ValueError("Incluye al menos un H3 bajo un H2")
        if not unique([s.title for s in self.sections]):
            raise ValueError("Los encabezados deben ser únicos")
        return self
