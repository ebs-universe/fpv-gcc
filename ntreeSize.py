"""
Copyright (C) 2015 Quazar Technologies Pvt. Ltd.
              2015 Chintalagiri Shashank

This file is part of fpv-gcc.

fpv-gcc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

fpv-gcc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with fpv-gcc.  If not, see <http://www.gnu.org/licenses/>.
"""


from ntree import NTreeNode, NTree
import warnings


class SizeNTreeNode(NTreeNode):
    def __init__(self, parent=None, node_t=None):
        super(SizeNTreeNode, self).__init__(parent, node_t)
        self._leafsize = None

    @property
    def size(self):
        rval = 0
        if self.is_leaf:
            rval = self.leafsize
        else:
            for child in self.children:
                try:
                    rval += child.size
                except TypeError:
                    warnings.warn("Size information not available for : " + child.gident)
                    return "Err"
        return rval

    @property
    def leafsize(self):
        raise NotImplementedError

    @leafsize.setter
    def leafsize(self, value):
        raise NotImplementedError


class SizeNTree(NTree):
    def __init__(self, node_t=None):
        if node_t is None:
            node_t = SizeNTreeNode
        super(SizeNTree, self).__init__(node_t)

    @property
    def size(self):
        return self.root.size
