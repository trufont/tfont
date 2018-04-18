from time import time

# TODO: we could keep only the tracking variants later on


class TaggingList:
    __slots__ = "_parent"

    def __init__(self, parent):
        self._parent = parent

    def __delitem__(self, index):
        sequence = self._sequence
        sequence[index]._parent = None
        del sequence[index]

    def __getitem__(self, index):
        return self._sequence[index]

    # we don't implement __setitem__

    def __contains__(self, value):
        return value in self._sequence

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._sequence == other._sequence

    def __iter__(self):
        return iter(self._sequence)

    def __len__(self):
        return len(self._sequence)

    def __repr__(self):
        return repr(self._sequence)

    def __reversed__(self):
        return reversed(self._sequence)

    @property
    def _sequence(self):
        raise NotImplementedError

    def append(self, value):
        self._sequence.append(value)
        value._parent = self._parent

    # we don't implement clear()

    # we don't implement copy()

    def extend(self, values):
        self._sequence.extend(values)
        parent = self._parent
        for value in values:
            value._parent = parent

    def index(self, value):
        return self._sequence.index(value)

    def insert(self, index, value):
        self._sequence.insert(index, value)
        value._parent = self._parent

    def pop(self, index=-1):
        value = self._sequence.pop(index)
        value._parent = None
        return value

    def remove(self, value):
        self._sequence.remove(value)
        value._parent = None

    def reverse(self):
        self._sequence.reverse()


