"""
Utilities for handling token/rule functions in `ply`.
"""
import ply.lex
from inspect import getargspec
from functools import wraps, partial  # this is really cool!

__all__ = [
        "checked_decorator",
        "universal_decorator",
        ]


def checked_decorator(g):
    """
    Given a decorator, return the same decorator which checks whether the 
    decorated object is indeed callable.
    """
    if hasattr(g, '__call__'):
        def h(f):
            if hasattr(f, '__call__'):
                return g(f)
            else:
                raise TypeError("The decorated object is not callable.")
        return h
    else:
        raise TypeError("The decorated object is not callable.")


@checked_decorator
def universal_decorator(g):
    """
    Given a decorator that decorates a single-argument function, return a 
    decorator that decorates functions with either one or two arguments.

    For token/rule functions, `ply` would check the number of their arguments, 
    and variable-length arguments are not allowed in `ply`.  As a result, when 
    decorating token/rule functions, we need to return functions with explicit 
    number of arguments, i.e., f(self, t) or f(t)

    This function simplifies this process, taking a decorator g, and returns 
    a decorator that can decorate f(self, t) and f(t).

    Argument:
        g: A decorator that decorates a single-argument bound function.

    Returns:
        A decorator that decorates f(self, t) and f(t) respectively by the 
        input function, g.

    Note:
        A universal decorator is checked (i.e., raising an exception if the 
        decorated object is not callable).  See documentation of 
        `checked_decorator` for details.

    Example:

        The decorator:
        >>> def verbose_token(prompt):
        ...     def g(f):
        ...         @functools.wraps(f)
        ...         def h(t):
        ...             print prompt,
        ...             print getattr(f, 'regex', f.__doc__)
        ...             return f(t)
        ...         h = ply.TOKEN(f)(h)
        ...         return h
        ...     return g

        In a module:
        >>> @universal_decorator(verbose_token(prompt=':::'))
        ... def t_PLUS(t):
        ...     r'+'
        ...     ...

        In a class:
        >>> class Foo():
        ...
        ...     ...
        ...
        ...     @universal_decorator(verbose_token(prompt=':::'))
        ...     def t_PLUS(self, t):
        ...         r'+'
        ...         ...
        ...
        ...     ...
        ...

        At runtime, both of the above decorated functions would produce 
        verbose output defined in the `verbose_token` decorator.
    """
    @checked_decorator
    def h(f):
        nargs = len(getargspec(f).args)
        if nargs == 1:
            # One argument, which suggests that the method is already bound at 
            # declaration time.  Therefore, we can directly return the 
            # decorated function.
            w = wraps(f)(g(f))  # ensure docstring propagation for parser rules
        elif nargs == 2:
            # Two arguments, which suggests that the method is not bound at 
            # declaration time.  Therefore, we can only decorate the function 
            # at runtime.
            @wraps(f)  # ensure docstring propagation for parser rules
            def w(self, v):
                # Bind, decorate, then invoke.
                # All three steps happen at runtime, as the function g will 
                # not decorate an unbound function.
                return g(wraps(f)(partial(f, self)))(v)  # ensure docstring propagation for parser rules
        else:
            raise TypeError(
                    "Unable to decorate functions with {} arguments,"
                    "as `ply` only allows 1 or 2 explicit arguments."
                    .format(nargs))
        # Pass the token/rule pattern.
        # NOTE
        # The `ply.lex.TOKEN` decorator will only set the `regex` attribute of 
        # the decorated function, instead of directly setting its docstring.
        # This will work for decorating tokenization functions, but would fail 
        # for parsing functions, which rely directly on the docstring, not the 
        # `regex` attribute.
        # Therefore, the statement here only ensures propagation of the 
        # patterns for tokenization rules while being decorated.  To ensure 
        # propagation of the grammar rules for parser action functions, see 
        # the `wraps` decorators in the above if-else clauses.
        w = ply.lex.TOKEN(f)(w)
        return w
    return h
