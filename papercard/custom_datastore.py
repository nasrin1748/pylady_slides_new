"""Simple, observable, key/value data store for COW apps."""

import json


class ObservableMixin:
    """Mixin for simple-istic observables."""

    def add_listener(self, listener):
        """
        Add a listener for changes to the dictionary.
        """

        self._listeners.append(listener)

    def call_listeners(self):
        """
        Call all listeners when the dictionary has been changed.
        """

        for listener in self._listeners:
            listener(self)


class DataStore(dict, ObservableMixin):
    """A transient data store that just wraps a Python dictionary."""

    def __init__(self, **kwargs):
        """Constructor."""

        self._data = {**kwargs}
        self._listeners = []

    def clear(self):
        """
        Removes all items from the dictionary.
        """

        self._data.clear()
        self.call_listeners()

    def copy(self):
        """
        Returns a shallow copy of the dictionary.
        """

        return type(self)(**self._data.copy())

    def get(self, key, default=None):
        """
        Returns the value for key in the dictionary; if not found returns a default
        value.
        """

        return self._data.get(key, default=default)

    def items(self):
        """
        Return a new view of the dictionary’s items ((key, value) pairs).
        """

        return self._data.items()

    def keys(self):
        """
        Return a new view of the dictionary’s keys.
        """

        return self._data.keys()

    def values(self):
        """
        Return a new view of the dictionary’s values.
        """

        return self._data.values()

    def pop(self, key, default=None):
        """
        If key is in the dictionary, remove it and return its value, else return
        default. If default is not given and key is not in the dictionary, a KeyError
        is raised.
        """

        result = self._data.pop(key, default)
        self.call_listeners()

        return result

    def popitem(self):
        """
        Remove and return a (key, value) pair from the dictionary.
        """

        result = self._data.popitem()
        self.call_listeners()

    def setdefault(self, key, value=None):
        """
        If key is in the dictionary, return its value. If not, insert key with a
        value of default and return default. default defaults to None.
        """

        self._data.setdefault(key, value)
        self.call_listeners()

        return value

    def update(self, iterable):
        """
        Update the dictionary with the key/value pairs from other, overwriting existing
        keys. Return None. For each key/value pair in the iterable, insert them into the
        data store.
        """

        self._data.update(iterable)
        self.call_listeners()

    def __len__(self):
        """
        Return the number of items in the dictionary.
        """

        return len(self._data)

    def __getitem__(self, key):
        """
        Called to implement evaluation of self[key].
        """

        return self._data[key]

    def __setitem__(self, key, value):
        """
        Called to implement assignment to self[key].
        """

        self._data[key] = value
        self.call_listeners()

    def __delitem__(self, key):
        """
        Called to implement deletion of self[key].
        """

        del self._data[key]
        self.call_listeners()

    def __iter__(self):
        """
        Return an iterator over the keys.
        """
        return iter(self._data)

    def __contains__(self, key):
        """
        Called to implement membership test operators.
        """

        return key in self._data


class PersistentDataStore(dict, ObservableMixin):
    """
    Wraps a JavaScript Storage object for browser based data storage. Looks
    and feels mostly like a Python dictionary but has the same characteristics
    as a JavaScript localStorage object.
    For more information see:
    https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API
    """

    def __init__(self, **kwargs):
        """
        The underlying Storage object is an instance of Window.localStorage
        (it persists between browser opening/closing). Any **kwargs are added
        to the dictionary.
        """

        self._listeners = []

        try:
            from js import localStorage
            self.store = localStorage
        except ImportError:
            self.store = {}

        if kwargs:
            self.update(kwargs.items())

    def clear(self):
        """
        Removes all items from the data store.
        """

        result = self.store.clear()
        self.call_listeners()

        return result

    def copy(self):
        """
        Returns a Python dict copy of the data store.
        """
        return {k: v for k, v in self.items()}

    def get(self, key, default=None):
        """
        Return the value of the item with the specified key.
        """
        if key in self:
            return self[key]
        return default

    def items(self):
        """
        Yield over the key/value pairs in the data store.
        """
        for i in range(0, len(self)):
            key = self.store.key(i)
            value = self[key]
            yield (key, value)

    def keys(self):
        """
        Returns a list of keys stored by the user.
        """
        result = []
        for i in range(0, len(self)):
            result.append(self.store.key(i))
        return result

    def pop(self, key, default=None):
        """
        Pop the specified item from the data store and return the associated
        value.
        """
        if key in self:
            result = self[key]
            del self[key]
        else:
            result = default

        self.call_listeners()
        return result

    def popitem(self):
        """
        Makes no sense given the underlying JavaScript Storage object's
        behaviour.
        """
        raise NotImplementedError

    def setdefault(self, key, value=None):
        """
        Returns the value of the item with the specified key.
        If the key does not exist, insert the key, with the specified value.
        Default value is None.
        """
        if key in self:
            return self[key]
        self[key] = value

        self.call_listeners()
        return value

    def update(self, iterable):
        """
        For each key/value pair in the iterable, insert them into the
        data store.
        """
        for key, value in iterable:
            self[key] = value

        self.call_listeners()

    def values(self):
        """
        Return a list of the values stored in the data store.
        """
        result = []
        for i in range(0, len(self)):
            key = self.store.key(i)
            result.append(self[key])
        return result

    def __len__(self):
        """
        Number of items in the data store.
        """
        return self.store.length

    def __getitem__(self, key):
        """
        Get the item (as a string) stored against the given key.
        """
        if key in self:
            return json.loads(self.store.getItem(key))
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """
        Set the value (as a JSON string) against the given key.
        The underlying JavaScript Storage only stored values as strings.
        """

        result = self.store.setItem(key, json.dumps(value))
        self.call_listeners()
        return result

    def __delitem__(self, key):
        """
        Delete the item stored against the given key.
        """
        if key in self:
            result = self.store.removeItem(key)
            self.call_listeners()
            return result
        else:
            raise KeyError(key)

    def __iter__(self):
        """
        Return an iterator over the keys.
        """
        return (key for key in self.keys())

    def __contains__(self, key):
        """
        Checks if a key is in the datastore.
        """
        return key in self.keys()