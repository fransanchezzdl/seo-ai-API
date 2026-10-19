"""Endpoint de articles."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models.articles import ArticleRequest, ArticleResponse
from app.services import seo_service

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.post("/generate", response_model=ArticleResponse, responses=ERROR_RESPONSES)
def generate_article(request: ArticleRequest) -> ArticleResponse:
    return seo_service.generate_article(request)
