from setuptools import setup, find_packages


def get_reqs():
    """
    The get_external_reqs function reads the requirements.txt file and returns a list of strings,
    where each string is an external requirement for this project.

    :return: A list of dependencies
    """
    with open("requirements.txt", "r") as f:
        return [x for x in f.read().split("\n") if x]


setup(
    name="loghive",
    version="1.0.0",
    packages=find_packages(),
    package_data={
        "loghive": [
            "alembic.ini",
            "alembic/*",
            "alembic/versions/*",
            "alembic/script.py.mako",
        ]
    },
    install_requires=get_reqs(),
    include_package_data=True,
    classifiers=[
        "License :: Proprietary",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    author="Pratham Agrawal",
    author_email="prathamagrawal1205@example.com",
    description="A powerful, extensible Python logging library that enables distributed log collection across multiple Python servers with support for multiple message brokers and asynchronous database operations.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
