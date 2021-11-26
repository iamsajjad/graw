
import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="graw",
    version="0.0.0",
    description="Dowload files and subdirectories from github.com and gitlab.com",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/iamsajjad/graw",
    author="Sajjad alDalwachee",
    author_email="sajjad.alDalwachee@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["graw"],
    include_package_data=True,
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "graw=graw.graw:run",
        ]
    },
)

