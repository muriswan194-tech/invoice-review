import json
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from app.config import Settings
from app.document_review.models import AdvisorRecommendation, ChatMessage, ChatResponse


def advise_invoice_review(
    document: dict[str, Any],
    checks: dict[str, Any],
    issues: list[dict[str, Any]],
    conflicts: list[str],
    gl_suggestion: dict[str, Any],
    config: Settings,
) -> AdvisorRecommendation:
    """Ask the Foundry prompt agent for an explanation of already-computed evidence."""
    project_client = AIProjectClient(
        endpoint=config.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
    )
    openai_client = project_client.get_openai_client()
    evidence = {
        "document": document,
        "checks": checks,
        "issues": issues,
        "conflicts": conflicts,
        "gl_suggestion": gl_suggestion,
    }
    response = openai_client.responses.create(
        input=[
            {
                "role": "user",
                "content": json.dumps(evidence, default=str),
            }
        ],
        extra_body={
            "agent_reference": {
                "name": config.foundry_agent_name,
                "version": config.foundry_agent_version,
                "type": "agent_reference",
            }
        },
    )
    try:
        result = json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise ValueError("The invoice-review advisor returned invalid JSON.") from error
    return AdvisorRecommendation.model_validate(result)


def chat_with_advisor(
    messages: list[ChatMessage],
    config: Settings,
) -> ChatResponse:
    """Send a conversation to the Foundry agent and get a response."""
    project_client = AIProjectClient(
        endpoint=config.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
    )
    openai_client = project_client.get_openai_client()

    # Convert our messages to the format the API expects
    input_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    response = openai_client.responses.create(
        input=input_messages,
        extra_body={
            "agent_reference": {
                "name": config.foundry_agent_name,
                "version": config.foundry_agent_version,
                "type": "agent_reference",
            }
        },
    )
    return ChatResponse(
        role="assistant",
        content=response.output_text,
    )
