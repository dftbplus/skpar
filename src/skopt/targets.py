def setTargets(RefDict,KeysWeights):
    """
    """
    from deap import base,creator
    creator.create("Target",tuple,weight=None)
    toolbox = base.Toolbox()
    toolbox.register("target", creator.Target)
    targets = list()
    KW = dict(KeysWeights)
    sumW = sum([KW[k] for k in list(KW.keys())])
    # normalize the weights prior to final assignments to targets
    for k in sorted(KW.keys()):
        try:
            t = toolbox.target((k,RefDict[k]))
            t.weight = KW[k]/sumW
            targets.append(t)
        except KeyError:
            print("ERROR: '{0}' not found in reference data. Failed to add corresponding target.".format(k))
            raise
    return targets

