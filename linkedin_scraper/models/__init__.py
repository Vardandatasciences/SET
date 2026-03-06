"""Pydantic data models for LinkedIn scraper."""

from .person import Person, Experience, Education, Contact, Accomplishment, Interest, Post

__all__ = [
    "Person",
    "Experience",
    "Education",
    "Contact",
    "Accomplishment",
    "Interest",
    "Post",
]

