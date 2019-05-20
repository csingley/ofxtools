"""
Release process:
    1. Update ofxtools.__version__.__version__
    2. Change download_url below
    3. Commit changes & push
    4. `git tag` the release
    5. Push tags
    6. Change download_url back to master; commit & push
"""
# stdlib imports
import os.path
from setuptools import setup, find_packages

__here__ = os.path.dirname(os.path.realpath(__file__))

ABOUT = {}
with open(os.path.join(__here__, 'ofxtools', '__version__.py'), 'r') as f:
    exec(f.read(), ABOUT)

with open(os.path.join(__here__, 'README.rst'), 'r') as f:
    README = f.read()

URL_BASE = "{}/tarball".format(ABOUT["__url__"])

setup(
    name=ABOUT["__title__"],
    version=ABOUT["__version__"],
    description=ABOUT["__description__"],
    long_description=README,
    long_description_content_type="text/x-rst",
    author=ABOUT["__author__"],
    author_email=ABOUT["__author_email__"],
    url=ABOUT["__url__"],
    packages=find_packages(),
    package_data={'ofxtools': ["README.rst", "config/*.cfg"]},
    python_requires=">=3.4",
    license=ABOUT["__license__"],

    # Note: change 'master' to the tag name when releasing a new verion
    #  download_url="{}/master".format(URL_BASE),
    download_url="{}/{}".format(URL_BASE, ABOUT["__version__"]),

    entry_points={'console_scripts': ['ofxget=ofxtools.scripts.ofxget:main']},

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Topic :: Office/Business",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords=['ofx', 'Open Financial Exchange'],
)
