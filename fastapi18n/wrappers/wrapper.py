import gettext
import logging
from typing import Self
from typing_extensions import Optional
import contextvars

# Context variable to store the locale for each request individually.
# This ensures that each request has its own locale without affecting others.
# It prevents race conditions in asynchronous environments.
locale_context = contextvars.ContextVar("locale_context", default=None)


def set_locale(locale: Optional[str]):
    """Set locale context."""
    locale_context.set(locale)


def get_locale() -> Optional[str]:
    """Get locale context."""
    return locale_context.get()


class GetText(str):
    """
    A lazy translation wrapper that stores a message and applies the correct translation
    when converted to a string. This class allows setting a locale explicitly, ensuring
    translations remain consistent even if the global locale changes.

    - The translation occurs when `__str__()` is called.
    - If a locale is provided via `set_locale()`, it is used instead of the default locale.
    """
    _message: str  # The original message before translation
    _locale: Optional[str] = None  # Stores the locale for translation (if explicitly set)

    def __init__(self, message: str):
        """
        Initializes the GetText object with a given message.
        :param message: The text to be translated.
        """
        self._message = message
        self._locale = None  # Locale can be set later using `set_locale()`

    def __str__(self):
        """
        Returns the translated text for the stored message.

        - Calls `gettext()` from `TranslationWrapper` with the stored locale.
        - If no locale is set, it falls back to the default locale.
        :return: Translated string.
        """
        return TranslationWrapper.get_instance().gettext(self._message, lazy=False, locale=self._locale)

    def set_locale(self, locale: str):
        """
        Sets the locale for this specific translation instance.

        - Overrides the default locale from `TranslationWrapper`.
        - Ensures that translation remains consistent even if the global locale changes.

        :param locale: The locale to be used for translation.
        """
        self._locale = locale


class TranslationWrapper:
    """
    Singleton class for managing translations using gettext.

    This class initializes the translation object and provides
    a method for retrieving translated strings.

    Attributes:
        _instance (TranslationWrapper): The singleton instance of
        the TranslationWrapper class.
        translations (gettext.GNUTranslations): The translation
        object for managing translations.
    """

    _instance: Optional[Self] = None
    _locale: Optional[str] = None
    _locale_dir: Optional[str]
    _languages: list[tuple[str, str]] = []
    _default_language: str = "en"
    _translations_cache = {}

    def __new__(cls, locales_dir, languages, language, *args, **kwargs):
        """
        Create a new instance of the class if it doesn't
        exist, otherwise return the existing instance.

        Returns:
            TranslationWrapper: The instance of the class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.init_translation(locales_dir, languages, language)
        return cls._instance

    def init_translation(self, locales_dir, languages, language):
        """Initialize translations by preloading all languages."""
        self._locale_dir = locales_dir
        self._default_language = language
        self._languages = languages

        # Load all languages into cache
        for lang, _ in self._languages:
            try:
                self._translations_cache[lang] = gettext.translation(
                    "messages", localedir=self._locale_dir, languages=[lang], fallback=True
                )
            except FileNotFoundError:
                logging.warning(f"⚠️ Warning: No translations found for {lang}. Using fallback.")

    def _detect_locale(self, locale: Optional[str] = None, locales: Optional[str] = None) -> str:
        language = self._default_language
        if locale and len([loc for loc in self._languages if loc[0] == locale]) == 1:
            language = locale
        if locales:
            for locale in locales:
                if len([loc for loc in self._languages if loc[0] == locale]) == 1:
                    language = locale
                    break
        return language

    @classmethod
    def get_instance(cls) -> Self:
        if not cls._instance:
            raise AttributeError("TranslationWrapper has not been initialized")
        return cls._instance

    @classmethod
    def init(cls, locales_dir, languages, language):
        if not cls._instance:
            cls(locales_dir, languages, language)

    def gettext(self, message: str, locale: Optional[str] = None, lazy: bool = True) -> str or GetText:
        """
        Get the translated string for the specified message.

        - Automatically selects the correct translation based on the current locale.
        """
        current_locale = locale or get_locale() or self._default_language
        translation = self._translations_cache.get(current_locale, self._translations_cache.get(self._default_language))

        if lazy:
            g = GetText(message)
            g.set_locale(current_locale)
        return translation.gettext(message)

    def set_locale(self, locale: Optional[str] = None, locales: Optional[list[str]] = None, use_context: bool = False):
        """Set locale for current request."""
        locale = self._detect_locale(locale, locales)
        if use_context:
            set_locale(locale)
        else:
            self._default_language = locale

    def get_locales(self) -> list[tuple[str, str]]:
        """Return the list of supported locales."""
        return self._languages

    def get_locale(self) -> str:
        """Retrieve the locale from contextvars (or fallback to default)."""
        return get_locale() or self._default_language
