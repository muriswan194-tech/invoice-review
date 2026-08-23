import base64
import json
from pathlib import Path

from openai import OpenAI

from app.accounting.catalog import GL_ACCOUNTS
from app.config import Settings
from app.correction_email.models import CorrectionEmailContext, CorrectionEmailDraft
from app.document_review.models import AiExtractionResult, ClassificationResult, GlSuggestion


def classify_document(file_path: Path, config: Settings) -> ClassificationResult:
    client = OpenAI(base_url=config.openai_endpoint, api_key=config.openai_api_key)
    encoded_file = base64.b64encode(file_path.read_bytes()).decode("ascii")
    mime_type = mime_type_for(file_path)
    response = client.responses.create(
        model=config.openai_deployment,
        input=[
            {
                "role": "user",
                "content": [
                    classification_content(file_path, mime_type, encoded_file),
                    {
                        "type": "input_text",
                        "text": "Classify this document as an invoice or receipt.",
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "document_classification",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "document_type": {"type": "string", "enum": ["invoice", "receipt"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["document_type", "confidence"],
                    "additionalProperties": False,
                },
            }
        },
    )
    output = json.loads(response.output_text)
    return ClassificationResult.model_validate(output)


def extract_document_fields(file_path: Path, config: Settings) -> AiExtractionResult:
    client = OpenAI(base_url=config.openai_endpoint, api_key=config.openai_api_key)
    encoded_file = base64.b64encode(file_path.read_bytes()).decode("ascii")
    mime_type = mime_type_for(file_path)
    response = client.responses.create(
        model=config.openai_deployment,
        input=[
            {
                "role": "user",
                "content": [
                    classification_content(file_path, mime_type, encoded_file),
                    {
                        "type": "input_text",
                        "text": (
                            "Extract invoice or receipt fields. Return null when a field is not "
                            "visible. Do not guess values."
                        ),
                    },
                ],
            }
        ],
        text={"format": extraction_format()},
    )
    return AiExtractionResult.model_validate(json.loads(response.output_text))


def suggest_gl_account(document_fields: dict[str, object], config: Settings) -> GlSuggestion:
    client = OpenAI(base_url=config.openai_endpoint, api_key=config.openai_api_key)
    catalog = [{"code": code, "name": name} for code, name in GL_ACCOUNTS.items()]
    response = client.responses.create(
        model=config.openai_deployment,
        input=(
            "Choose the best account from this fixed catalog. Return only a catalog code and "
            f"name. Document fields: {json.dumps(document_fields, default=str)}. Catalog: "
            f"{json.dumps(catalog)}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "gl_account_suggestion",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "account_code": {"type": "string", "enum": list(GL_ACCOUNTS)},
                        "account_name": {"type": "string", "enum": list(GL_ACCOUNTS.values())},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["account_code", "account_name", "confidence"],
                    "additionalProperties": False,
                },
            }
        },
    )
    suggestion = GlSuggestion.model_validate(json.loads(response.output_text))
    if GL_ACCOUNTS.get(suggestion.account_code) != suggestion.account_name:
        raise ValueError("Azure OpenAI returned an inconsistent GL account.")
    return suggestion


def draft_correction_email(
    context: CorrectionEmailContext,
    config: Settings,
) -> CorrectionEmailDraft:
    """Ask Azure OpenAI to word a correction request. Eligibility was already decided in code."""
    client = OpenAI(base_url=config.openai_endpoint, api_key=config.openai_api_key)
    response = client.responses.create(
        model=config.openai_deployment,
        input=(
            "Write a short, polite correction request from the finance team at Northstar "
            "Facilities B.V. to a supplier. Write in English. State only the listed problems, "
            "ask for a corrected document, and do not invent facts, amounts, deadlines, or "
            "contact details. "
            f"Context: {context.model_dump_json()}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "correction_email_draft",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["subject", "body"],
                    "additionalProperties": False,
                },
            }
        },
    )
    return CorrectionEmailDraft.model_validate(json.loads(response.output_text))


def extraction_format() -> dict[str, object]:
    nullable_string = {"type": ["string", "null"]}
    properties = {
        "document_type": {"type": "string", "enum": ["invoice", "receipt"]},
        "supplier_name": nullable_string,
        "supplier_vat_id": nullable_string,
        "customer_vat_id": nullable_string,
        "invoice_number": nullable_string,
        "purchase_order": nullable_string,
        "invoice_date": nullable_string,
        "due_date": nullable_string,
        "merchant_name": nullable_string,
        "transaction_date": nullable_string,
        "subtotal": nullable_string,
        "vat_total": nullable_string,
        "total": nullable_string,
        "currency": nullable_string,
    }
    return {
        "type": "json_schema",
        "name": "document_field_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    }


def mime_type_for(file_path: Path) -> str:
    mime_types: dict[str, str] = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    try:
        return mime_types[file_path.suffix.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported document type: {file_path.suffix}") from error


def classification_content(file_path: Path, mime_type: str, encoded_file: str) -> dict[str, str]:
    data_url = f"data:{mime_type};base64,{encoded_file}"
    if file_path.suffix.lower() == ".pdf":
        return {
            "type": "input_file",
            "filename": file_path.name,
            "file_data": data_url,
        }

    return {"type": "input_image", "image_url": data_url}