from setuptools import setup, find_packages
import os.path

# Get the long description from the relevant file
__here__ = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(__here__, 'README.rst'), 'r') as f:
    long_description = f.read()

setup(
    name='ofxtools',
    version='0.7.0',
    # Note: change 'master' to the tag name when release a new verion
    download_url='https://github.com/csingley/ofxtools/tarball/master',
    #  download_url='https://github.com/csingley/ofxtools/tarball/0.7.0',

    description=('Library for working with Open Financial Exchange (OFX) '
                 'formatted data used by financial institutions'),
    long_description=long_description,
    long_description_content_type="text/x-rst",

    url='https://github.com/csingley/ofxtools',

    author='Christopher Singley',
    author_email='csingley@gmail.com',

    license='MIT',

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

    packages=find_packages(),

    package_data={
        'ofxtools': ['README.rst', 'config/*.cfg', 'tests/*'],
    },

    entry_points={
        'console_scripts': [
            'ofxget=ofxtools.Client:main',
        ],
    },
)
