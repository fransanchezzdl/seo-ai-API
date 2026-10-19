"""Endpoint de keywords."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models.keywords import KeywordRequest, KeywordResponse
from app.services import seo_service

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.post("/generate", response_model=KeywordResponse, responses=ERROR_RESPONSES)
def generate_keywords(request: KeywordRequest) -> KeywordResponse:
    return seo_service.generate_keywords(request)
