#!/usr/bin/env python3
import ipdb
ipdb.set_trace(context=5)
import os
import numpy as np
import yaml
from pprint import pformat
from collections import OrderedDict
import logging
from skopt.utils import setup_logger
from skopt.input import get_file_data, System, refdatahandler, RefData

def parse_systems(data, logger=None, **kwargs):
    """
    """
    if logger is None:
        logger = logging.getLogger('__name__')
    systems = []
    for key, value in data.items():
        logger.info('Defining system {}'.format(key))
        # assume default filename for the system.yaml
        _file = 'system_{}.yaml'.format(key)
        # get system.data
        _data = get_file_data(val, _file, logger)
        # create an instance with default attributes
        ss = System(logger=logger, **_data)
        # reference data and corresponding weights must be reinitialised
        ss.refdata, ss.weights = 
            parse_refdata(_data.get('refdata', {}), logger)
#        # tasks may need to be reinitialised too
#        ss.tasks = parse_tasks(_data.get('tasks', {}), logger)
        systems.append(ss)
    return systems   


def parse_refdata(data, logger=None, **kwargs):
    """
    """
    ref_data = []
    ref_weights = []
    for key, val in data.items():
        logger.info ("Parsing reference item {}".format(key))
        # logger.debug (pformat(val))
        _ref = refdatahandler.get(key, RefData)(val, logger=logger)
        # currently the _ref object does not have a .data and .weights
        # fields, but different reference groups, each with a 
        # relative weight and subweights for individual reference items
        # within the group
        # this need to be serialised somehow!
        ref_data.append(_ref.data)
        ref_weights.append(_ref.weights)
    return ref_data, ref_weights

def parse_tasks(data, logger=None, **kwargs):
    
def parse_executables(data, logger=None, **kwargs):

def parse_skopt_in(file, logger=None, **kwargs):
    """
    """
    if logger is None:
        logger = logging.getLogger('__name__')
    skopt_in_data = loadyaml(file)
    systems     = parse_systems(skopt_in_data, logger)
    refdata     = parse_refdata(skopt_in_data, logger)
    tasks       = parse_tasks(skopt_in_data, logger)
    executables = parse_executables(skopt_in_data, logger)

        # parse reference data for each system
        _refdata = []
        for key, val in _data['refdata'].items():
            logger.info ("Parsing reference item {}".format(key))
            logger.debug (pformat(val))
            _ref = refdatahandler.get(key, RefData)(val, logger=logger)
            _refdata.append(_ref)


if __name__ == "__main__":
    logger = setup_logger('skopt', 'skopt.dbg.log', verbosity=logging.INFO)
    file = 'skopt_in.yaml'
    logger.info('Reading {}'.format(file))
    parse_skopt_in(file, logger=logger)
    ipdb.pm()
