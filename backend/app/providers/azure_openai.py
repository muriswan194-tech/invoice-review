import base64
import json
from pathlib import Path

from openai import OpenAI

from app.config import Settings, require_setting
from app.document_review.models import AiExtractionResult


def extract_document_fields(file_path: Path, config: Settings) -> AiExtractionResult:
    client = OpenAI(
        base_url=require_setting(config.openai_endpoint, "AZURE_OPENAI_ENDPOINT"),
        api_key=require_setting(config.openai_api_key, "AZURE_OPENAI_API_KEY"),
    )
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


def extraction_format() -> dict[str, object]:
    nullable_string = {"type": ["string", "null"]}
    properties = {
        "document_type": {"type": "string", "enum": ["invoice", "receipt"]},
        "supplier_name": nullable_string,
        "supplier_gstin": nullable_string,
        "buyer_gstin": nullable_string,
        "supplier_pan": nullable_string,
        "place_of_supply": nullable_string,
        "hsn_sac": nullable_string,
        "invoice_number": nullable_string,
        "taxable_value": nullable_string,
        "cgst": nullable_string,
        "sgst_or_utgst": nullable_string,
        "igst": nullable_string,
        "cess": nullable_string,
        "reverse_charge": {"type": ["boolean", "null"]},
        "purchase_order": nullable_string,
        "project_code": nullable_string,
        "cost_centre": nullable_string,
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
