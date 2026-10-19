"""Metadatos completos: se rechaza el exceso, sin cortar frases ni keywords."""

from pydantic import Field, model_validator

from app.models.common import Model, Text, unique

META_TITLE_MAX = 60
META_DESCRIPTION_MAX = 160


class MetadataRequest(Model):
    article_title: Text = Field(max_length=250)
    main_keyword: Text = Field(max_length=50)
    article_excerpt: Text = Field(max_length=10000)


class MetaTitle(Model):
    text: Text = Field(max_length=META_TITLE_MAX)
    char_count: int

    @model_validator(mode="after")
    def count(self):
        self.char_count = len(self.text)
        return self


class MetaDescription(Model):
    text: Text = Field(max_length=META_DESCRIPTION_MAX)
    char_count: int

    @model_validator(mode="after")
    def count(self):
        self.char_count = len(self.text)
        return self


class MetadataResponse(Model):
    meta_titles: list[MetaTitle] = Field(min_length=3, max_length=5)
    meta_descriptions: list[MetaDescription] = Field(min_length=3, max_length=5)

    @model_validator(mode="after")
    def distinct(self):
        for variants in (self.meta_titles, self.meta_descriptions):
            if not unique([v.text for v in variants]):
                raise ValueError("Las variantes deben ser distintas")
        return self
