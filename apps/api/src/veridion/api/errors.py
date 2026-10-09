"""Map domain errors to HTTP responses with clear, user-facing messages."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from veridion.assessment.engine import RunError
from veridion.services.documents import DuplicateDocumentError, UploadError
from veridion.services.entitlements import PlanLimitError
from veridion.storage import FileMissing


class NotFound(Exception):
    def __init__(self, what: str = "Resource") -> None:
        super().__init__(f"{what} not found")


class Conflict(Exception):
    pass


class RegistrationClosed(Exception):
    pass


def install(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(PlanLimitError)
    async def _plan(_: Request, exc: PlanLimitError):
        return JSONResponse({"detail": str(exc), "limit": exc.limit, "code": "plan_limit"}, status_code=402)

    @app.exception_handler(UploadError)
    async def _upload(_: Request, exc: UploadError):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(DuplicateDocumentError)
    async def _duplicate(_: Request, exc: DuplicateDocumentError):
        return JSONResponse({"detail": str(exc), "code": "duplicate_document", "existing_id": exc.existing_id},
                            status_code=409)

    @app.exception_handler(FileMissing)
    async def _file_missing(_: Request, exc: FileMissing):
        return JSONResponse({"detail": "The stored copy of this document is no longer available. Upload the same "
                                       "file again to restore it.", "code": "file_missing"}, status_code=410)

    @app.exception_handler(RunError)
    async def _run(_: Request, exc: RunError):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(Conflict)
    async def _conflict(_: Request, exc: Conflict):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(RegistrationClosed)
    async def _registration_closed(_: Request, exc: RegistrationClosed):
        return JSONResponse({"detail": str(exc), "code": "registration_closed"}, status_code=403)
