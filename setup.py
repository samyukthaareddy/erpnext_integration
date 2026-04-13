from setuptools import setup, find_packages

setup(
    name="erpnext-crm-integration",
    version="0.1.0",
    description="ERPNext CRM Integration Service - Task 3 of AI-Driven Sales & Marketing Automation System",
    author="Harshita & Samyukthaa",
    author_email="harshita@ideabytes.com",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "Flask>=3.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "jsonschema>=4.20.0",
        "pytest>=7.4.3",
        "pytest-cov>=4.1.0",
    ],
    extras_require={
        "dev": [
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
        ],
    },
)
