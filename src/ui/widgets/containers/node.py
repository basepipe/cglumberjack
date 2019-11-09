# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from Qt import QtXml


# noinspection PyPropertyAccess,PyProtectedMember
class Node(object):

    def __init__(self, name, parent=None):
        self._name = name
        self._parent = parent
        self._children = []
        self._value = None
        if parent is not None:
            parent.addChild(self)

    @staticmethod
    def typeInfo():
        return 'NODE'

    def addChild(self, child):
        self._children.append(child)

    def insertChild(self, position, child):
        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        if position < 0 or position > len(self._children):
            return False

        self._children.pop(position)
        self.child._parent = None
        return True

    # noinspection PyArgumentList
    def attrs(self):
        classes = self.__class__.__mro__
        keyvalued = {}
        for cls in classes:
            for key, value in cls.__dict__.iteritems():
                if isinstance(value, property):
                    keyvalued[key] = value.fget(self)
        return keyvalued

    def to_xml(self):
        doc = QtXml.QDomDocument()
        node = doc.createElement(self.typeInfo())
        doc.appendChild(node)

        for i in self._children:
            i._recurseXml(doc, node)

        return doc.toString(indent=4)

    def _recurse_xml(self, doc, parent):
        node = doc.createElement(self.typeInfo())
        parent.appendChild(node)
        attrs = self.attrs().iteritems()

        for k, v in attrs:
            node.setAttribute(k, v)

        for child in self._children:
            child._recurse_xml(doc, node)

    def to_list(self):
        output = []
        if self._children:
            for child in self._children:
                output += [self.name, child.to_list()]
        else:
            output += [self.name, self.value]
        return output

    def to_dict(self, d):
        for child in self._children:
            child._recurse_dict(d)
        return d

    def _recurse_dict(self, d):
        if self._children:
            d[self.name] = {}
            for child in self._children:
                child._recurse_dict(d[self.name])
        else:
            d[self.name] = self.value

    # noinspection PyMethodParameters
    def name():
        def fget(self):
            return self._name

        def fset(self, value):
            self._name = value
        return locals()
    name = property(**name())

    # noinspection PyMethodParameters
    def value():
        def fget(self):
            return self._value

        def fset(self, value):
            self._value = value
        return locals()
    value = property(**value())

    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    # noinspection PyPep8Naming
    def log(self, tabLevel=-1):
        output = ''
        tabLevel += 1

        for i in range(tabLevel):
            output += '    '

        output += ''.join(('|----', self._name, ' = ', '\n'))

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += '\n'
        return output

    def __repr__(self):
        return self.log()

    def data(self, column):
        if column is 0:
            return self.name
        elif column is 1:
            return self.value

    def setData(self, column, value):
        if column is 0:
            self.name = value
        if column is 1:
            self.value = value

    @staticmethod
    def resource():
        return None

