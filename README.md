# FastAPI18n

## Features:

✅ Middleware for handling multilingual requests in FastAPI  
✅ Supports **gettext** for internationalization  
✅ Multilingual fields for **Tortoise ORM** models  
✅ **Aerich** integration for database migrations  
✅ Auto-translate missing text using **Google Translate API**  
✅ Fully compatible with **FastAPI Admin**  
✅ **Context-aware localization**: Stores locale using `contextvars`, ensuring per-session isolation

## Installation

```sh
pip install fastapi18n
```

## Usage Example

```python
from fastapi import FastAPI
from fastapi18n.middlewares import LocalizationMiddleware
from fastapi18n.wrappers import TranslationWrapper

app = FastAPI()
app.add_middleware(LocalizationMiddleware)
_ = TranslationWrapper.get_instance().gettext

TranslationWrapper.init(
    locales_dir="locales",
    languages=[("en", "English"), ("fr", "French")],
    language="en"
)


@app.get("/")
async def read_root():
    return {"message": _("Hello, world!")}
```

## Multilingual ORM Fields with Tortoise ORM

### Database Integration

When using Tortoise ORM, multilingual fields will be automatically created for each language during database migrations.

```python
from tortoise import fields
from fastapi18n.decorators import multilangual_model
from tortoise.models import Model


@multilangual_model({"name", "description"})
class Product(Model):
    # for IDE
    name = fields.CharField(max_length=100)
    description = fields.TextField()

    id = fields.IntField(pk=True)
```

## What happens during migration?

When running migrations (aerich migrate), the following fields will be automatically generated:

```python
from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "job" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name_en" VARCHAR(100) NOT NULL,
    "name_ru" VARCHAR(100) NOT NULL,
    "description_en" TEXT NOT NULL,
    "description_ru" TEXT NOT NULL,
);"""
```

## Fields access

FastAPI18n allows you to dynamically access **multilingual fields** based on the currently active locale.

### **Example Usage**

```python
# Access based on the current locale:
from fastapi18n.wrappers import TranslationWrapper

product = Product()
activate = TranslationWrapper.get_instance().set_locale
# Set English as the active language and assign a value
activate("en")
product.name = "Example Name"

# Switch to French and assign a value in French
activate("fr")
product.name = "Nom d'exemple"

# Switch back to English and retrieve the stored value
activate("en")
print(product.name)  # Returns 'Example Name' in the selected language
```

## Passing Language in API Requests

FastAPI18n provides multiple ways to define the user 's language when making API requests.

### **1️⃣ Using Query Parameters**

You can pass the language directly in the URL using the `lang` parameter.

#### **Example**

```
GET /api/resource?lang=fr
```

This tells the middleware to use French (fr) for this request.

### **2️⃣ Using Accept-Language Header**

You can also define the language via the Accept-Language header.

```
curl -H "Accept-Language: fr" http://localhost:8000/api/resource
```

### 3️⃣**Active Language in Code**

In code you can activate language with

```python
from fastapi18n.wrappers import TranslationWrapper

activate = TranslationWrapper.get_instance().set_locale

activate("en")
```

## 🎛 Command-Line Interface (CLI)

FastAPI18n provides a CLI for managing translations. You can run the following commands in your terminal:

### **Available Commands**

| Command                      | Description                                                  |
|------------------------------|--------------------------------------------------------------|
| `fastapi18n makemessages`    | Extracts translatable strings and creates `.po` files        |
| `fastapi18n compilemessages` | Compiles `.mo` files for runtime usage                       |
| `fastapi18n translate`       | Automatically translates missing text using Google Translate |

### **Command Arguments**

| Argument            | Description                                                                     |
|---------------------|---------------------------------------------------------------------------------|
| `-d, --dir`         | Specifies the locale directory (default: `locales/`)                            |
| `-l, --languages`   | Defines languages as a `                                                        |`-separated list (e.g., `"en|fr|de"`) |
| `-o, --only`        | Translates only selected languages (comma-separated, e.g., `"en,fr"`)           |
| `-e, --exclude`     | Excludes specific languages from translation (comma-separated, e.g., `"de,it"`) |
| `-s, --source_lang` | Default messages language in code ("en")                                        |

### Using `.env` for Default Settings**

You can **store default values** for `makemessages` and `compilemessages` in a `.env` file:

#### **Example `.env` file**

```sh
LOCALES_DIR=locales
LANGUAGES=en|fr
SOURCE_TRANSLATE_LANGUAGE=en # default "en"
```

---

### **Examples**

#### Extract translatable messages and create `.po` files

```sh
fastapi18n makemessages -d locales -l en|fr|es
```

This extracts all translatable strings and generates .po files for English, French, and Spanish.

#### Auto-translate missing text using Google Translate

```sh
fastapi18n translate -o fr,de
```

This translates missing strings only for French and German.

#### Exclude a language from auto-translation

```
fastapi18n translate -e en
```

This translates all missing strings except for English.

## 🌍 Setting up Google Cloud Translate

FastAPI18n supports **automatic translation of missing texts** using **Google Cloud Translate API**.

### **Step 1: Create a Google Cloud Project**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on **Select a project** → **New Project**.
3. Give your project a name and click **Create**.

---

### **Step 2: Enable Cloud Translation API**

1. Open the [Cloud Translation API page](https://console.cloud.google.com/apis/library/translate.googleapis.com).
2. Click **Enable**.

---

### **Step 3: Generate API Key**

1. Go to [Google Cloud Credentials](https://console.cloud.google.com/apis/credentials).
2. Click **Create Credentials** → **API Key**.
3. Copy the generated **API Key**.

---

### **Step 4: Set Up Environment Variables**

FastAPI18n requires the Google API key to be stored in an environment variable.

#### **Method 1: Set in `.env` file**

```sh
GOOGLE_APPLICATION_CREDENTIALS=your-google-api-key
```

#### **Method 2: Export in Terminal (for Linux/macOS)**

```
export GOOGLE_APPLICATION_CREDENTIALS="your-google-api-key"
```