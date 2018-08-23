import numpy as np


class Query(object):
    """Decouple the intent of making a query from actually making it.

    A query is registered upon instance creation, by stating a model_name
    (or a list thereof) and a key to be queried from the corresponding
    dict(s). However, there is no binding to any object containing the 
    data to be queried at this stage. The binding happens upon execution
    of the query, which attempts to find the model data in a common
    database (`Query.modelsdb`) or a database that is passed as an argument
    to the __call__() method.

    The class has a database of models (dict objects, resolved by name).
    The database is built by allocating the dictionaries via
    Query.add_modelsdb('model_name', dict), and can be flushed by 
    Query.flush_modelsdb().
    Initially, dict items in a modelsdb will be empty, but subsequently the 
    model calculators will continually update the corresponding dictionaries.

    Examples::
        >>> # usage with modelsdb belonging to the class
        >>> Query.flush_modelsdb()
        >>> db1 = {'a':1, 'b':2}
        >>> db2 = {'a':3, 'b':4, 'c':7}
        >>> Query.add_modelsdb('d1', db1)
        >>> Query.add_modelsdb('d2', db2)
        >>> q1 = Query('d1', 'a')
        >>> q2 = Query(['d1', 'd2'], 'b')
        >>> pprint (q1())
        >>> pprint (q2())
        1
        [2, 4]
        >>> # usage with modelsdb passed at the stage of query
        >>> q3 = Query('d3', 'e')
        >>> modelsdb={}
        >>> db3 = {}
        >>> modelsdb['d3'] = db3
        >>> db3['e'] = 10.
        >>> pprint (q3(modelsdb))

    TODO:
        It is conceivable to benefit from a multi-key query (be it over a
        single or multiple models), but this is still in the future.
    """
    __modelsdb = {}
    
    @classmethod
    def flush_modelsdb(cls):
        cls.__modelsdb = {}

    @classmethod
    def get_modeldb(cls, name):
        try:
            modelref = cls.__modelsdb[name]
            return modelref
        except KeyError:
            return None

    @classmethod
    def add_modelsdb(cls, name, ref=None):
        """Add a new name-dict pair to the modelsdb.
           `name` must be a string. ref a dict.
        """
        if name in cls.__modelsdb:
            return cls.__modelsdb[name]
        else:
            if ref is None:
                ref = {}
                cls.__modelsdb[name] = ref
            else:
                cls.__modelsdb[name] = ref
        return ref
        
    def __init__(self, model_names, key):
        self.model_names = model_names
        self.key = key
            
    def __call__(self, modelsdb=None, atleast_1d=True):
        if modelsdb == None:
            modelsdb = self.__modelsdb
        if isinstance(self.model_names, list):
            result = []
            for m in self.model_names:
                result.append(modelsdb[m][self.key])
        else:
            result = modelsdb[self.model_names][self.key]
        if atleast_1d:
            result = np.atleast_1d(result)
        return result
