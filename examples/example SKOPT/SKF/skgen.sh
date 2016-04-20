#skgen atom Si
#skgen potcomp Si
#skgen wavecomp Si
#
#skgen atom O
#skgen potcomp O
#skgen wavecomp O
#
#skgen twocnt -g 0.2 -s potential Si Si
#skgen twocnt -g 0.2 -s potential O O
#skgen twocnt -g 0.2 -s potential Si O
#
#skgen sktable -d Si Si
skgen sktable -d O O
#skgen sktable -d Si O
