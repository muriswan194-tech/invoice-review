from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Float, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    """One reviewed financial document, with each pipeline stage stored as its own column."""

    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    invoice_number: Mapped[str | None] = mapped_column(String(255))
    saved_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    is_demo: Mapped[bool] = mapped_column(nullable=False, default=False)
    upload_count: Mapped[int] = mapped_column(nullable=False, default=1)
    primary_confidence: Mapped[float | None] = mapped_column(Float)
    document: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    field_sources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conflicts: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    classification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    checks: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    issues: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

class DocumentRepository:
    """The only module that touches the database."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def save_review(self, values: dict[str, Any]) -> DocumentRecord:
        record = DocumentRecord(**values)
        with Session(self.engine) as session:
            session.add(record)
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
            record.supplier_name = supplier_name
            record.invoice_number = invoice_number
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

    def delete_demo_reviews(self) -> list[str]:
        """Clear previous local demo records before starting the fixed demo again."""
        with Session(self.engine) as session:
            records = list(
                session.scalars(select(DocumentRecord).where(DocumentRecord.is_demo.is_(True)))
            )
            saved_names = [record.saved_name for record in records]
            for record in records:
                session.delete(record)
            session.commit()
            return saved_names

    def list_reviews(self) -> list[DocumentRecord]:
        with Session(self.engine) as session:
            return list(session.scalars(select(DocumentRecord).order_by(DocumentRecord.id.desc())))

def build_repository(database_url: str, data_dir: Path) -> DocumentRepository:
    """Create the data directory and a ready-to-use repository."""
    data_dir.mkdir(parents=True, exist_ok=True)
    repository = DocumentRepository(database_url)
    repository.create_tables()
    return repository
