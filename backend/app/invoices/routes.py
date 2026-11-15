import json
import traceback
from secrets import token_hex
from typing import Literal

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.config import APP_CONFIG, settings
from app.invoices.repository import build_repository
from app.invoices.service import (
    ReviewError,
    apply_corrections,
    create_demo_review,
    process_document,
    process_document_events,
    review_payload,
)

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

router = APIRouter(prefix="/invoices", tags=["invoices"])
repository = build_repository(APP_CONFIG.database_url, APP_CONFIG.data_dir)


class FieldCorrections(BaseModel):
    fields: dict[str, str | None] = Field(min_length=1)


@router.post("/upload")
def upload_invoice(
    file: UploadFile,
    document_type: Literal["invoice"] = Form("invoice"),
) -> dict[str, object]:
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Only PDF, PNG, and JPEG files are supported.")

    content = file.file.read(APP_CONFIG.max_upload_bytes + 1)
    if len(content) > APP_CONFIG.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Files must be 4 MB or smaller.")

    APP_CONFIG.upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{token_hex(16)}{extension}"
    saved_path = APP_CONFIG.upload_dir / saved_name
    saved_path.write_bytes(content)

    try:
        return process_document(
            file_path=saved_path,
            saved_name=saved_name,
            original_filename=file.filename or saved_name,
            document_type=document_type,
            config=settings,
            repository=repository,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Document analysis failed.") from error


@router.post("/upload/stream")
def upload_invoice_stream(
    file: UploadFile,
    document_type: Literal["invoice"] = Form("invoice"),
) -> StreamingResponse:
    """Stream real review-pipeline progress while a single upload is processed."""
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Only PDF, PNG, and JPEG files are supported.")

    content = file.file.read(APP_CONFIG.max_upload_bytes + 1)
    if len(content) > APP_CONFIG.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Files must be 4 MB or smaller.")

    APP_CONFIG.upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{token_hex(16)}{extension}"
    saved_path = APP_CONFIG.upload_dir / saved_name
    saved_path.write_bytes(content)

    def stream() -> object:
        try:
            for event in process_document_events(
                file_path=saved_path,
                saved_name=saved_name,
                original_filename=file.filename or saved_name,
                document_type=document_type,
                config=settings,
                repository=repository,
            ):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except ValueError as error:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(error)})}\n\n"
        except Exception:
            traceback.print_exc()
            yield 'data: {"event": "error", "detail": "Document analysis failed."}\n\n'

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/demo")
def open_demo_review() -> dict[str, object]:
    """Open the fixed fictional review without calling any Azure service."""
    try:
        return create_demo_review(repository)
    except ReviewError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/history")
def invoice_history() -> list[dict[str, object]]:
    return [review_payload(record) for record in repository.list_reviews()]


@router.get("/{record_id}")
def get_review(record_id: int) -> dict[str, object]:
    record = repository.get_review(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="This review was not found.")
    return review_payload(record)


@router.get("/{record_id}/document")
def get_review_document(record_id: int) -> FileResponse:
    """Return the original upload for one stored review, without exposing local paths."""
    record = repository.get_review(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="This review was not found.")

    upload_dir = APP_CONFIG.upload_dir.resolve()
    document_path = (upload_dir / record.saved_name).resolve()
    if not document_path.is_relative_to(upload_dir) or not document_path.is_file():
        raise HTTPException(status_code=404, detail="The original document is no longer available.")

    media_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    return FileResponse(
        path=document_path,
        media_type=media_types.get(document_path.suffix.lower(), "application/octet-stream"),
        content_disposition_type="inline",
        filename=record.original_filename,
    )


@router.put("/{record_id}")
def correct_review(record_id: int, corrections: FieldCorrections) -> dict[str, object]:
    try:
        return apply_corrections(record_id, corrections.fields, settings, repository)
    except ReviewError as error:
        raise HTTPException(status_code=status_for(error), detail=str(error)) from error


@router.delete("/{record_id}")
def delete_invoice(record_id: int) -> dict[str, object]:
    saved_name = repository.delete_review(record_id)
    if saved_name is None:
        raise HTTPException(status_code=404, detail="This review was not found.")

    (APP_CONFIG.upload_dir / saved_name).unlink(missing_ok=True)
    return {"record_id": record_id, "status": "deleted"}


def status_for(error: ReviewError) -> int:
    """Not found is a 404; every other workflow refusal is a 409."""
    return 404 if "was not found" in str(error) else 409
