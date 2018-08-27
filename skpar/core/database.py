"""Database and query objects.
"""
import numpy as np
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

def update(database, model, data=None):
    """Update model storage with input data items.

    Args:
        database(obj): supporting get() and update()
        model(str or dict): model (dict) or model name
        data(dict): key-value items for the model to be updated
    """
    if data is None:
        data = {}
    try:
        # model is a key and in DB; update it with data
        database.get(model, None).update(data)
    except (KeyError, AttributeError):
        # model is a key but not in DB; None has no .update()
        database.update({model: data})
    except TypeError:
        # model is a dict; not hashable
        assert data == {}, data
        database.update(model)


class Database():
    """A database object providing several methods to access/modify the data.
    """
    def __init__(self):
        """Yield an object for data storage, NOT to be accessed directly."""
        self._storage = {}

    def clear(self):
        """Clear the contents of DB"""
        self._storage = {}

    def update(self, model, data=None):
        """Update storage with a new model"""
        update(self._storage, model, data)

    def get(self, model, default=None):
        """Get a model."""
        return self._storage.get(model, default)

    def get_item(self, model, item):
        """Get an item from a model; None if either does not exist."""
        return self._storage.get(model, {}).get(item, None)

    def all(self):
        """Yield internal database object"""
        return self._storage

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
                result.append(database.get(model, {}).get(self.key))
        else:
            result = database.get(self.model_names, {}).get(self.key)
        if atleast_1d:
            result = np.atleast_1d(result)
        return result

    def __repr__(self):
        """Yield a summary of the query.
        """
        srepr = []
        srepr.append('\tQuery key: {}'.format(self.key))
        srepr.append('\tModel Names: {}'.format(self.model_names))
        if self.database:
            srepr.append('\tQuery result: {}'.format(self.__call__()))
        return '\n'+"\n".join(srepr)
