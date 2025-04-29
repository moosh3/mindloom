import traceback
import logging
from typing import Callable, Awaitable

from fastapi import Request, Response, status, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class CustomErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Catch and handle HTTP exceptions and standard Python exceptions."""
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            # Let FastAPI handle its own HTTPExceptions
            # Re-raising might be okay, or return a JSONResponse directly
            logger.warning(f"HTTPException caught by middleware: {exc.status_code} - {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None)
            )
        except RequestValidationError as exc:
            # Handle Pydantic validation errors specifically for request bodies
            logger.warning(f"Request validation error: {exc.errors()}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": exc.errors()},
            )
        except ValidationError as exc:
            # Handle Pydantic validation errors that might occur elsewhere
            logger.error(f"Pydantic validation error during processing: {exc.errors()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error processing data.", "errors": exc.errors()},
            )
        except Exception as exc:
            # Catch all other exceptions
            logger.exception(
                f"Unhandled exception during request {request.method} {request.url.path}:",
                exc_info=exc
            )
            # Optional: Log traceback
            # tb_str = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
            # logger.error("\n".join(tb_str))

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An unexpected internal server error occurred."}, # Avoid leaking details
            )
