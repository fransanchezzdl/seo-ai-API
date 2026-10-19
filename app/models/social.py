"""El texto/caption es la publicación completa, incluyendo CTA y hashtags."""

import re
from typing import Literal

from pydantic import Field, model_validator

from app.models.common import Model, Text, unique

TWITTER_MAX = 280
Platform = Literal["twitter", "linkedin", "instagram", "facebook"]


class SocialRequest(Model):
    article_title: Text = Field(max_length=250)
    article_content: Text = Field(max_length=50000)
    target_platforms: list[Platform] = Field(
        default_factory=lambda: ["twitter", "linkedin", "instagram", "facebook"],
        min_length=1,
        max_length=4,
    )

    @model_validator(mode="after")
    def distinct(self):
        if not unique(self.target_platforms):
            raise ValueError("No repitas plataformas")
        return self


class SocialContent(Model):
    hashtags: list[Text] = Field(min_length=1, max_length=10)
    call_to_action: Text

    @model_validator(mode="after")
    def complete_post(self):
        text = getattr(self, "text", getattr(self, "caption", ""))
        if self.call_to_action not in text:
            raise ValueError("Incluye el CTA literalmente en la publicación")
        if not unique(self.hashtags):
            raise ValueError("No repitas hashtags")
        for tag in self.hashtags:
            if not tag.startswith("#") or len(tag) < 2 or not tag[1:].isalnum() or tag not in text:
                raise ValueError("Cada hashtag debe ser #alfanumérico y aparecer en el texto")
        return self


class TwitterContent(SocialContent):
    text: Text = Field(max_length=TWITTER_MAX)

    @model_validator(mode="after")
    def conservative_x_length(self):
        # Cota conservadora para Unicode; los enlaces cortos reservan al menos
        # 23 unidades. No se aprovecha el acortamiento de enlaces largos.
        length = sum(
            1
            if ord(c) <= 0x10FF
            or 0x2000 <= ord(c) <= 0x200D
            or 0x2010 <= ord(c) <= 0x201F
            or 0x2032 <= ord(c) <= 0x2037
            else 2
            for c in self.text
        )
        for link in re.findall(r"https?://[^\s]+|www\.[^\s]+", self.text):
            length += max(0, 23 - len(link))
        if length > TWITTER_MAX:
            raise ValueError("Publicación X excede 280 unidades ponderadas")
        return self


class LinkedInContent(SocialContent):
    text: Text = Field(max_length=3000)


class InstagramContent(SocialContent):
    caption: Text = Field(max_length=2200)


class FacebookContent(SocialContent):
    text: Text = Field(max_length=2000, description="Límite editorial para resúmenes breves")


class SocialResponse(Model):
    twitter: TwitterContent | None
    linkedin: LinkedInContent | None
    instagram: InstagramContent | None
    facebook: FacebookContent | None
