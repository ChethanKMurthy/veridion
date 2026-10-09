"""Portable column types."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# JSONB on PostgreSQL (indexable, compact), JSON elsewhere.
JSONType = JSON().with_variant(JSONB(), "postgresql")

ID_LEN = 40
