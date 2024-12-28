import os
from setuptools import setup, find_packages

base_dir = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(base_dir, "README.md")
long_description = ""

if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="loghive",
    version="1.0.0b1",
    packages=find_packages(),
    package_data={
        "loghive": [
            "alembic.ini",
            "alembic/*",
            "alembic/versions/*",
            "alembic/script.py.mako",
            "requirements.txt",
            "README.md"
        ]
    },
    install_requires=[
        "alembic>=1.8.1,<1.14.0",
        "SQLAlchemy==2.0.36",
        "annotated-types==0.7.0",
        "anyio==4.6.2.post1",
        "asyncpg==0.30.0",
        "black==24.10.0",
        "blinker==1.9.0",
        "certifi==2024.8.30",
        "click==8.1.7",
        "colorlog==6.9.0",
        "dnspython==2.7.0",
        "email_validator==2.2.0",
        "exceptiongroup==1.2.2",
        "fastapi==0.115.5",
        "fastapi-cli==0.0.5",
        "Flask==3.1.0",
        "greenlet==3.1.1",
        "h11==0.14.0",
        "httpcore==1.0.7",
        "httptools==0.6.4",
        "httpx==0.27.2",
        "idna==3.10",
        "itsdangerous==2.2.0",
        "Jinja2==3.1.4",
        "Mako==1.3.6",
        "markdown-it-py==3.0.0",
        "MarkupSafe==3.0.2",
        "mdurl==0.1.2",
        "mypy-extensions==1.0.0",
        "packaging==24.2",
        "pathspec==0.12.1",
        "pika==1.3.2",
        "platformdirs==4.3.6",
        "psycopg2==2.9.10",
        "pydantic==2.9.2",
        "pydantic-settings==2.6.1",
        "pydantic_core==2.23.4",
        "Pygments==2.18.0",
        "python-dotenv==1.0.1",
        "python-multipart==0.0.17",
        "PyYAML==6.0.2",
        "rich==13.9.4",
        "shellingham==1.5.4",
        "sniffio==1.3.1",
        "starlette==0.41.3",
        "tomli==2.1.0",
        "typer==0.13.1",
        "typing_extensions==4.12.2",
        "uvicorn==0.32.0",
        "uvloop==0.21.0",
        "watchfiles==0.24.0",
        "websockets==14.1",
        "Werkzeug==3.1.3",
    ],
    include_package_data=True,
    author="Pratham Agrawal",
    author_email="prathamagrawal1205@example.com",
    description="A powerful, extensible Python logging library that enables distributed log collection across multiple Python servers with support for multiple message brokers and asynchronous database operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
