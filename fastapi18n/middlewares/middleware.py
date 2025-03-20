from starlette.middleware.base import BaseHTTPMiddleware
from ..wrappers import TranslationWrapper
from starlette.requests import Request
from fastapi import Response


class LocalizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling localization based on request parameters or headers.
    It extracts the preferred language from the request and sets it for the translation wrapper.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Intercepts the request, extracts the language preference, and applies localization.

        - First, checks if the "lang" query parameter exists.
        - If not, it falls back to the "Accept-Language" header.
        - The selected language(s) are then passed to the TranslationWrapper.
        - Stores the detected language in `request.state.language` for further use.
        """
        lang = request.query_params.get("lang") or request.headers.get("Accept-Language")
        if lang:
            langs = [l.split(";")[0].strip() for l in lang.split(",")]
            TranslationWrapper.get_instance().set_locale(locales=langs, use_context=True)
            request.state.language = lang
        response: Response = await call_next(request)
        return response