class TaggingDictList(TaggingList):
    __slots__ = ()

    def __delitem__(self, key):
        sequence = self._sequence
        if isinstance(key, str):
            prop = self._property
            for index, value in enumerate(sequence):
                if getattr(value, prop) == key:
                    sequence[index]._parent = None
                    del sequence[index]
                    return
            raise KeyError(key)
        sequence[key]._parent = None
        del sequence[key]

    def __getitem__(self, key):
        sequence = self._sequence
        if isinstance(key, str):
            prop = self._property
            for index, value in enumerate(sequence):
                if getattr(value, prop) == key:
                    return sequence[index]
            raise KeyError(key)
        return sequence[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            parent = self._parent
            prop = self._property
            existing = value._parent == parent
            if existing and getattr(value, prop) == key:
                return
            setattr(value, prop, key)
            value._parent = parent
            sequence = self._sequence
            for index, value_ in enumerate(sequence):
                if value_ == value:
                    delIndex = index
                elif getattr(value_, prop) == key:
                    sequence[index] = value
                    if not existing:
                        return
            if existing:
                del sequence[delIndex]
            else:
                sequence.append(value)
            return
        # we don't implement non-str __setitem__
        raise KeyError("indices must be str, not %s" % key.__class__.__name__)

    def __contains__(self, key):
        if isinstance(key, str):
            prop = self._property
            for value in self._sequence:
                if getattr(value, prop) == key:
                    return True
            return False
        return key in self._sequence

    def append(self, value):
        parent = self._parent
        if value._parent == parent:
            return
        value._parent = parent
        sequence = self._sequence
        prop = self._property
        propValue = getattr(value, prop)
        for index, value_ in enumerate(sequence):
            if getattr(value_, prop) == propValue:
                sequence[index] = value
                return
        sequence.append(value)

    # get()?

    # for now we don't enforce uniqueness in extend(), insert()

    def extend(self, values):
        raise NotImplementedError


class TaggingDict:
    # TODO: we could lazify this...
    __slots__ = "_parent"

    def __init__(self, parent):
        self._parent = parent

    def __delitem__(self, key):
        del self._sequence[key]

    def __getitem__(self, key):
        return self._sequence[key]

    def __setitem__(self, key, value):
        self._sequence[key] = value

    def __contains__(self, key):
        return key in self._sequence

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._sequence == other._sequence

    def __iter__(self):
        return iter(self._sequence)

    def __len__(self):
        return len(self._sequence)

    def __repr__(self):
        return repr(self._sequence)

    @property
    def _sequence(self):
        raise NotImplementedError

    # we don't implement clear()

    # we don't implement copy()

    def keys(self):
        return self._sequence.keys()

    def items(self):
        return self._sequence.items()

    # we don't implement pop()

    # we don't implement update()

    def values(self):
        return self._sequence.values()

# --------
# Tracking
# --------


# this will work for
# layer_components, layer_paths, layer_guidelines, path_points
class TrackingList(TaggingList):
    _graphics = True  # only False for guidelines
    _selectible = True  # only False for paths

    def __delitem__(self, index):
        sequence = self._sequence
        value = sequence[index]
        del sequence[index]
        #
        if index.__class__ is slice:
            for v in value:
                self.applyChange(v, False)
        else:
            self.applyChange(value, False)

    # we don't implement __setitem__

    def applyChange(self, value=None, isAdding=None):
        graphics = self._graphics
        parent = self._parent
        if value is not None:
            if isAdding:
                value._parent = parent
            else:
                value._parent = None
        # Path?
        if not hasattr(parent, "_selectionBounds"):
            # the first parent is Path
            # handle Path, then shift our parent to Layer
            if graphics:
                parent._bounds = parent._graphicsPath = None
            parent = parent._parent
            if parent is None:
                return
        # Layer
        if graphics:
            parent._bounds = parent._closedGraphicsPath = \
                parent._openGraphicsPath = parent._selectedPaths = None
        if value is not None:
            if self._selectible:
                if value.selected:
                    if isAdding:
                        parent._selection.add(value)
                    else:
                        parent._selection.remove(value)
                    parent._selectedPaths = parent._selectionBounds = None
            else:
                if isAdding:
                    value.selected = False
        else:
            if isAdding is not None:
                parent.selected = False
        # Glyph
        glyph = parent._parent
        if glyph is not None:
            glyph._lastModified = time()

    def append(self, value):
        self._sequence.append(value)
        #
        self.applyChange(value, True)

    # we don't implement clear()

    def extend(self, values):
        self._sequence.extend(values)
        for value in values:
            self.applyChange(value, True)

    def insert(self, index, value):
        self._sequence.insert(index, value)
        #
        self.applyChange(value, True)

    def pop(self, index=-1):
        value = self._sequence.pop(index)
        #
        self.applyChange(value, False)
        #
        return value

    def remove(self, value):
        self._sequence.remove(value)
        #
        self.applyChange(value, False)


# this will work for
# layer_anchors, glyph_layers
class TrackingDictList(TaggingDictList):
    __slots__ = ()

    _getattr = getattr
    _strict = False

    def __delitem__(self, key):
        sequence = self._sequence
        if isinstance(key, str):
            prop = self._property
            for index, value in enumerate(sequence):
                if self._getattr(value, prop) == key:
                    value = sequence[index]
                    del sequence[index]
                    self.applyChange(value, False)
                    return
            raise KeyError(key)
        value = sequence[key]
        del sequence[key]
        #
        if key.__class__ is slice:
            for v in value:
                self.applyChange(v, False)
        else:
            self.applyChange(value, False)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            parent = self._parent
            prop = self._property
            existing = value._parent == parent
            if existing and self._getattr(value, prop) == key:
                return
            setattr(value, prop, key)
            sequence = self._sequence
            for index, value_ in enumerate(sequence):
                if value_ == value:
                    delIndex = index
                elif self._getattr(value_, prop) == key:
                    sequence[index] = value
                    if not existing:
                        self.applyChange(value, True)
                        return
            if existing:
                del sequence[delIndex]
            else:
                sequence.append(value)
            self.applyChange(value, True)
            return
        # we don't implement non-str __setitem__
        raise KeyError("indices must be str, not %s" % key.__class__.__name__)

    def applyChange(self, value=None, isAdding=None):
        parent = self._parent
        if value is not None:
            if isAdding:
                value._parent = parent
            else:
                value._parent = None
        # Layer?
        if hasattr(parent, "_selectionBounds"):
            # the first parent is Layer
            # handle Layer, then shift our parent to Glyph
            if value is not None:
                if value.selected:
                    if isAdding:
                        parent._selection.add(value)
                    else:
                        parent._selection.remove(value)
                    parent._selectionBounds = None
            else:
                if isAdding is not None:
                    parent.selected = False
            parent = parent._parent
            if parent is None:
                return
        # Glyph
        parent._lastModified = time()

    def append(self, value):
        parent = self._parent
        if value._parent == parent:
            return
        value._parent = parent
        sequence = self._sequence
        if self._strict:
            prop = self._property
            propValue = self._getattr(value, prop)
            for index, value_ in enumerate(sequence):
                if self._getattr(value_, prop) == propValue:
                    sequence[index] = value
                    self.applyChange(value, True)
                    return
        sequence.append(value)
        self.applyChange(value, True)

    # we don't implement clear()

    # we don't implement extend()

    def insert(self, index, value):
        self._sequence.insert(index, value)
        #
        self.applyChange(value, True)

    def pop(self, index=-1):
        value = self._sequence.pop(index)
        #
        self.applyChange(value, False)
        #
        return value

    def remove(self, value):
        self._sequence.remove(value)
        #
        self.applyChange(value, False)


class TrackingDict(TaggingDict):
    __slots__ = ()

    def __delitem__(self, key):
        del self._sequence[key]
        #
        parent = self._parent
        while not hasattr(parent, "_lastModified"):
            parent = parent._parent
        parent._lastModified = time()

    def __setitem__(self, key, value):
        # do we got same-value elision?
        self._sequence[key] = value
        #
        parent = self._parent
        while not hasattr(parent, "_lastModified"):
            parent = parent._parent
        parent._lastModified = time()

    # we don't implement clear()

    # we don't implement pop()

    # we don't implement update()
