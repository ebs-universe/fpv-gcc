"""
This file is part of fpv-gcc
See the COPYING, README, and INSTALL files for more information
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
