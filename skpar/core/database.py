"""Database and query objects.
"""
import numpy as np
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

def update(database, model, data):
    """Update model database with input data items.

    Args:
        database(obj): database, supporting get(), update() and a way to check
                       if item is contained
        model(str): model name
        data(dict): new data to be put in the model-own database
    """
    try:
        # assume model already exists in the DB
        modeldb = database.get_model(model)
        modeldb.update(data)
    except AttributeError:
        database.add_model(model, data)


class Database():
    """A database object providing several methods to access/modify the data.

    The public methods for accessing the internal database are:
        * update_modeldb -- add data to a model (create the model if missing)
        * query -- get data from a model
        * purge -- clear the internal database
    """
    def __init__(self):
        """Yield an object for data storage, NOT to be accessed directly."""
        self._database = {}

    def purge(self):
        """Clear the contents of DB"""
        self._database = {}

    def get_model(self, model):
        """Get a reference to a specific model in the database"""
        try:
            modelref = self._database[model]
            return modelref
        except KeyError:
            return None

    def add_model(self, model, data=None):
        """Add model to the database and return its reference.

        If data is not None, initialise the data for the model.
        If model happens to be already in the database and data is not None,
        its data is being replaced with the input argument.
        """
        if data is not None:
            self._database[model] = data
        else:
            if model not in self._database:
                self._database[model] = {}
        return self._database[model]

    def update(self, model, data):
        """Update the data of a given model in the database"""
        update(self, model, data)

    def get(self, model, item):
        """Get a particular data item from a particular model."""
        return self._database[model][item]

    def all(self):
        """Yield internal database object"""
        return self._database

    # legacy stuff; will  likely disappear when refactoring objectives
    def query(self, models, item, atleast_1d=True):
        """Return the value of an item from a model or a list of models."""
        _query = Query(models, item, self)
        return _query(atleast_1d=atleast_1d)


class Query():
    """Decouple the declaration of query from performing a query."""
    def __init__(self, model_names, key, database=None):
        """Instantiate a query to be performed later by calling it.

        A call to the object will result in:
            database.model.key or
            [database.model1.key, database.model2.key, ...]
        depending on the number of model names provided
        Note that it is mandatory to provide support for database being passed
        to __call__ instead of __init__. This way the same queries may be
        duplicated and later called in parallel with different databases

        Args:
            model_names: level-one keys in the database
            key: level-two keys
            database: where the search should be performed; could be provided
                      at call time instead of initialisation
        """
        self.database = database
        self.model_names = model_names
        self.key = key

    def __call__(self, database=None, atleast_1d=True):
        """Execute data query.

        Args:
            database: database; should not be needed
            atleast_1d: return numpy.array even if data is a float

        Return:
            The result of the query - as a numpy array by default.
        """
        if database is None:
            database = self.database
        assert database is not None
        if isinstance(self.model_names, list):
            result = []
            for model in self.model_names:
                result.append(database.get(model, self.key))
        else:
            result = database.get(self.model_names, self.key)
        if atleast_1d:
            result = np.atleast_1d(result)
        return result
