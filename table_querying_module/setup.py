"""
Setup script for the Table Querying Module.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="table-querying-module",
    version="1.0.0",
    description="A modular system for extracting, processing, and querying HTML tables with LLM-generated descriptions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Table Querying Module Team",
    author_email="contact@example.com",
    url="https://github.com/your-org/table-querying-module",
    
    # Package discovery
    packages=find_packages(where=".", include=["src*"]),
    package_dir={"": "."},
    
    # Include non-Python files
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
        "src": ["*.json", "*.yaml", "*.yml"],
        "examples": ["*.py", "*.json", "*.html"],
        "configs": ["*.json", "*.yaml", "*.yml"],
        "docs": ["*.md", "*.rst"],
    },
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "production": [
            "gunicorn>=20.1.0",
            "uvicorn>=0.18.0",
            "fastapi>=0.95.0",
            "prometheus-client>=0.16.0",
            "psutil>=5.9.0",
        ],
        "postgresql": [
            "psycopg2-binary>=2.9.0",
        ],
        "mongodb": [
            "pymongo>=4.0.0",
        ],
        "redis": [
            "redis>=4.3.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
            "gunicorn>=20.1.0",
            "uvicorn>=0.18.0",
            "fastapi>=0.95.0",
            "prometheus-client>=0.16.0",
            "psutil>=5.9.0",
            "psycopg2-binary>=2.9.0",
            "pymongo>=4.0.0",
            "redis>=4.3.0",
        ]
    },
    
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "table-querying=src.cli.main:main",
            "table-query=src.cli.main:main",
            "tq-process=src.cli.process:main",
            "tq-chat=src.cli.chat:main",
            "tq-deploy=src.production.deployment:main",
            "tq-validate=src.production.deployment:validate_main",
        ],
        "table_querying.plugins": [
            # Plugin entry points will be discovered here
        ],
    },
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    
    # Keywords for discovery
    keywords=[
        "table", "html", "extraction", "processing", "llm", "nlp", 
        "database", "query", "chat", "ai", "machine-learning",
        "data-extraction", "web-scraping", "document-processing"
    ],
    
    # Project URLs
    project_urls={
        "Documentation": "https://github.com/your-org/table-querying-module/docs",
        "Source": "https://github.com/your-org/table-querying-module",
        "Bug Tracker": "https://github.com/your-org/table-querying-module/issues",
        "Changelog": "https://github.com/your-org/table-querying-module/blob/main/CHANGELOG.md",
        "Examples": "https://github.com/your-org/table-querying-module/tree/main/examples",
    },
    
    # License
    license="MIT",
    
    # Zip safety
    zip_safe=False,
)