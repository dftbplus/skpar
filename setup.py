#!/usr/bin/env python3

# Copyright (C) 2013 - 2016  Stanislav Markov, The University of Hong Kong
# Please see the accompanying LICENSE file for further information.

#from distutils.core import setup, Command
#from distutils.command.build_py import build_py as _build_py
#from glob import glob
from setuptools import setup

from os.path import join

import os
import sys

if sys.version_info < (3, 0, 0, 'final', 0):
    raise SystemExit('Python 3 is required!')

short_description = ('Optimisation of Slater-Koster files (.skf) '+
                    'for density functional-based tight binding (DFTB)')
long_description  = open('README.txt').read()
name         = 'skopt'
# todo: try to regenerate ./skopt/__init__.py to include the version stated here
version      = '0.1.0'

package_dir  = {'skopt': 'skopt',}

packages     = []
for dirname, dirnames, filenames in os.walk('skopt'):
        if '__init__.py' in filenames:
            packages.append(dirname.replace('/', '.'))

package_data = {}

scripts=['bin/skopt', 'bin/dftbutils']

## try to cater for windows
if 'sdist' in sys.argv or os.name in ['ce', 'nt']:
    for s in scripts[:]:
        print ("Making .bat files for Windows")
        scripts.append(s + '.bat')

# data_files needs (directory, files-in-this-directory) tuples
data_files = []

setup(name=name,
      version=version,
      description=short_description,
      long_description=long_description,
      url='https://bitbucket.org/stanmarkov/skopt',
      maintainer='Stanislav Markov, The University of Hong Kong',
      maintainer_email='figaro@hku.hk',
      keywords=['dftb', 'slater-koster integrals', 'dftb+', 'lodestar', 'particle swarm optimisation', 'optimisation', 'pso', 'skopt'],
      license='MIT',
      platforms=['any'],
      packages=packages,
      package_dir=package_dir,
      package_data=package_data,
      scripts=scripts,
      data_files=data_files,
#      classifiers=[
#        'Development Status :: 0 - initial/exploratory',
#        'Intended Audience :: Developers',
#        'Intended Audience :: Education',
#        'Intended Audience :: Science/Research',
#        'Environment :: Console',
#        'Operating System :: OS Independent',
#        'License :: OSI Approved :: MIT',
#        'Programming Language :: Python :: 3',
#        'Topic :: Scientific/Engineering',
#        'Topic :: Software :: Development',
#        ],
)
