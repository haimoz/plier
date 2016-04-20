from ..utils.trees import cst
from ..utils.func import universal_decorator
from inspect import getargspec
from functools import wraps, partial  # this is really cool!
import warnings
import re
import ply.yacc as ply_yacc

__all__ = [
        "WITH_CST",
        "ExcessGroupingWarning",
        ]


# parser-related utilities ####################################################
## parsing exceptions and warnings ############################################

## TODO: Build a CST parser from a single string of rules #####################
_rule_separator_regex = re.compile(r'\n\s*(?=[a-zA-Z0-9])')
_category_separator_regex = re.compile(r'\s*:\s*')
_rhs_separator_regex = re.compile(r'\s*\|\s*')
## End of TODO ################################################################


class _attributable_object(object):
    """
    Just a class that supports arbitrary setting of attributes.
    """
    pass


def _create_plier_object(x):
    """
    From an object assumed by `ply`, create an object mocking it's behavior, 
    with an added attribute of `plier_data`.
    """


    class _plier_object(type(x)):
        """
        An object emulating an element of the argument in an `ply.yacc` action 
        function.  It is transparent to the client program, while supporting 
        additional attributes specific to `plier`.

        When getting an object's attribute, the lookup is in the following 
        order:

          1. If the attribute name is exactly 'plier_data', then an internal 
             plier-specific object is returned, which could be attached with 
             attributes for plier-specific operations.

          2. If the attribute name is exactly '_data', then the underlying 
             object is returned.

          3. The underlying object is looked up for the attribute.

        When the client program sets an attribute, the attribute will be set 
        on the underlying object.  If it fails, nothing will be set, as the 
        client program is not allowed to manipulate data specific to `plier`.

        This class has to inherit from the class of the underlying object, and 
        implement object containment at the same time, because:

          1. The underlying object's data should be visible to the client 
             program at the instance-level (thus the object containment).

          2. Some behaviors such as operator overloading are looked up at 
             class-level, instead of instance-level (thus the class inheritance).
        """


        def __init__(self, data):
            object.__setattr__(self, '_data', data)  # the underlying object
            object.__setattr__(self, 'plier_data', _attributable_object())  # the plier-specific data dictionary


        def __getattribute__(self, name):
            if name == 'plier_data':
                return object.__getattribute__(self, 'plier_data')
            elif name == '_data':
                return object.__getattribute__(self, '_data')
            else:
                return getattr(object.__getattribute__(self, '_data'), name)


        def __setattr__(self, name, value):
            # set attribute on the underlying object
            self._data.__class__.__setattr__(self._data, name, value)

    return _plier_object(x)


#class _plier_list(object):
#    """
#    An object compatible with and transparent to the argument to an `yacc.py` 
#    action function.
#    """
#
#
#    def __init__(self, p):
#        self.p = p
#
#
#    def __getitem__(self, n):
#        if isinstance(n, slice):
#            return [getattr(x, 'ast', None) or x for x in self.p[n]]
#        else:
#            v = self.p[n]
#            return getattr(v, 'ast', None) or v
#
#
#    def __setitem__(self, n, v):
#        self.p[n].ast = v
#
#
#    def __getslice__(self, i, j):
#        return [getattr(x, 'ast', None) or x for x in self.p[i:j]]


@universal_decorator
def WITH_CST(f):
    """
    Transforms an input function into a CST builder based on its docstring 
    following the `ply` spec.  The decorated function will be used as the 
    constructor from CST to AST, which is executed on the AST managed by the 
    client program.

    NOTE:
    If not all actions (functions with 'p_' prefix as required by `ply`) are 
    decorated as 'CST_BUILDER', then the CST construction chain would be 
    broken.  In this case, the nodes with missing CST will be treated as 
    terminals, and be used directly in CST construction.  No warnings will be 
    given in this case.
    """
    @wraps(f)
    def g(p):
        # Construct the CST before the client program could potentially 
        # reassign the `plier.cst` attribute value.
        the_cst = cst(
                p.slice[0].type,
                *[getattr(getattr(x, 'plier_data', None), 'cst', None) or x for x in p[1:]])
        # run the client program's logic
        retval = f(p)  # record the return value of the decorated function, if any
        # attach the CST to p[0]
        p[0] = _create_plier_object(p[0])
        p[0].plier_data.cst = the_cst
        return retval  # return the return value of the decorated function, if any
    # Default behavior of `functools.wraps` already replicate the docstring, 
    # so we do not need to do it explicitly.
    return g


