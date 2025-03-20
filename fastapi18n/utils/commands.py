import os
import argparse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .manage_translations import ManageTranslations

load_dotenv()

# Default values (from environment variables if available)
LOCALES_DIR = os.getenv("LOCALES_DIR")  # Use current working dir if not set
LANGUAGES = os.getenv("LANGUAGES")
SOURCE_TRANSLATE_LANGUAGE = os.getenv("SOURCE_TRANSLATE_LANGUAGE")


class Commands:
    """
    Command-line utility for managing translations in FastAPI18n.
    Supports message extraction, compilation, and automated translation.
    """

    locales_dir: Optional[str or Path] = LOCALES_DIR
    languages: Optional[str] = LANGUAGES

    @classmethod
    def get_languages(cls):
        if not cls.languages:
            cls.languages = input("Please specify languages: en|fr (example)")
        print(cls.languages)
        return [(l, l) for l in cls.languages.split("|")]

    @classmethod
    def get_locales_dir(cls):
        if not cls.locales_dir:
            locales_dir = input("Please specify locales dir: locales")
            cls.locales_dir = str(Path.cwd() / ("locales" if not locales_dir else Path(locales_dir)))
        print(cls.locales_dir)
        return cls.locales_dir

    @classmethod
    def makemessages(cls):
        """Extracts translatable strings and creates translation files."""
        ManageTranslations(cls.get_locales_dir(), cls.get_languages()).make()

    @classmethod
    def compilemessages(cls):
        """Compiles translations into .mo files."""
        ManageTranslations(cls.get_locales_dir(), cls.get_languages()).compile()

    @classmethod
    def translate(cls, only=None, exclude=None, source_lang=None):
        """
        Translates missing text using Google Cloud Translate.

        :param only: List of languages to translate.
        :param exclude: List of languages to exclude.
        :param source_lang: Source language of messages
        """
        print(f"Starting translation... Only: {only}, Exclude: {exclude}")
        ManageTranslations(
            cls.get_locales_dir(), cls.get_languages(), source_lang=source_lang
        ).translate_files(only=only, exclude=exclude)


def main():
    """
    Entry point for command-line execution.
    Parses arguments and executes corresponding commands.
    """
    parser = argparse.ArgumentParser(description="FastAPI18n translation management utility")

    # Define command-line arguments
    parser.add_argument("-d", "--dir", default=LOCALES_DIR, help="Set work directory for translations")
    parser.add_argument("-l", "--languages", default=LANGUAGES, help="Set languages (separated by |)")
    parser.add_argument("-o", "--only", help="Translate only these languages (comma-separated, e.g., 'en,fr')")
    parser.add_argument("-e", "--exclude", help="Exclude these languages from translation (comma-separated)")
    parser.add_argument("-s", "--source_lang", default=SOURCE_TRANSLATE_LANGUAGE,
                        help="Set default code messages language")
    parser.add_argument("command", choices=["makemessages", "compilemessages", "translate"], help="Command to execute")

    # Parse arguments
    args = parser.parse_args()

    Commands.languages = args.languages
    Commands.locales_dir = args.dir

    # Execute selected command
    if args.command == "makemessages":
        Commands.makemessages()
    elif args.command == "compilemessages":
        Commands.compilemessages()
    elif args.command == "translate":
        only_list = args.only.split(",") if args.only else None
        exclude_list = args.exclude.split(",") if args.exclude else None
        source_lang = args.source_lang if args.source_lang else None
        Commands.translate(only=only_list, exclude=exclude_list, source_lang=source_lang)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
