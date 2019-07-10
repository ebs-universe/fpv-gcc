
# Copyright (C) 2015 Quazar Technologies Pvt. Ltd.
#               2015 Chintalagiri Shashank
#
# This file is part of fpv-gcc.
#
# fpv-gcc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fpv-gcc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fpv-gcc.  If not, see <http://www.gnu.org/licenses/>.


import logging
from os.path import commonprefix


class NTreeNode(object):
    _leaf_property = None
    _ident_property = None

    def __init__(self, parent=None, node_t=None):
        self.parent = parent
        if node_t is None:
            if self.parent is not None:
                node_t = self.parent.node_t
            else:
                node_t = NTreeNode
        self.node_t = node_t
        self.children = []

    @property
    def tree(self):
        if isinstance(self.parent, NTree):
            return self.parent
        else:
            return self.parent.tree

    @property
    def is_root(self):
        if isinstance(self.parent, NTree):
            return True
        else:
            return False

    @property
    def is_toplevelnode(self):
        if self.is_root:
            return False
        if isinstance(self.parent.parent, NTree):
            return True
        return False

    @property
    def is_leaf(self):
        if len(self.children) > 0:
            return False
        else:
            return True

    def add_child(self, newchild=None):
        if newchild is None:
            newchild = self.node_t(parent=self, node_t=self.node_t)
        try:
            for child in self.children:
                if child.ident == newchild.ident:
                    raise ValueError("Child with that identifier already "
                                     "exists: {0}".format(newchild.ident))
        except NotImplementedError:
            pass
        if len(self.children) == 0:
            try:
                if self._is_leaf_property_set is True:
                    logging.warning(
                        "Adding children to node which has leaf specific "
                        "information set : {0}".format(self.gident)
                    )
            except NotImplementedError:
                pass
        newchild.parent = self
        self.children.append(newchild)
        return newchild

    @property
    def _is_leaf_property_set(self):
        if self._leaf_property is None:
            raise NotImplementedError
        if getattr(self, self._leaf_property) is not None:
            return True
        return False

    @property
    def _is_ident_property_set(self):
        if not self._ident_property:
            raise NotImplementedError
        if not getattr(self, self._ident_property, None):
            return True
        return False

    @property
    def idx(self):
        if self.parent is None:
            return 'Root'
        else:
            return self.parent.children.index(self)

    @property
    def ident(self):
        if self._ident_property:
            return getattr(self, self._ident_property, '')
        else:
            return str(self.idx)

    @ident.setter
    def ident(self, value):
        if self._ident_property:
            setattr(self, self._ident_property, value)

    @property
    def has_ident(self):
        return self._ident_property is not None

    @property
    def gident(self):
        rval = self.ident
        walker = self
        while not isinstance(walker.parent, NTree):
            walker = walker.parent
            rval = walker.ident + '.' + rval
        return rval

    def get_child_by_ident(self, ident):
        for child in self.children:
            if child.ident == ident:
                return child
        raise ValueError

    def get_child_disambig(self, ident, prospective=False):
        disambig = None
        for child in self.children:
            if ':' in child.ident:
                name, d = child.ident.split(':')
                if name == ident:
                    disambig = disambig or 0
                    disambig = max(disambig, int(d))
            elif prospective and child.ident == ident:
                # print("Recommending disambig for {0};{1}".format(self.gident, ident))
                disambig = disambig or 0
        return disambig

    def get_descendent_by_ident(self, ident):
        res = self.get_child_by_ident(ident)
        if res is not None:
            return res
        for child in self.children:
            if child.is_leaf is False:
                res = child.get_descendent_by_ident(ident)
                if res is not None:
                    return res
        return ValueError

    def all_nodes(self):
        yield self
        for child in self.children:
            for node in child.all_nodes():
                yield node

    @property
    def get_top_level_ancestor(self):
        walker = self
        if walker.is_root:
            return None
        while not walker.is_toplevelnode:
            walker = walker.parent
        return walker


class NTree(object):
    node_t = NTreeNode

    def __init__(self):
        self.root = self.node_t(parent=self, node_t=self.node_t)

    @property
    def top_level_nodes(self):
        return self.root.children

    @property
    def top_level_idents(self):
        if self.root.has_ident:
            return [x.ident for x in self.top_level_nodes]
        else:
            raise AttributeError

    @property
    def top_level_gidents(self):
        return [x.gident for x in self.top_level_nodes]

    def get_node_disambig(self, gident, prospective=False):
        crumbs = gident.split('.')
        if crumbs[0] != self.root.ident:
            raise ValueError
        walker = self.root
        for crumb in crumbs[1:-1]:
            if walker.get_child_disambig(crumb) is None:
                walker = walker.get_child_by_ident(crumb)
            else:
                raise ValueError('Deep disambig found at intermediate node : '
                                 '{0}'.format(crumbs))
        return walker.get_child_disambig(crumbs[-1], prospective)

    def get_node(self, gident, create=False):
        crumbs = gident.split('.')
        if crumbs[0] != self.root.ident:
            raise ValueError
        walker = self.root
        for crumb in crumbs[1:]:
            try:
                walker = walker.get_child_by_ident(crumb)
            except ValueError:
                if create:
                    # print "Creating Node : " + crumb
                    newnode = walker.add_child()
                    if newnode.has_ident:
                        newnode.ident = crumb
                    else:
                        raise ValueError
                    walker = walker.get_child_by_ident(crumb)
                else:
                    raise ValueError
        return walker

    def get_least_common_ancestor(self, nodes):
        t = commonprefix([node.gident for node in nodes])
        k = t.rfind('.')
        return self.get_node(t[:k])
