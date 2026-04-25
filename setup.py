from setuptools import find_packages, setup


setup(
    name="transportes-la-serena-cotizador",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["fastapi>=0.115,<1", "httpx>=0.27,<1", "uvicorn[standard]>=0.30,<1"],
    entry_points={
        "console_scripts": [
            "cotizador=cotizador.presentation.cli:main",
        ]
    },
)
