from setuptools import setup, find_packages

setup(
    name="hopper_backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "yfinance",
        "httpx",
        "pytest",
        "pytest-asyncio",
        "tenacity",
        "pydantic"
    ],
) 