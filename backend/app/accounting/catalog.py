from typing import Final

GL_ACCOUNTS: Final[dict[str, str]] = {
    "6100": "Cleaning services",
    "6110": "Maintenance services",
    "6120": "Electrical and plumbing",
    "6130": "Fuel and travel",
    "6200": "Equipment and supplies",
}


def is_valid_account(account_code: str) -> bool:
    """A reviewer may only select an account that exists in the fixed Northstar catalog."""
    return account_code in GL_ACCOUNTS


def account_name(account_code: str) -> str | None:
    return GL_ACCOUNTS.get(account_code)


def catalog_entries() -> list[dict[str, str]]:
    """The catalog in the shape the interface consumes."""
    return [{"code": code, "name": name} for code, name in GL_ACCOUNTS.items()]
