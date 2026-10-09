"""SQLAlchemy models.

The claim-to-evidence graph is modelled relationally:

    Requirement ──< Finding >── AssessmentRun ── input manifest (Document hashes)
                       │
                       ├──< FindingEvidence >── Passage ── Document ── Company
                       ├──< Review   (append-only human corrections)
                       └──< Action   (remediation linked to the gap that triggered it)

Every query against tenant data filters by `org_id`.
"""

from veridion.models.assessment import Action, AssessmentRun, Finding, FindingEvidence, Review
from veridion.models.documents import Company, CompanyPeer, Document, ExtractedMetric, Passage
from veridion.models.identity import AuditEvent, Enquiry, Membership, Organization, UsageEvent, User
from veridion.models.jobs import Job, LLMCacheEntry
from veridion.models.requirements import ApplicabilityDecision, Requirement, RequirementSet

__all__ = [
    "Action",
    "ApplicabilityDecision",
    "AssessmentRun",
    "AuditEvent",
    "Company",
    "CompanyPeer",
    "Document",
    "Enquiry",
    "ExtractedMetric",
    "Finding",
    "FindingEvidence",
    "Job",
    "LLMCacheEntry",
    "Membership",
    "Organization",
    "Passage",
    "Requirement",
    "RequirementSet",
    "Review",
    "UsageEvent",
    "User",
]
