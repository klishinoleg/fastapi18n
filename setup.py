from setuptools import setup, find_packages

setup(
    name="fastapi18n",
    version="0.1.3",
    author="Klishin Oleg",
    author_email="klishinoleg@gmail.com",
    description="Multilingual support middleware for FastAPI using gettext with support Tortoise ORM models",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/klishinoleg/fastapi18n",
    packages=find_packages(),
    install_requires=[
        "google-cloud-translate",
        "typing_extensions",
        "starlette",
        "python-dotenv",
        "Babel",
        "contextvars",
        "tortoise-orm==0.24.2",
        "aerich",
        "fastapi",
        "fastapi-admin",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "Framework :: Tortoise-ORM",
        "Framework :: gettext",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "fastapi18n=fastapi18n.utils.commands:main",
        ],
    }
)
