from setuptools import setup, find_packages

setup(
    name="bureaucracy-copilot",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0",
        "anthropic>=0.28.0",
        "pyyaml>=6.0",
        "jsonschema>=4.19.0",
        "click>=8.1.7",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bureaucracy-copilot=src.main:main",
        ]
    },
)
