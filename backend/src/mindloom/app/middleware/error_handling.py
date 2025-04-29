import logging
import traceback
from typing import Callable, Awaitable

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def http_error_handler(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Catch and handle HTTP exceptions and standard Python exceptions."""
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        # Let FastAPI handle its own HTTPExceptions
        raise exc
    except RequestValidationError as exc:
        # Handle Pydantic validation errors specifically for request bodies
        # Use status 422 Unprocessable Entity
        logger.warning(f"Request validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )
    except ValidationError as exc:
        # Handle Pydantic validation errors that might occur elsewhere (e.g., response models)
        # Often indicates a server-side issue with data processing
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
        # Prepare detailed traceback for logging (optional: could be omitted in production)
        tb_str = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        logger.error("\n".join(tb_str))

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."}, # Avoid leaking details
        )
