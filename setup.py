from setuptools import setup, find_packages

NAME = "synonymizer"
URL = "https://github.com/monarch-initiative/synonymizer"
AUTHOR = "Harshad Hegde"
EMAIL = "hhegde@lbl.gov"
REQUIRES_PYTHON = ">=3.7.0"
VERSION = "0.0.1"
LICENSE = "BSD"

EXTRAS = {}

setup(
    name=NAME,
    author=AUTHOR,
    version=VERSION,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license=LICENSE,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    extras_require=EXTRAS,
    include_package_data=True,
    # add package dependencies
    install_requires=["click", "pandas", "pytest", "pyyaml"],
)
