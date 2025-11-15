"""Setup configuration for MTP2 - Arithmetic Word Problem Toolkit."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = "Arithmetic Word Problem Toolkit - Generate synthetic math reasoning datasets"
try:
    if readme_file.exists():
        long_description = readme_file.read_text(encoding="utf-8")
except (UnicodeDecodeError, OSError):
    pass  # Use default description if README can't be read

setup(
    name="awp",
    version="2.0.0",
    description="Arithmetic Word Problem Toolkit - Generate synthetic math reasoning datasets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MTP2 Team",
    python_requires=">=3.10",
    packages=find_packages(exclude=["scripts", "output", "docs"]),
    install_requires=[
        "networkx>=3.0",
        "numpy>=1.24",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "awp-generate=scripts.generate_dataset:main",
            "awp-analyze=scripts.analyze_quality:main",
            "awp-test=scripts.run_tests:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="arithmetic word problems dataset generation machine-learning nlp reasoning",
)
