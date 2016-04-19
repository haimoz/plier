#registry for mapping between rules and actions

"""
A registry for keeping the mapping between grammar rules and actions for 
various modes of parsing.

For example, a parser in symbolic construction mode would defer any 
evaluation, whereas a parser in evaluation mode would immediately evaluate any 
input, while both parsers use a same set of grammar rules.

The point of the registry module is to encourage reusability of the grammar 
rules.
"""

# a rule-action registry is first indexed by the declared method names, then by its mode.
_registry = {}
_all_modes = set()  # a set of subscribed modes
_current_mode = 'default'


def DECLARE(f):
    """Declare the name of a function to the registry."""
    global _registry
    global _current_mode
    fname = f.__name__
    if _registry.has_key(fname):
        raise Exception(
                'The function named \'{}\' '
                'is already registered '
                'with the rule-action registry.'.format(fname))
    else:
        _registry[fname] = { 'default': [] }
    def g(p):
        f(p)
        for func in _registry[fname].get(_current_mode, []):
            func(p)
    g.__doc__ = f.__doc__  # copy over the docstring containing the parsing rules
    return g


def SUBSCRIBE(names, modes=tuple(['default'])):
    """Subscribe an action to the specified grammar rule function, with 
    optional modes."""
    global _registry
    global _all_modes
    # check whether the names of the rules are already registered
    slots = map(lambda x: _registry.get(x), names)
    for i, name in enumerate(names):
        if slots[i] is None:
            raise Exception(
                    'The function \'{}\' '
                    'is not yet registered as a rule.'.format(name))
    for slot in slots:
        for mode in modes:
            if not slot.has_key(mode):
                slot[mode] = []
    _all_modes = _all_modes.union(set(modes))
    def subscriber(f):
        for slot in slots:
            for mode in modes:
                slot[mode].append(f)
        return f
    return subscriber


def set_mode(mode):
    """Set the mode for a parser."""
    global _current_mode
    if mode not in _all_modes:
        raise Exception('Unsubscribed mode \'{}\'.'.format(mode))
    _current_mode = mode
