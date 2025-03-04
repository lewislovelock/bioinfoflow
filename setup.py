"""
Setup script for BioinfoFlow package.
"""
from setuptools import setup, find_packages

# Get version and description from package
about = {}
with open("src/bioinfoflow/__init__.py") as f:
    exec(f.read(), about)

# Read the requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="bioinfoflow",
    version=about["__version__"],
    description=about["__description__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url="https://github.com/lewislovelock/bioinfoflow",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bioinfoflow=bioinfoflow.cli.main:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
) 