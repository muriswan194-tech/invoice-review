import argparse
from pathlib import Path

from app.config import settings
from app.providers.azure_openai import classify_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify one document with Azure OpenAI.")
    parser.add_argument("file", type=Path, help="Path to a PDF or image document")
    arguments = parser.parse_args()

    result = classify_document(arguments.file, settings)
    print(f"document_type: {result.document_type}")
    print(f"confidence: {result.confidence}")


if __name__ == "__main__":
    main()