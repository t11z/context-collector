"""Authentication routes."""


def login(username: str, password: str) -> bool:
    """Handle user login."""
    return username == "admin" and password == "secret"


def logout() -> None:
    """Handle user logout."""
    pass
