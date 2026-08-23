from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Float, Index, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.invoices.models import InvoiceDocument, invoice_key_parts


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    """One reviewed financial document, with each pipeline stage stored as its own column."""

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_identity", "supplier_key", "invoice_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)
    supplier_key: Mapped[str | None] = mapped_column(String(255))
    invoice_key: Mapped[str | None] = mapped_column(String(255))
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    invoice_number: Mapped[str | None] = mapped_column(String(255))
    saved_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    upload_count: Mapped[int] = mapped_column(nullable=False, default=1)
    primary_confidence: Mapped[float | None] = mapped_column(Float)
    selected_account_code: Mapped[str | None] = mapped_column(String(16))
    document: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    field_sources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conflicts: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    classification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    gl_suggestion: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    advisor: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    checks: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    issues: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)


class DocumentRepository:
    """The only module that touches the database."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)
        # Existing local tutorial databases predate the advisor column.
        with self.engine.begin() as connection:
            columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(documents)"))
            }
            if "advisor" not in columns:
                connection.execute(text("ALTER TABLE documents ADD COLUMN advisor JSON"))

    def invoice_exists(self, document: InvoiceDocument) -> bool:
        supplier_key, invoice_key = invoice_key_parts(document)
        if supplier_key is None or invoice_key is None:
            return False

        with Session(self.engine) as session:
            statement = select(DocumentRecord.id).where(
                DocumentRecord.supplier_key == supplier_key,
                DocumentRecord.invoice_key == invoice_key,
            )
            return session.scalar(statement) is not None

    def save_review(self, values: dict[str, Any]) -> DocumentRecord:
        record = DocumentRecord(**values)
        with Session(self.engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def count_repeat_upload(self, supplier_key: str, invoice_key: str) -> DocumentRecord | None:
        """Count another sighting of an invoice identity already in the database."""
        with Session(self.engine) as session:
            statement = select(DocumentRecord).where(
                DocumentRecord.supplier_key == supplier_key,
                DocumentRecord.invoice_key == invoice_key,
            )
            record = session.scalar(statement)
            if record is None:
                return None
            record.upload_count += 1
            session.commit()
            session.refresh(record)
            return record

    def get_review(self, record_id: int) -> DocumentRecord | None:
        with Session(self.engine) as session:
            return session.get(DocumentRecord, record_id)

    def apply_corrections(
        self,
        record_id: int,
        document: dict[str, Any],
        field_sources: dict[str, Any],
        checks: dict[str, Any],
        issues: list[Any],
        advisor: dict[str, Any],
        supplier_name: str | None,
        invoice_number: str | None,
    ) -> DocumentRecord | None:
        """Store a revalidated document after a reviewer edited one or more fields."""
        with Session(self.engine) as session:
            record = session.get(DocumentRecord, record_id)
            if record is None:
                return None
            record.document = document
            record.field_sources = field_sources
            record.checks = checks
            record.issues = issues
            record.advisor = advisor
            record.supplier_name = supplier_name
            record.invoice_number = invoice_number
            session.commit()
            session.refresh(record)
            return record

    def update_status(self, record_id: int, status: str) -> DocumentRecord | None:
        with Session(self.engine) as session:
            record = session.get(DocumentRecord, record_id)
            if record is None:
                return None
            record.review_status = status
            session.commit()
            session.refresh(record)
            return record

    def update_account(self, record_id: int, account_code: str) -> DocumentRecord | None:
        with Session(self.engine) as session:
            record = session.get(DocumentRecord, record_id)
            if record is None:
                return None
            record.selected_account_code = account_code
            session.commit()
            session.refresh(record)
            return record

    def delete_review(self, record_id: int) -> str | None:
        """Remove one review and return the stored file name so its upload can be deleted."""
        with Session(self.engine) as session:
            record = session.get(DocumentRecord, record_id)
            if record is None:
                return None
            saved_name = record.saved_name
            session.delete(record)
            session.commit()
            return saved_name

    def list_reviews(self) -> list[DocumentRecord]:
        with Session(self.engine) as session:
            return list(session.scalars(select(DocumentRecord).order_by(DocumentRecord.id.desc())))


def build_repository(database_url: str, data_dir: Path) -> DocumentRepository:
    """Create the data directory and a ready-to-use repository."""
    data_dir.mkdir(parents=True, exist_ok=True)
    repository = DocumentRepository(database_url)
    repository.create_tables()
    return repository
