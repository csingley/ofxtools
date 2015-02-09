from setuptools import setup, find_packages
from codecs import open # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))
usercfgdir = path.join(path.expanduser('~'), '.config', 'ofxtools')

# Get the long description from the relevant file
with open(path.join(here, 'README'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ofxtools',
    version='0.1',
    description=('Library for downloading and parsing Open Financial Exchange'
                 '(OFX) formatted data from financial institutions'),
    long_description=long_description,

    url='https://github.com/csingley/ofxtools',

    author='Christopher Singley',
    author_email='csingley@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='ofx, Open Financial Exchange',

    packages=['ofx'],

    data_files=[
        ('config', ['config/fi.cfg']),
        (usercfgdir, ['config/ofxget_example.cfg']),
    ],

    entry_points={
        'console_scripts': [
            'ofxget=ofx.Client:main',
        ],
    },
)

