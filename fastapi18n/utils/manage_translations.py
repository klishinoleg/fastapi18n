import os
import re
import shutil
from typing import Optional
import subprocess
from google.cloud import translate_v2 as tr


class ManageTranslations:
    _locales_dir: str
    _languages: list[tuple[str, str]]
    _source_lang: str = "en"

    def __init__(self, locales_dir: str, languages: list[tuple[str, str]], source_lang: str = "en"):
        self._locales_dir = locales_dir
        self._languages = languages
        self._source_lang = source_lang

        # ✅ Check if the locale directory exists, create it if necessary
        print(f"📁 Checking if locales directory exists: {self._locales_dir}")
        os.makedirs(self._locales_dir, exist_ok=True)

    @staticmethod
    def _get_exclude(excludes: Optional[list[str]] = None) -> list:
        """
        Prepare a list of arguments to exclude specific paths from translation processing.
        """
        omit_args = []
        if excludes:
            for path in excludes:
                omit_args.append("--omit")
                omit_args.append(path + "/*")
        return omit_args

    def _get_base_file_path(self) -> str:
        """
        Get the base `.pot` file path for translations.
        """
        path = os.path.join(self._locales_dir, "messages.pot")
        print(f"📂 Base translation file path: {path}")  # 🛠️ Debugging output
        return path

    def _make_basefile(self, excludes: list):
        """
        Extract translatable strings from the project and generate the base `.pot` file.
        """

        print("🔍 Extracting translatable strings...")

        # ✅ Ensure the base directory exists before running `pybabel`
        base_file_path = self._get_base_file_path()
        base_dir = os.path.dirname(base_file_path)
        print(f"📂 Ensuring base directory exists: {base_dir}")
        os.makedirs(base_dir, exist_ok=True)

        # ✅ Run `pybabel extract`
        extract_command = [
                              "pybabel", "extract", "-o", base_file_path, "."
                          ] + self._get_exclude(excludes)

        print(f"🛠️ Running command: {' '.join(extract_command)}")  # 🛠️ Debugging output
        subprocess.run(extract_command, check=True)

    def _make_languages_files(self):
        """
        Initialize translation files (`messages.po`) for each language if they do not exist.
        """
        for lang, label in self._languages:
            lang_dir = os.path.join(self._locales_dir, lang, "LC_MESSAGES")
            po_file = os.path.join(lang_dir, "messages.po")

            # ✅ Ensure the directory exists for each language
            print(f"📂 Ensuring language directory exists: {lang_dir}")
            os.makedirs(lang_dir, exist_ok=True)

            if not os.path.exists(po_file):
                print(f"🌍 Initializing translations for {lang}...")
                init_command = [
                    "pybabel", "init", "-i", self._get_base_file_path(),
                    "-d", self._locales_dir, "-l", lang
                ]
                print(f"🛠️ Running command: {' '.join(init_command)}")  # 🛠️ Debugging output
                subprocess.run(init_command, check=True)

    def make(self, excludes: Optional[list[str]] = None):
        """
        Generate base translation files and initialize per-language `.po` files.
        """
        try:
            self._make_basefile(excludes)
            self._make_languages_files()
            print("✅ Done!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running pybabel: {e}")

    def compile(self):
        """
        Compile all translation files (`.mo`) from `.po` files.
        """
        print("📦 Compiling translations...")
        compile_command = ["pybabel", "compile", "-d", self._locales_dir]
        print(f"🛠️ Running command: {' '.join(compile_command)}")  # 🛠️ Debugging output
        subprocess.run(compile_command, check=True)
        print("✅ Done!")

    @staticmethod
    def add_line_to_file(new_file, line):
        """
        Append a line to a file.
        """
        with open(new_file, 'a', encoding='utf-8') as f:
            f.writelines([line])

    def translate_files(self, exclude: Optional[list[str]] = None, only: Optional[list[str]] = None):
        """
        Automatically translate missing `msgstr` values in `.po` files using Google Cloud Translate API.
        """
        for language, _ in self._languages:
            if language == self._source_lang:
                continue
            if exclude and language in exclude:
                continue
            if only and language not in only:
                continue
            print(language + " >>> Start translation...")

            lang_dir = os.path.join(self._locales_dir, language, 'LC_MESSAGES')
            current_file = os.path.join(lang_dir, 'messages.po')
            backup_file = os.path.join(lang_dir, 'messages.po.bak')

            # Create a backup before modifying the file
            shutil.copyfile(current_file, backup_file)
            os.remove(current_file)

            source_text_lines = None
            collect_sources = False

            with open(backup_file, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    if line == '\n' or line[0] == '#':
                        pass
                    elif 'msgid' in line:
                        source_text_lines = []
                        collect_sources = True
                        if '""' not in line:
                            source_text_lines.append(re.findall(r"\"(.*?)\"", line)[0])
                    elif 'msgstr' in line:
                        if '""' in line and len(source_text_lines) > 0:
                            # Translate missing text using Google Cloud Translate API
                            result = tr.Client().translate(
                                values=" ".join(source_text_lines),
                                target_language=language,
                                source_language=self._source_lang
                            )
                            line = line.replace('""', f'"{result.get("translatedText")}"')
                            source_text_lines = None
                            collect_sources = False
                            print(result)
                    elif collect_sources:
                        source_text_lines.append(re.findall("\"(.*?)\"", line)[0])

                    self.add_line_to_file(current_file, line)
