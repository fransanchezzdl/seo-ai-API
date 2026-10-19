"""Endpoint de faqs."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models.faqs import FAQRequest, FAQResponse
from app.services import seo_service

router = APIRouter(prefix="/api/faqs", tags=["faqs"])


@router.post("/extract", response_model=FAQResponse, responses=ERROR_RESPONSES)
def extract_faqs(request: FAQRequest) -> FAQResponse:
    return seo_service.extract_faqs(request)
