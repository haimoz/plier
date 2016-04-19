"""
Lex/yacc independent utilities to be used in the use of the `ply` package.
"""
import re

__all__ = [
        "re_wrap",
        "re_space_out",
        "re_or",
        ]


## regular expressions utilities ##############################################


def re_wrap(p):
    """
    Wrap a regular expression if necessary, i.e., if it contains unescaped '|' 
    in the outermost level.
    """
    escaped = False
    level = 0
    for c in p:
        if c == '\\':
            escaped = not escaped
        elif c == '(' and not escaped:
            level += 1
        elif c == ')' and not escaped:
            level -= 1
        elif c == '|' and not escaped:
            if level == 0:  # outmost level, must wrap
                p = '(' + p + ')'
                break
        else:
            escaped = False
    return p


def re_space_out(t):
    r"""
    Given an input string, return a regular expression that matches any 
    sequence of the characters in the input text, separated by arbitrary 
    number of white spaces in between, e.g.:

    r'\foo' ==> r'\s*\\\s*f\s*o\s*o\s*'
    which would match:
    r'  \  fo  o  '

    'a\tb' ==> '\\s*a\\s*\t\\s*b\\s*'
    which would match:
    ' \t\n  a\r\t\v b  \n '

    """
    return r'\s*'.join([''] + list(t) + [''])


def re_or(*args):
    """Return a regular expression that matches any one of the multiple 
    patterns, in the order they are provided as arguments."""
    return '|'.join(map(re_wrap, args))
