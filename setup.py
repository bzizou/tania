# -*- coding: utf-8 -*-
import re
import os.path as op
from setuptools import setup


def read(filename):
    ''' Return the file content. '''
    with open(op.join(op.abspath(op.dirname(__file__)), filename)) as fd:
        return fd.read()


def get_version():
    return re.compile(r".*__version__ = '(.*?)'", re.S)\
             .match(read(op.join('tania', '__init__.py'))).group(1)

with open("README.md", "r") as fh:
        long_description = fh.read()

setup(
    name='tania',
    author='Bruno Bzeznik',
    author_email='Bruno.Bzeznik@univ-grenoble-alpes.fr',
    version=get_version(),
    url='https://github.com/bzizou/tania',
    install_requires=[
        'configparser',
        'pathlib',
        'filelock'
    ],
    packages=['tania'],
    zip_safe=False,
    description='A greedy processes sniper',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNU GPL v3",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',  # noqa
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',
    ],
    python_requires='>=3.5',
    entry_points='''
        [console_scripts]
        tania=tania.main:main
    ''',
)
