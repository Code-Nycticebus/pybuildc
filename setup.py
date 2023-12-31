from setuptools import setup, find_packages

setup(
    name="pybuildc",
    description="A Build system for the C language",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Loris Kriyonas",
    author_email="loris.kriyonas@gmail.com",
    keywords=["c"],
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        'importlib-metadata; python_version<"3.11"',
    ],
    entry_points={
        "console_scripts": [
            "pybuildc = pybuildc.main:main",
        ]
    },
    setup_requires=[
        "setuptools>=42",
        "setuptools_scm>=3.5",
    ],
    use_scm_version={"write_to": "pybuildc/__version__.py"},
)
