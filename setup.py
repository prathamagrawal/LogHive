from setuptools import setup, find_packages

setup(
    name="loghive",
    version="v1.0",
    packages=find_packages(),
    install_requires=[
        "alembic==1.14.0",
        "annotated-types==0.7.0",
        "anyio==4.6.2.post1",
        "asyncpg==0.30.0",
        "black==24.10.0",
        "colorlog==6.9.0",
        "pika==1.3.2",
        "psycopg2==2.9.10",
        "pydantic==2.9.2",
        "pydantic-settings==2.6.1",
        "pydantic_core==2.23.4",
        "SQLAlchemy==2.0.36",
        "typer==0.13.1",
        "typing_extensions==4.12.2",
        "greenlet==3.1.1"
    ],
    author="Pratham Agrawal",
    author_email="prathamagrawal1205@example.com",
    description="Short description",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
