"""
Setup script for Local AI Agent
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="local-ai-agent",
    version="1.0.0",
    author="Local AI Agent Team",
    author_email="team@localaiagent.com",
    description="A local-first AI agent that autonomously drives web browsers to perform tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/local-ai-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "gpt4all": [
            "gpt4all>=2.0.2",
        ],
        "ollama": [
            "ollama>=0.1.7",
        ],
        "llama": [
            "transformers>=4.35.2",
            "torch>=2.1.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "local-ai-agent=cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/local-ai-agent/issues",
        "Source": "https://github.com/yourusername/local-ai-agent",
        "Documentation": "https://github.com/yourusername/local-ai-agent#readme",
    },
)
