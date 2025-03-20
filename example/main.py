import uvicorn
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from tortoise import fields
from tortoise.models import Model
from fastapi18n.middlewares.middleware import LocalizationMiddleware
from fastapi18n.wrappers.wrapper import TranslationWrapper
from fastapi18n.decorators.multilangual import multilangual_model
from tortoise.contrib.pydantic import pydantic_model_creator
from pathlib import Path
import os

# Initialize FastAPI
app = FastAPI()

# Enable multilingual support using FastAPI18n
app.add_middleware(LocalizationMiddleware)

TranslationWrapper.init(
    locales_dir=os.path.join(Path.cwd().parent, "locales"),  # Directory for translation files
    languages=[("en", "English"), ("fr", "French")],  # Supported languages
    language="en"  # Default language
)

_ = TranslationWrapper.get_instance().gettext

# Configure SQLite database with Tortoise ORM
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["main"]},  # Load models from this module
    generate_schemas=True,  # Automatically create tables if they don't exist
    add_exception_handlers=True,
)


# Define a multilingual model using FastAPI18n decorator
@multilangual_model({"name", "description"})
class Product(Model):
    """Product model with multilingual fields for 'name' and 'description'."""
    name = fields.CharField(max_length=255, required=True, null=False)
    description = fields.TextField()

    id = fields.IntField(pk=True, generated=True)


# Define Pydantic schema for API requests and responses
ProductSchema = pydantic_model_creator(
    Product,
    name="ProductSchema",
    include=("id", "name", "description"),
    optional=("id",)
)

ProductListSchema = pydantic_model_creator(
    Product,
    name="ProductListSchema",
    include=("id", "name")
)


# Create a new product (POST request)
@app.post("/products/", response_model=ProductSchema)
async def create_product(product: ProductSchema):
    """Creates a new product and stores it in the database."""
    new_product = await Product.create(name=product.name, description=product.description)
    return await ProductSchema.from_tortoise_orm(new_product)


# Get all products (GET request)
@app.get("/products/", response_model=List[ProductListSchema])
async def list_products():
    """Fetches all products from the database."""
    return await ProductListSchema.from_queryset(Product.all())


# Retrieve a product by ID (GET request)
@app.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int):
    """Fetches a product from the database by its ID."""
    product = await Product.get_or_none(id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await ProductSchema.from_tortoise_orm(product)


# Update an existing product (PUT request)
@app.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductSchema):
    """Updates an existing product's name and description."""
    db_product = await Product.get_or_none(id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    data = dict(product)
    await db_product.update_from_dict({k: data.get(k) for k in product.model_fields_set})
    await db_product.save()
    return await ProductSchema.from_tortoise_orm(db_product)


@app.get("/products/description/")
async def products_description():
    return {
        "name": _("Products"),
        "desctiption": _("Products description")
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
