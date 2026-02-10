"""Query generation module for SPARQL queries."""

from .templates import QueryTemplates
from .query_generator import QueryGenerator

__all__ = ["QueryTemplates", "QueryGenerator"]
