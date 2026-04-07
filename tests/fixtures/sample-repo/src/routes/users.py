"""User management routes."""


def list_users() -> list[str]:
    """List all users."""
    return ["alice", "bob"]


def get_user(user_id: int) -> str:
    """Get a user by ID."""
    return f"User {user_id}"
