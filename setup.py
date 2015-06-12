#!/usr/bin/env python
from distutils.core import setup

import src.skopt as skopt

setup(name='skopt',
      version=skopt.__revision__,
      description='Optimisation of Slater-Koster files (.skf) for DFTB with the help of SKGEN',
      long_description=open('README.txt').read(),
      author=skopt.__author__,
      author_email=skopt.__email__,
      url='https://bitbucket.org/dftbplus/sktools',
      packages=['skopt', ],
      package_dir={'': 'src', },
      scripts=[ "bin/skopt", "bin/skeval"],
      platforms=['any'],
      keywords=['dftb', 'slater-koster integrals', 'dftb+', 'lodestar', 'particle swarm optimisation', 'pso', 'skopt'],
#      license='LGPL',
      classifiers=[
        'Development Status :: 0 - initial/exploratory',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Operating System :: OS Independent',
#        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        ],
)
