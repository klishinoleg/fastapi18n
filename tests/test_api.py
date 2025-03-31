import os
from pathlib import Path
from typing import List
import pytest
from fastapi import HTTPException, FastAPI
from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from .models import Product, _, LocalizationMiddleware
from fastapi.testclient import TestClient

app = FastAPI()
app.add_middleware(LocalizationMiddleware)
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


@pytest.fixture(scope="module", autouse=True)
async def initialize_db(asyncio_mode="auto"):
    """Initialize Tortoise ORM for async tests."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["tests.models"]}
    )
    await Tortoise.generate_schemas()

    yield
    await Tortoise.close_connections()


client = TestClient(app)


@pytest.mark.asyncio
async def test_products():
    en_data = {"name": "En Name", "description": "En Description"}
    fr_data = {"name": "Fr Name", "description": "Fr Description"}

    res = client.post("/products", json=en_data, headers={"Accept-Language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == en_data.get("name")
    assert data["description"] == en_data.get("description")
    product_id = data.get("id")
    res_fr_update = client.put(f"/products/{product_id}", json=fr_data, headers={"Accept-Language": "fr"})
    assert res_fr_update.status_code == 200
    data = res_fr_update.json()
    assert data["name"] == fr_data.get("name")
    assert data["description"] == fr_data.get("description")
    res = client.get(f"/products/{product_id}", headers={"Accept-Language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == en_data.get("name")
    assert data["description"] == en_data.get("description")
    product = await Product.get(pk=product_id)
    assert product.name_en == en_data.get("name")
    assert product.description_en == en_data.get("description")
    assert product.name_fr == fr_data.get("name")
    assert product.description_fr == fr_data.get("description")
