"""
The `plier` package enhances the `ply` package, with various tools to 
facilitate compiler development, including:

    1. Conveniently define and modify behaviors of Lex token rules.

    2. Automatically construct concrete syntax tree (CST) from the grammar.

    3. [TODO] Define linearizers associated to the concrete grammar rules or 
       abstract grammar symbols.

    4. [TODO] Facilitate reuse of grammar rules and dynamic binding between 
       rules and actions in different parsers

    5. [TODO] Create lexers and parsers from a subset of the declared tokens 
       and grammars.

    6. Various features, including:
        - Printing the context of a token
        - Warnings and exceptions specific for the lexing/parsing process
        - Printing the CST/AST
        - A Lexer class that forwards the context of the token to the parser.
          (`ply` would only pass the value of the token.)

Remarks:

    In `ply`, the functions defined with 'p_' prefix are essentially the 
    constructors for building abstract syntax trees (AST).  Therefore, we do 
    not need to explicitly support AST.  Linearizers need to be supported 
    as the inverse operation of AST constructors, so that we could build 
    cross-compilers between multiple languages.
"""

from . import framework, utils

__all__ = ["framework", "utils"]
