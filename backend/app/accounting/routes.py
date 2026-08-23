from fastapi import APIRouter

from app.accounting.catalog import catalog_entries

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.get("/gl-accounts")
def gl_accounts() -> list[dict[str, str]]:
    """The fixed Northstar GL catalog a reviewer may choose from."""
    return catalog_entries()
