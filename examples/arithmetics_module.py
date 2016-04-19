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


tokens = (
        'NUMBER',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
        'LPAREN', 'RPAREN',
        'LPAREN_NONSTD', 'RPAREN_NONSTD',
        )

t_PLUS    = as_function(r'\+')
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_LPAREN_NONSTD = as_non_standard('(')(as_function(r'\{'))
t_RPAREN  = r'\)'
t_RPAREN_NONSTD = as_non_standard(')')(as_function(r'\}'))

def t_NUMBER(t):
    r'(0|[1-9][0-9]*)(?![0-9])'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

# Build the lexer
lexer = lex(module=sys.modules[__name__])
#start_console(lexer)


# parsing grammar


precedence = (
        ('left','PLUS','MINUS'),
        ('left','TIMES','DIVIDE'),
        )

@WITH_CST
def p_expression_plus(p):
    'expression : expression PLUS term'
    p[0] = p[1] + p[3]

@WITH_CST
def p_expression_minus(p):
    'expression : expression MINUS term'
    p[0] = p[1] - p[3]

@WITH_CST
def p_expression_term(p):
    'expression : term'
    p[0] = p[1]

@WITH_CST
def p_term_times(p):
    'term : term TIMES factor'
    p[0] = p[1] * p[3]

@WITH_CST
def p_term_div(p):
    'term : term DIVIDE factor'
    p[0] = p[1] / p[3]

@WITH_CST
def p_term_factor(p):
    'term : factor'
    p[0] = p[1]

@WITH_CST
def p_factor_num(p):
    'factor : NUMBER'
    p[0] = p[1]

@WITH_CST
def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc(module=sys.modules[__name__])
start_console(parser)
