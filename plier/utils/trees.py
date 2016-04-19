# -*- coding: utf-8 -*-

import pprint

__all__ = [
        "tree",
        "cst",
        "ast",
        ]


class tree(object):
    """
    A basic tree class.

    Supports data storage as key-value pairs in each node, and hierarchical 
    navigation (i.e., to parent, and to children, but not to siblings).
    """

    def __init__(self, **kwargs):
        """
        Initialize a tree, setting its node data to the supplied key-value 
        pairs.
        """
        object.__init__(self)
        object.__setattr__(self, '_parent', None)
        object.__setattr__(self, '_children', [])
        object.__setattr__(self, '_data', kwargs.copy())  # NOTE shallow copy!
        object.__setattr__(self, '_len', None)


    # attribute access


    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                    "tree instance has no attribute '{}'".format(name))


    def __setattr__(self, name, value):
        if name in ('_parent', '_children', '_data', '_len'):
            raise AttributeError(
                    "A tree's '{}' attribute is read-only.".format(name))
        elif name in ('parent', 'children', 'data'):
            raise AttributeError(
                    "A tree's '{}' property is read-only.".format(name))
        else:  # set an entry in the data table
            self._data[name] = value  # NOTE consistent shallow copy behavior with the initializer


    def __delattr__(self, name):
        if name in ('_parent', '_children', '_data', '_len'):
            raise AttributeError(
                    "A tree's '{}' attribute cannot be deleted.".format(name))
        elif name in ('parent', 'children', 'data'):
            raise AttributeError(
                    "A tree's '{}' property cannot be deleted.".format(name))
        else:  # set an entry in the data table
            self._data.pop(name, None)


    # representations


    def __str__(
            self,
            tab_size=4,
            vertical_char='|',
            connector_2_char='`',
            connector_3_char='|',
            horizontal_char='-'):
        """Visualize the tree."""

        # print own data
        tree_lines = pprint.pformat(self._data) + '\n'

        # attach all child tree
        for i, c in enumerate(self.children):
            sub_tree = c.__str__(
                    tab_size,
                    vertical_char,
                    connector_2_char,
                    connector_3_char,
                    horizontal_char).strip().split('\n')
            if i != len(self.children) - 1:
                connector_char = connector_3_char
                leader_char = vertical_char
            else:
                connector_char = connector_2_char
                leader_char = ' '
            # the first line of the sub-tree connects to the root
            first_line = connector_char + horizontal_char * (tab_size - 1)
            # if this is not the last child, also cotinue a leader line
            subsequent_line = leader_char + ' ' * (tab_size - 1)
            tree_lines += vertical_char + '\n' + first_line + ('\n' + subsequent_line).join(sub_tree) + '\n'
        return tree_lines


    # hierarchy management


    @property
    def parent(self):
        """Parent of the current tree."""
        return self._parent


    @property
    def children(self):
        """All children of a tree."""
        return self._children

    @property
    def data(self):
        return self._data


    def has_ancestor(self, node):
        """Test whether a node is an ancestor or the root of the tree."""
        if self is node:
            return True
        elif self._parent is None:
            return False
        else:
            return self._parent.has_ancestor(node)


    def attach_to(child, parent, position=None):
        """
        Attach to a parent.  The optional position argument specifies the 
        position in the parent's existing children to insert at.

        Returns:
            The parent attached to.  This is useful to chain the tree 
            construction in a bottom-up fashion, i.e.:
                child.attach_to(parent).attach_to(grand_parent)
            And the grand_parent will be returned, which is the root.
        """
        # this is essentially a shorthand function
        # NOTE notice the only difference in return value
        parent.add_child(child, position)
        return parent


    def detach(child):
        """
        Detach from parent.

        Returns:
            The parent detached from.

        Remarks:
            When the node is already detached, the return value would be None.
        """
        p = child._parent
        if p is None:
            return None
        else:
            return p.remove_child(child)


    def add_child(parent, child, position=None):
        """
        Append a child.  Optionally, insert the child at a specific position.

        Returns:
            The child added.
        """
        if child._parent is not None:
            raise ValueError(
                    'The child is still attached to a parent.  '
                    'Detach it first.')
        if parent.has_ancestor(child):  # check towards root for possible cyclic structure
            raise RuntimeError(
                    'Circular reference detected: '
                    'the child is an ancestor of the parent.')
        object.__setattr__(child, '_parent', parent)
        if position is None:
            parent._children.append(child)
        else:
            parent._children.insert(position, child)

        # invalidate all ancestor nodes' length
        p = parent
        while p is not None:
            object.__setattr__(p, '_len', None)
            p = p._parent

        return child


    def append_children(parent, *children):
        """Append multiple children to the parent and return the parent."""
        for c in children:
            parent.add_child(c)


    def remove_child(parent, child=None):
        """
        Remove a child from the tree, and return the removed child.  If no 
        child is specified, pop the last child.

        Returns:
            The removed child.

        Raises:
            IndexError -- when the parent has no children
            LookupError -- when the parent does not contain the child
        """
        if child is None:
            return parent.remove_child_at()
        for i, c in enumerate(parent._children):
            if c is child:
                return parent.remove_child_at(i)
        raise LookupError(
                'The parent does not contain the child')


    def remove_child_at(parent, position=None):
        """
        Remove the child at a specific position, and return the removed child.  
        If no position is specified, pop the last child.

        Returns:
            The removed child.

        Raises:
            IndexError -- when the parent has no children
        """
        if position is None:
            child = parent._children.pop()
        else:
            child = parent._children.pop(position)
        object.__setattr__(child, '_parent', None)

        # invalidate all ancestor nodes' length
        p = parent
        while p is not None:
            object.__setattr__(p, '_len', None)
            p = p._parent

        return child


    # container/iterator interface


    def __len__(self):
        object.__setattr__(
                self,
                '_len',
                self._len or 1 + sum(map(len, self._children)))
        return self._len


    def nodes(self, method='dfs', criteria=lambda x: True):
        """Returns a BFS/DFS iterator based on certain criteria."""
        if method == 'bfs':
            def bfs_iter():
                queue = [self]
                while True:
                    try:
                        n = queue.pop(0)
                    except IndexError:
                        raise StopIteration
                    queue.extend(n._children)
                    if criteria(n):
                        yield n
            return bfs_iter()  # call the generator
        elif method == 'dfs':
            def dfs_iter():
                stack = (self,)
                while True:
                    try:
                        n = stack[0]
                    except IndexError:
                        raise StopIteration
                    # TODO check whether using tuple here is actually faster than list
                    stack = tuple(n._children) + stack[1:]  # prepend
                    if criteria(n):
                        yield n
            return dfs_iter()  # call the generator


    def __contains__(self, item):
        return item.has_ancestor(self)


