"""
Various features depending on the `ply.lex` module.

They mostly support the definition of lexers.
"""
# all our internally defined decorators are checked and universal
from ..utils.func import universal_decorator
import ply.lex as ply_lex
import warnings

__all__ = [
        "context",
        "find_column",
        "as_function",
        "as_non_standard",
        "NonStandardTokenWarning",
        "Lexer",
        "lex",
        ]


## context tracking ###########################################################

# NOTE:
# The newline characters used in these two following functions are fixed to be 
# '\n', which should be changed in future versions
# One recommendation is to use the pattern used for `t_newline` function in 
# `ply`.


def context(token, position=None, length=None, margin=(None, None)):
    """
    Get the context of a token or a specific position in its input.

    Arguments:
        token:
            The token to show context for.
        position:
            A custom position that marks the beginning of the target text.
            Defaults to the starting position of the token.
        length:
            Length of the target text.  Defaults to the length of the token 
            value if the position of `left' is not specified; and 1 otherwise.
        margin:
            Left/right margins from the target text's left/right boundary.
            Defaults to (None, None), which would extend the margin to the 
            entire line of input.

    Returns:
        A string formated with the context of the target text and an 
        additional line under it to highlight the target text.

    Example:

        A quick brown foox jumps over a lazy dog.
        --------------^^^^-----------------------

        A quick brown fo
        --------------^^
        ox jumps over a lazy dog.
        ^^-----------------------
    """
    length = length or (1 if position else len(token.value))
    position = position or token.lexpos
    start = token.lexer.lexdata.rfind('\n', 0, position) + 1  # closest newline character to the left of the token of interest
    if margin[0] is not None:
        start = max(start, position - margin[0])
    end = token.lexer.lexdata.find('\n', position + length)  # closest newline character to the right of the token of interest
    if margin[1] is not None:
        if end == -1:
            end = min(len(token.lexer.lexdata), position + length + margin[1])
        else:
            end = min(end, position + length + margin[1])
    else:
        if end == -1:
            end = len(token.lexer.lexdata)
    context = token.lexer.lexdata[start : end]
    underline = '-' * (position - start) + '^' * length + '-' * (end - position - length)
    for i,c in enumerate(context):
        if c == '\n':
            underline[i] = c
    return '\n' + '\n'.join([
            '\n'.join(l) for l in
            zip(context.split('\n'), underline.split('\n'))]) + '\n'


# compute column number
def find_column(t, pos=None):
    """
    Find the column of the token or a specific position in the token's data.

    Argument:
        t   - the token
        pos - an optional number indicating the position in the input data, if 
              not using the token's starting position
    """
    position = pos or t.lexpos  # position of the character in the input stream, default to the token's position
    last_cr = t.lexer.lexdata.rfind('\n', 0, position)
    if last_cr < 0:
        last_cr = 0
    column = (position - last_cr) + 1
    return column


## useful decorators in defining tokens #######################################


def as_function(p, is_class_method=False):
    """
    Transform a token pattern string into a function.

    The use of this function is to be able to explicitly control the 
    precedence of token resolution.  When a string is transformed into a 
    function, there is no added functionality, and a simple pass-through 
    function is returned.  If the input is a callable object already, then 
    the function does nothing and returns this callable object.

    Arguments:

        p:
            the pattern string

        is_class_method:
            whether the returned function should match a class method's 
            signature, i.e., f(self, t)

    Returns:

        `lambda self, p: p` if `is_class_method` is True.
        `lambda p: p` if `is_class_method` is False.

    NOTE:

    1.

    `ply` uses `__code__.co_firstlineno` to order the precedence of the tokens.  As 
    a result, all functions decorated by a same decorator would point to a 
    same line, resulting in undefined order of token resolution.  I (Haimo) 
    will try to fix this in the `ply` project, possibly by disassembling the 
    scope and use the last line the variable is bound.  Util that happens, 
    these decorators will interfere the resolution of tokens having same 
    prefices.

    2.

    There is no restrictions on where this function is called.  Therefore, 
    there is no way to decide whether the returned function will be used as 
    class method, class static method, or functions.  As a result, we need to 
    explicitly specifiy how the returned function will be used in `ply`.
    """
    if is_class_method:
        f = lambda self, p: p
    else:
        f = lambda p: p
    return ply_lex.TOKEN(p)(f)  # use the token decorator to properly set the rule pattern


def as_non_standard(standard_form):
    r"""
    Mark a token as non-standard.
    The `standard_form` argument can either be a string, or a function that 
    maps from the captured non-standard tokens to their standard-form strings.

    Examples are Greek letters in LaTeX that are the same as Latin letters 
    such as '\Alpha', and non-standard trigonometric functions such as 
    '\arccot', which should be '\operatorname{arccot}'.
    """
    @universal_decorator  # a universal decorator is checked
    def _decor(f):
        def g(t):
            t = f(t)
            try:
                e = NonStandardTokenWarning(t, standard_form(t))
            except TypeError:
                # The `standard_form` is not callable.  Treat as string.
                e = NonStandardTokenWarning(t, standard_form)
            warnings.warn(e)
            return t
        return ply_lex.TOKEN(f)(g)
    return _decor


## lexing exceptions and warnings #############################################


class NonStandardTokenWarning(SyntaxWarning):
    def __init__(self, t, std):
        self.token = t
        self.standard_form = std

    def __str__(self):
        return (
                '{}:{} - Non-standard token "{}" found for token type "{}"\n'
                'Use "{}" instead.\n'
                'Context:{}'.format(
                    self.token.lineno,
                    find_column(self.token),
                    self.token.value,
                    self.token.type,
                    self.standard_form,
                    context(self.token)))


###############################################################################
## A lexer that writes the token attributes to the token's value, so that the 
## lexing information is carried forward to the parsing stage.  This is useful 
## in printing context information from the parser.


class Lexer():
    """
    A lexer class that wraps the `ply.lex.Lexer` class.

    The added features include:

      1. Writes the token attributes to the token's value, so that the lexing 
         information is carried forward to the parsing stage.  This is useful 
         in printing context information from the parser.

    There is no point using this class directly without a configured 
    `ply.lex.Lexer` object, since the `ply.lex.Lexer` class's initializer 
    would return a partially configured lexer, which is only fully configured 
    by the `ply.lex.lex` function.  Therefore, this class's initializer 
    requires a `ply.lex.Lexer` object to implement object containment, rather 
    than class inheritance.

    The `plier` verion of the `ply.lex.lex` function returns a fully 
    configured `plier.framework.lex.Lexer` object, as done similarly in 
    `ply.lex.lex`.
    """


    def __init__(self, ply_lexer):
        """
        Wrap a `ply.lex.Lexer` object, so that the token meta data would be 
        visible to the parser.
        """
        self._ply_lexer = ply_lexer


    def __getattr__(self, name):
        return getattr(self._ply_lexer, name)


    def token(self):
        t = self._ply_lexer.token()
        if t is None:
            return t
        d = {}
        d.update(t.__dict__)
        t.value = d
        return t


###############################################################################
## Similar to `ply.lex.lex`, this returns a `plier.framework.lex.Lexer` 
## instead of `ply.lex.Lexer`.


def lex(*args, **kwargs):
    """
    Returns a `plier.framework.lex.Lexer` object instead of a `ply.lex.Lexer`.
    """
    l = ply_lex.lex(*args, **kwargs)
    return Lexer(l)
