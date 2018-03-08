#!/usr/bin/env python3

# Copyright (C) 2013 - 2017  Stanislav Markov
# Please see the accompanying LICENSE file for further information.

from setuptools import setup
from os.path import join
import os
import sys

if sys.version_info < (3, 0, 0, 'final', 0):
    raise SystemExit('Python 3 is required!')

name         = 'skpar'
short_description = ('Optimisation of Slater-Koster files (.skf) '+
                    'for density functional-based tight binding (DFTB)')
long_description  = open('README.txt').read()

version      = '0.2.4'

package_dir  = {'skpar': 'skpar',}

packages     = []
for dirname, dirnames, filenames in os.walk('skpar'):
        if '__init__.py' in filenames:
            packages.append(dirname.replace('/', '.'))

package_data = {}

scripts=['bin/skpar', 'bin/dftbutils', 'bin/check_dftblog', 
        'bin/skpar_splinerepfit', 'bin/skpar_addrepulsive']

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
      url='https://github.com/smarkov/skpar',
      download_url = 'https://github.com/smarkov/skpar/archive/{}.tar.gz'.format(version),
      author='Stanislav Markov, The University of Hong Kong',
      author_email='figaro@hku.hk',
      keywords=['dftb', 'slater-koster integrals', 'dftb+', 'lodestar', 'particle swarm optimisation', 'optimisation', 'pso', 'skpar'],
      license='MIT',
      platforms=['any'],
      packages=packages,
      package_dir=package_dir,
      package_data=package_data,
      scripts=scripts,
      data_files=data_files,
      install_requires = [
            'numpy',
            'scipy',
            'deap',
            'pyyaml',
            'matplotlib'
          ],
      classifiers=[],
)
