# -*- coding: utf-8 -*-

import re
from setuptools import setup
from setuptools import find_packages


REQUIRES = [
    'six>=1.9.0',
    'blinker>=1.3',
]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='nplusone',
    version=find_version('nplusone/__init__.py'),
    description='Detecting the n+1 queries problem in Python',
    long_description=read('README.rst'),
    author='Joshua Carp',
    author_email='jm.carp@gmail.com',
    url='https://github.com/jmcarp/nplusone',
    packages=find_packages(exclude=('test*', )),
    package_dir={'nplusone': 'nplusone'},
    include_package_data=True,
    install_requires=REQUIRES,
    license=read('LICENSE'),
    zip_safe=False,
    keywords='nplusone',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests'
)
