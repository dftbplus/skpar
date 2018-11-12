"""Module that handles reference data
"""
import numpy as np
import uuid
from os.path import abspath, expanduser
from skpar.core.utils import get_ranges

def parse_refdata_input(userinp, db=None):
    """Get reference data based on user directives.

    User directives are in `userinp` and either contain data or indicate a
    source, from which to obtain the data. If `db` is none, a
    """
    if db is None:
        db = {}

    for uid, item in userinp.items():
        _ref = ReferenceItem(item, uid)
        print(_ref)
        db.update({_ref.uid: _ref})
    return db

def get_refdata(uid, db):
    """Return the reference data corresponding to a unique reference ID.
    """
    # the following makes no hard assumption of how the reference data item is
    # stored -- could be a dictionary, could be an object that emulates
    # dictionary; all we need is a .get() support
    refitem = db.get(uid)
    return refitem.get()

def parse_refsource(userinp):
    """Parse users input and return reference data.
    """
    if 'file' in userinp.keys():
        # user input is an instruction where/how to obtain values
        _file = abspath(expanduser(userinp['file']))
        # actual data in file -> load it
        # set default loader_args, assuming 'column'-organised data
        loader_args = {} #{'unpack': False}
        # overwrite defaults and add new loader_args
        loader_args.update(userinp.get('loader_args', {}))
        # make sure we don't try to unpack a key-value data
        if 'dtype' in loader_args.keys() and\
            'names' in loader_args['dtype']:
                loader_args['unpack'] = False
        # read file
        try:
            _data = np.loadtxt(_file, **loader_args)
        except ValueError:
            # `file` was not understood
            print ('np.loadtxt cannot understand the contents of {}'\
                    .format(_file))
            print ('with the given loader arguments: {}'\
                    .format(**loader_args))
            raise
        except (IOError, FileNotFoundError):
            # `file` was not understood
            print ('Reference data file {} cannot be found'\
                    .format(_file))
            raise
        # do some filtering on columns and/or rows if requested
        # note that file to 2D-array mapping depends on 'unpack' from
        # loader_args, which transposes the loaded array.
        postprocess = userinp.get('process', {})
        if postprocess:
            if 'unpack' in loader_args.keys() and loader_args['unpack']:
                # since 'unpack' transposes the array, now row index
                # in the original file is along axis 1, while column index
                # in the original file is along axis 0.
                key1, key2 = ['rm_columns', 'rm_rows']
            else:
                key1, key2 = ['rm_rows', 'rm_columns']
            for axis, key in enumerate([key1, key2]):
                rm_rngs = postprocess.get(key, [])
                if rm_rngs:
                    indexes=[]
                    # flatten, combine and sort, then delete corresp. object
                    for rng in get_ranges(rm_rngs):
                        indexes.extend(list(range(*rng)))
                    indexes = list(set(indexes))
                    indexes.sort()
                    _data = np.delete(_data, obj=indexes, axis=axis)
            scale = postprocess.get('scale', 1)
            _data = _data * scale
        return _data


class ReferenceItem():

    def __init__(self, userinp, uid=None):
        """Reference item contains unique id and data"""

        assert isinstance(userinp, dict)
        self.uid = uuid.uuid1() if uid is None else uid
        doc = userinp.get('doc', None)
        self.doc = self.uid if doc is None else doc
        #
        _source = userinp.get('source', None)
        if _source is not None:
            self.data = parse_refsource(_source)
        #
        else:
            _data = userinp.get('data', None)
            if _data is not None:
                if isinstance(_data, dict):
                    # key value pair
                    dtype = [('keys','S15'), ('values','float')]
                    self.data = np.array([(key,val) for key,val in
                                          _data.items()], dtype=dtype)
                else:
                    # scalar or array like
                    self.data = np.atleast_1d(_data)
            else:
                logger.critical('Improperly declared ReferenceItem'\
                               'having both "source" and "data".')
                raise(RuntimeError)

        # lock it
        self.data.flags.writeable = False

    def get(self):
        """Return the data"""
        return self.data

    def __repr__(self):
        ss = []
        ss.append('refid: {}'.format(self.uid))
        ss.append('  doc: {}'.format(self.doc))
        ss.append(' data: {}'.format(self.data))
        return "\n"+"\n".join(ss)

