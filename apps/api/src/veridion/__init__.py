"""Veridion — evidence-first company intelligence."""

__version__ = "0.1.0"

# Versions recorded on every assessment run so results stay reproducible.
# Bump the relevant constant whenever its behaviour changes.
PIPELINE_VERSION = "pipeline-1.0.0"  # PDF parsing, passage segmentation, table extraction
EXTRACTION_VERSION = "extract-1.0.0"  # numbers, units, periods, metric detection
RULES_VERSION = "rules-1.0.1"  # deterministic element checks and status logic
PROMPT_VERSION = "prompt-1.1.0"  # LLM assessment prompt and output schema