class cst(tree):
    """
    Concrete Syntax Tree (a.k.a. Parse Tree).

    This implementation and terminologies adhere to the course material at 
    http://www.cse.chalmers.se/edu/course/DAT150/lectures/proglang-02.html
    """


    def __init__(self, value, *rhs):
        """
        Build a CST with the given value (i.e., category) at the root, and 
        child CSTs.

        A CST has a (syntactic) category at the root.  We need to check the 
        right-hand side items to ensure that they are proper CSTs before 
        appending them.  If any of the right-hand side items is not a valid 
        CST, it is *quietly* converted to a CST before proceeding.
        """
        tree.__init__(self)
        self.cst_value = value
        # check rhs items
        for item in rhs:
            if isinstance(item, cst):
                self.add_child(item)
            else:
                self.add_child(cst(item))


    @property
    def is_terminal(self):
        """Whether a node is terminal."""
        for c in self.children:
            return False
        return True


    @property
    def category(self):
        """
        Category of the CST.  None if self is a leaf, in which case the 
        ``token`` property should be used.
        """
        return None if self.is_terminal else self.cst_value


    @property
    def token(self):
        """
        Terminal token of the CST leaf.  None if self is not a leaf, in which 
        case the ``category`` property should be used.
        """
        return self.cst_value if self.is_terminal else None


class ast(tree):
    """Abstract Syntax Tree"""
    pass
