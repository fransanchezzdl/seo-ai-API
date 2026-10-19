"""Endpoint de metadata."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models.metadata import MetadataRequest, MetadataResponse
from app.services import seo_service

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.post("/generate", response_model=MetadataResponse, responses=ERROR_RESPONSES)
def generate_metadata(request: MetadataRequest) -> MetadataResponse:
    return seo_service.generate_metadata(request)
