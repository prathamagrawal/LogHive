from setuptools import setup, find_packages
import os

def get_reqs():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    req_path = os.path.join(base_dir, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r") as f:
                return [x.strip() for x in f.read().splitlines() if x.strip() and not x.startswith('#')]
        except Exception as e:
            print(f"Error reading requirements.txt: {e}")
            return []
    print(f"Requirements file not found at: {req_path}")
    return []

base_dir = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(base_dir, "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="loghive",
    version="1.0.0b2",
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
    data_files=[
        ('', ['requirements.txt']),  # Include requirements.txt in the root
    ],
    install_requires=get_reqs(),
    include_package_data=True,
    author="Pratham Agrawal",
    author_email="prathamagrawal1205@example.com",
    description="A powerful, extensible Python logging library that enables distributed log collection across multiple Python servers with support for multiple message brokers and asynchronous database operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
)