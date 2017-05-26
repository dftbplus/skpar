#!/bin/bash
# With this script we obtain the free atoms from
# all-electron calculation within the prescribed basis,
# regardless of compression radii, and 
# regardless of valence orbital intended for dftb:
# NOTABENE: this script must be run in advance, 
# and NOT in the optimisation loop

# skgen expects skdefs.py -> make a link
/bin/ln -sf skdefs.freeatoms.py skdefs.py

# free atoms
skgen atom -b slateratom C
skgen atom -b slateratom C1

# rm link
/bin/rm skdefs.py
