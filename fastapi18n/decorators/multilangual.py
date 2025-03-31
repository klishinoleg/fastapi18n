import types
from typing import Callable, Set
from ..wrappers import TranslationWrapper
from copy import deepcopy
from tortoise.fields import CharField, TextField


def multilangual_model(multilangual_fields: Set[str]) -> Callable:
    """
    A decorator that dynamically adds multilingual fields to a Tortoise ORM model.

    This decorator automatically generates database fields for multiple languages based on
    a predefined configuration. It modifies the model by adding field variants for each language
    defined in `LANGUAGES` and ensures that these fields are registered in Tortoise ORM's `_meta.fields_map`,
    so they work properly with migrations (`aerich`).

    :param multilangual_fields: A set of multilangual fields

    **Example Usage:**
    ```python
    @multilangual_model({"name", "text"})
    class Article(models.Model):
        name = fields.CharField(max_length=100)
        text = fields.TextField()
    ```

    **Result:**
    - The decorator dynamically creates the following fields:
        ```python
        name_en = fields.CharField(max_length=100)
        name_ru = fields.CharField(max_length=100)
        text_en = fields.TextField()
        text_ru = fields.TextField()
        ```
    - and change original fields to has_db_field=False

    **Error Handling:**
    - Raises an `AttributeError` if the decorated class is not a valid Tortoise ORM model.
    - Raises a `TypeError` if the provided field type is not a subclass of `fields.Field`.

    :return: The modified class with dynamically added multilingual fields.
    """

    locales = tuple(TranslationWrapper.get_instance().get_locales())  # Get available locales
    get_locale = TranslationWrapper.get_instance().get_locale  # Function to retrieve the current locale

    def get_set_property(attr):
        """
        Creates a setter method for the dynamic multilingual field.

        - The setter automatically determines the correct language field
          based on the currently active locale and updates its value.
        """

        def set_property(self, value):
            if value is not None:
                lang_field = f"{attr}_{get_locale()}"  # Format field name based on active locale
                setattr(self, lang_field, value)  # Set the value in the correct localized field

        return set_property

    def get_get_property(attr):
        """
        Creates a getter method for the dynamic multilingual field.

        - The getter automatically determines the correct language field
          based on the currently active locale and retrieves its value.
        """

        def get_property(self):
            lang_field = f"{attr}_{get_locale()}"  # Format field name based on active locale
            first_lang_field = f"{attr}_{locales[0][0]}"
            # Get locale value or first locale value in locales list
            return getattr(self, lang_field) or getattr(self, first_lang_field)

        return get_property

    def kwargs_wrapper(original_method: Callable) -> Callable:
        def change_fields(data: dict) -> dict:
            locale = get_locale()
            lang_fields = multilangual_fields
            return {f"{key}_{locale}" if key in lang_fields else key: val for key, val in data.items()}

        def set_kwargs(self, kwargs):
            """ Custom __init__ method to modify multilingual field names dynamically. """
            kwargs = change_fields(kwargs)
            return original_method(self, kwargs)

        return set_kwargs

    def modify_field_object_to_not_db(field_object):
        class NoDbClass(field_object.__class__):
            has_db_field = False

        field_object.__class__ = NoDbClass
        field_object.null = True

    def get_field_object_with_new_source_field(field_object, source_field, is_first_lang):
        new_fiels_object = field_object.__class__(**field_object.constraints)
        new_fiels_object.source_field = source_field
        new_fiels_object.null = new_fiels_object.null or not is_first_lang
        return new_fiels_object

    def wrapper(cls):
        """
        Modifies the given Tortoise ORM model by dynamically adding multilingual fields.

        - Iterates through each base field and generates a language-specific variant for each available locale.
        - Creates getter and setter properties for dynamically accessing localized fields.
        - Registers the generated fields in `_meta.fields_map` to be recognized by Tortoise ORM.

        :raises AttributeError: If the class is not a Tortoise ORM model.
        """
        if not hasattr(cls, "_meta"):
            raise AttributeError(f"Class {cls.__name__} must be an instance of Tortoise ORM!")

        for field_name in multilangual_fields:
            is_first_lang = True
            # Get original field for replace
            field_object = cls._meta.fields_map.get(field_name)

            # Ensure that the model contains the specified multilingual field
            if not field_object:
                raise AttributeError(f"The model {cls} must contain a multilingual field '{field_name}'")

            # Validate that the multilingual field is either CharField or TextField
            if type(field_object) not in (CharField, TextField):
                raise AttributeError(
                    f"The multilingual field '{field_name}' in the model {cls} must be a CharField or TextField")

            # Create field for each language
            for lang, lang_label in locales:
                lang_field_name = f"{field_name}_{lang}"  # Generate field name (e.g., "name_en", "name_ru")
                field_instance = get_field_object_with_new_source_field(field_object, lang_field_name, is_first_lang)
                # only first language can be not null
                is_first_lang = False

                # Dynamically add the new field to the model class
                setattr(cls, lang_field_name, field_instance)

                # Register the new field in Tortoise ORM metadata
                cls._meta.add_field(lang_field_name, field_instance)
            modify_field_object_to_not_db(field_object)
            # Delete source field from db field list
            del cls._meta.fields_db_projection[field_name]
            # Create getter and setter properties for the base field name
            setattr(cls, field_name, property(get_get_property(field_name), get_set_property(field_name)))

        setattr(cls, "_set_kwargs", kwargs_wrapper(copy_method(cls, "_set_kwargs")))

        return cls  # Return the modified class

    return wrapper


def copy_method(cls, method_name):
    """
    Creates a copy of a class method by its name.

    :param cls: The class containing the method
    :param method_name: The name of the method to copy
    :return: A new method (copied)
    """
    if not hasattr(cls, method_name):
        raise AttributeError(f"Method '{method_name}' not found in class {cls.__name__}")

    method = getattr(cls, method_name)
    if not callable(method):
        raise TypeError(f"'{method_name}' is not a callable method in class {cls.__name__}")

    # Create a new function based on the method
    new_method = types.FunctionType(
        method.__code__,  # Original method code
        method.__globals__,  # Use original global variables
        name=method.__name__,  # Retain original method name
        argdefs=method.__defaults__,  # Set default arguments
        closure=method.__closure__  # Pass closures if any
    )

    return new_method
