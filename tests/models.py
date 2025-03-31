import os
from pathlib import Path

from tortoise import Model, fields

from fastapi18n import multilangual_model, TranslationWrapper, LocalizationMiddleware

TranslationWrapper.init(
    locales_dir=os.path.join(Path.cwd().parent, "locales"),  # Directory for translation files
    languages=[("en", "English"), ("fr", "French")],  # Supported languages
    language="en"  # Default language
)

_ = TranslationWrapper.get_instance().gettext


@multilangual_model({"name", "description"})
class Product(Model):
    """Product model with multilingual fields for 'name' and 'description'."""
    name = fields.CharField(max_length=255, required=True, null=False)
    description = fields.TextField()

    id = fields.IntField(primary_key=True, generated=True)
