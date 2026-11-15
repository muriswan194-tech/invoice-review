from fastapi import APIRouter

from app.gst_sources.catalog import GstSource, source_catalog

router = APIRouter(prefix="/gst-sources", tags=["gst-sources"])


@router.get("", response_model=list[GstSource])
def gst_sources() -> list[GstSource]:
    return source_catalog()
