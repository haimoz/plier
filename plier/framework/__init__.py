"""
Framework-specific classes/functions/objects that rely on the `ply` framework.
"""
from . import lex, yacc
import traceback

__all__ = [
        "lex",
        "yacc",
        "start_console",
        ]


def _check_lexer_interface(x):
    if not hasattr(x, 'token'):
        return False
    if not hasattr(x.token, '__call__'):
        return False
    if not hasattr(x, 'input'):
        return False
    if not hasattr(x.input, '__call__'):
        return False
    return True


def _check_parser_interface(x):
    return hasattr(x, 'parse') and hasattr(x.parse, '__call__')


def _lexer_process(lexer, text):
    ret = []
    lexer.input(text)
    while True:
        t = lexer.token()
        if t is None:
            return ret
        # *MUST* print and append the tokens in a loop, 
        # so that output is in sync with the processing of input.
        # This is a requirement for console responsiveness
        print t
        ret.append(t)


def _parser_process(parser, *args, **kwargs):
    # NOTE
    # Interestingly, if the parser is a plier LRParser already bound to a 
    # lexer, calling the parse method with another lexer would quietly 
    # override the existing binding.
    ret = parser.parse(*args, **kwargs)
    print ret
    return ret


def start_console(lp, prompt=None, is_lexer=None):
    """
    Interactive console for tokenizing/parsing.

    Given a lexer/parser, start an interactive console to print debug 
    information while tokenizing/parsing the input.  Return the last 
    tokenized/parsed result when the console is exited by EOF (<Ctrl-d> on a 
    blank line for UNIX-like systems, and <Ctrl-z> for Windows).

    If the 'is_lexer' argument is True, the first argument is treated as a 
    lexer; if it is False, then the first argument is treated as a parser.  In 
    both cases, the object is checked for the minimal interface to satisfy the 
    use as lexer/parser.

    For an object to be a parser, it must have a callable attribute 'parse'; 
    for it to be a lexer, it must have a callable attribute 'input', and a 
    callable attribute 'token'.  This is based on the minimal interface used 
    by `ply.yacc`, as documented in:
    http://www.dabeaz.com/ply/ply.html
    Section '4.20 Miscellaneous Issues'

    If 'is_lexer' is None, then the use of the first argument is automatically 
    determined.  It is first checked for the minimal parser interface.  If it 
    does not satisfy the minimal parser interface, it is then checked for the 
    minimal lexer interface.  If both checks failed, an exception is raised.
    """
    if is_lexer is None:
        if _check_parser_interface(lp):
            is_lexer = False
        elif _check_lexer_interface(lp):
            is_lexer = True
        else:
            # neither minimal interfaces are satisfied
            raise Exception(
                    "Neither of the minimal interfaces for parser nor lexer "
                    "could be satisfied by the first argument.")
    elif is_lexer is False:
        if not _check_parser_interface(lp):
            raise Exception(
                    "The first argument does not satisfy "
                    "the minimal interface for parser.")
    elif is_lexer is True:
        if not _check_lexer_interface(lp):
            raise Exception(
                    "The first argument does not satisfy "
                    "the minimal interface for lexer.")
    else:
        raise Exception(
                "The value of 'is_lexer', {}, is not recognized.  "
                "Use True, False, or None to treat the object as "
                "lexer, parser, or automatically determined.".format(is_lexer))
    process = _lexer_process if is_lexer else _parser_process
    prompt = prompt or ('LEX > ' if is_lexer else 'PARSE > ')

    ret = None
    while True:
        try:
            s = raw_input(prompt)
        except EOFError as eof:
            return ret
        try:
            ret = process(lp, s)
        except Exception as e:
            traceback.print_exc()
            print e
            ret = None
            continue
