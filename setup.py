#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Package setup
#
# ------------------------------------------------


# config
# ------
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages


config = __import__('package')
with open('requirements.txt', 'r') as reqs:
    requirements = map(lambda x: x.rstrip(), reqs.readlines())


test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-runner'
]


# files
# -----
with open('README.rst') as readme_file:
    readme = readme_file.read()


# exec
# ----
setup(
    name=config.__pkg__,
    version=config.__version__,
    description=config.__info__,
    long_description=readme,
    author=config.__author__,
    author_email=config.__email__,
    url=config.__url__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=requirements,
    license="Apache-2.0",
    zip_safe=False,
    keywords=[config.__pkg__, 'flask', 'permissions', 'authorization', 'user', 'group', 'role'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apple Public Source License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    tests_require=test_requirements
)
