"""Endpoint de social."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models.social import SocialRequest, SocialResponse
from app.services import seo_service

router = APIRouter(prefix="/api/social", tags=["social"])


@router.post("/summaries", response_model=SocialResponse, responses=ERROR_RESPONSES)
def generate_social(request: SocialRequest) -> SocialResponse:
    return seo_service.generate_social(request)
