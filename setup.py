import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "ofx",
    version = "0.1",
    packages = find_packages(),

    install_requires = ['sqlalchemy >= 0.6',
                        'elixir >= 0.7',
    ],

    # Metadata for PyPI
    author = "Christopher Singley",
    author_email = "csingley@gmail.com",
    description = "Open Financial Exchange (OFX) library module",
    license = "GPL",
    keywords = "ofx",
)