#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    import warnings
    warnings.warn("`setuptools` not found, using `distutils` instead.")
    from distutils.core import setup  # this is just as a fallback

setup(
        name='plier',
        version='0.1.0',
        description='Utilities for PLY (Python Lex & Yacc)',
        long_description="""
The "plier" package provides various utilities for use with the 
`PLY (Python Lex & Yacc) <http://www.dabeaz.com/ply/>`_ package.
""",
        license='MIT',
        author='Haimo Zhang',
        author_email='zh.hammer.dev@gmail.com',
        url='https://github.com/haimoz/plier',
        requires=['ply(>=3.8)',],
        install_requires=['ply>=3.8',],
        packages=['plier', 'plier.framework', 'plier.utils'],
        classifiers=[
                'Development Status :: 3 - Alpha',
                'Intended Audience :: Developers',
                'Intended Audience :: Science/Research',
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python :: 2 :: Only',
                'Topic :: Software Development :: Build Tools',
                'Topic :: Software Development :: Code Generators',
                'Topic :: Software Development :: Compilers',
                'Topic :: Software Development :: Interpreters',
                'Topic :: Software Development :: Pre-processors',
                'Topic :: Utilities',
                ],
        )
