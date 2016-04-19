#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys

# run as a script and import the plier package
if __name__ == '__main__':
    # adjust the path
    REPO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, REPO_BASE)
else:
    raise Exception(
            "The plier example '{}' is meant to be run as a script, "
            "not used as a module.".format(__name__))

from plier.framework.lex import as_function, as_non_standard, lex
from plier.framework.yacc import yacc, WITH_CST
from plier.framework import start_console


class ArithmeticsGrammar(object):
    tokens = (
            'NUMBER',
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
            'LPAREN', 'RPAREN',
            'LPAREN_NONSTD', 'RPAREN_NONSTD',
            )

    t_PLUS    = as_function(r'\+', is_class_method=True)
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'
    t_LPAREN  = r'\('
    t_LPAREN_NONSTD = as_non_standard('(')(as_function(r'\{', is_class_method=True))
    t_RPAREN  = r'\)'
    t_RPAREN_NONSTD = as_non_standard(')')(as_function(r'\}', is_class_method=True))

    def t_NUMBER(self, t):
        r'(0|[1-9][0-9]*)(?![0-9])'
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    # Ignored characters
    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")


    # parsing grammar


    precedence = (
            ('left','PLUS','MINUS'),
            ('left','TIMES','DIVIDE'),
            )

    @WITH_CST
    def p_expression_plus(self, p):
        'expression : expression PLUS term'
        p[0] = p[1] + p[3]

    @WITH_CST
    def p_expression_minus(self, p):
        'expression : expression MINUS term'
        p[0] = p[1] - p[3]

    @WITH_CST
    def p_expression_term(self, p):
        'expression : term'
        p[0] = p[1]

    @WITH_CST
    def p_term_times(self, p):
        'term : term TIMES factor'
        p[0] = p[1] * p[3]

    @WITH_CST
    def p_term_div(self, p):
        'term : term DIVIDE factor'
        p[0] = p[1] / p[3]

    @WITH_CST
    def p_term_factor(self, p):
        'term : factor'
        p[0] = p[1]

    @WITH_CST
    def p_factor_num(self, p):
        'factor : NUMBER'
        p[0] = p[1]

    @WITH_CST
    def p_factor_expr(self, p):
        'factor : LPAREN expression RPAREN'
        p[0] = p[2]

    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error in input!")


grammar = ArithmeticsGrammar()

# Build the lexer
lexer = lex(module=grammar)
#start_console(lexer)

# Build the parser
parser = yacc(module=grammar)
start_console(parser)
