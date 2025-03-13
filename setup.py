from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rufus",
    version="0.1.0",
    author="Ambuj Hakhu",
    author_email="ambuj.hakhu@gmail.com",
    description="Intelligent Web Data Extraction for LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ambuj991/rufus",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.3",
        "openai>=0.27.0",
        "tqdm>=4.62.0",
    ],
    extras_require={
        "dynamic": [
            "playwright>=1.12.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "flake8>=3.9.2",
        ],
        "rag": [
            "langchain>=0.0.200",
            "llama-index>=0.5.0",
        ],
    },
)