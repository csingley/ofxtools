"""
Release process:
    1. Update VERSION
"""
from setuptools import setup, find_packages
import os.path

__here__ = os.path.dirname(os.path.realpath(__file__))

about = {}
with open(os.path.join(__here__, 'ofxtools', '__version__.py'), 'r') as f:
    exec(f.read(), about)

with open(os.path.join(__here__, 'README.rst'), 'r') as f:
    readme = f.read()

url_base = "{}/tarball".format(about["__url__"])

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=readme,
    long_description_content_type="text/x-rst",
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    packages=find_packages(),
    package_data={'ofxtools': ['README.rst', 'config/*.cfg', 'tests/*']},
    python_requires=">=3.4",
    license=about["__license__"],

    # Note: change 'master' to the tag name when releasing a new verion
    #  download_url="{}/master".format(url_base),
    download_url="{}/{}".format(url_base, about["__version__"]),

    entry_points={'console_scripts': ['ofxget=ofxtools.Client:main']},

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords=['ofx', 'Open Financial Exchange'],
)
