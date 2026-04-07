"""Data models for the application."""

from dataclasses import dataclass


@dataclass
class User:
    """A user in the system."""

    id: int
    name: str
    email: str