# Excess grouping often require context to detect.  Therefore, it makes more 
# sense to define it as a parsing utility instead of as a lexing utility.
class ExcessGroupingWarning(SyntaxWarning):
    COMMON_DELIM = '{}()[]<>'
    def __init__(self, t):
        if t.value[0] not in COMMON_DELIM:
            #resetLexer(t.lexer)
            warnings.warn(SyntaxWarning(
                    'When warning about excess grouping, '
                    'no commonly accepted group delimiter is found '
                    'as the first character of the token value.\n'
                    'Common delimiters: {}\n'
                    'Warned token: {}\n'
                    'Context:{}'.format(
                        COMMON_DELIM,
                        t,
                        context(t))))
        else:
            self.token = t

    def __str__(self):
        return (
                'Excess group delimiter \'{}\' found at {}:{} of the input.\n'
                'Context:'
                '{}'
                'Consider removing this delimiter, '
                'as it does not affect parsing.'.format(
                    self.token.value[0],
                    self.token.lineno,
                    find_column(self.token),
                    context(self.token)))


###############################################################################
## A parser that can bind/unbind with lexer without parsing, in addition to 
## the `ply.yacc.LRParser` behaviors.


class LRParser():
    """
    A parser class that wraps the `ply.yacc.LRParser` class.

    The added features of this class include:

      1. Ability to bind/unbind with a lexer without doing the actual parsing.
         This is useful to create an anonymous lexer that is bound with the 
         parser; and that later the `parse` method would not need to be called 
         with a lexer.

    There is no point using this class directly without a configured 
    `ply.yacc.LRParser` object, since the `ply.yacc.LRParser` class's 
    initializer would return a partially configured parser, which is only 
    fully configured by the `ply.yacc.yacc` function.  Therefore, this class's 
    initializer requires a `ply.yacc.LRParser` object to implement object 
    containment, rather than class inheritance.

    The `plier` version of the `ply.yacc.yacc` function returns a fully 
    configured `plier.framework.yacc.LRParser` object, as done similarly in 
    `ply.yacc.yacc`.
    """


    def __init__(self, ply_parser, lexer=None):
        """
        Wrap a `ply.yacc.LRParser` object.
        """
        self._ply_parser = ply_parser
        if lexer is not None:
            self.bind_lexer(lexer)


    def __getattr__(self, name):
        return getattr(self._ply_parser, name)


    def bind_lexer(self, l):
        """
        Bind a lexer to the parser.

        Bind a lexer to the parser, so that when no lexer is provided when 
        calling the `parse` method on the parser, the bound lexer is used.
        """
        if l is not None:
            # This would shadow and partially bind the actual parser's parse 
            # method with the provided lexer.
            self.__setattr__('parse', partial(self._ply_parser.parse, lexer=l))
        else:
            # This would reveal and unbind the actual parser's parse method.
            try:
                self.__delattr__('parse')
            except AttributeError:
                pass
        return self


###############################################################################
## Similar to `ply.yacc.yacc`, this returns a `plier.framework.yacc.LRParser` 
## instead of `ply.yacc.LRParser`.


def yacc(*args, **kwargs):
    """
    Returns a `plier.framework.yacc.LRParser` object instead of a 
    `ply.yacc.LRParser`.
    """
    p = ply_yacc.yacc(*args, **kwargs)
    return LRParser(p)
