# -*- coding: utf-8 -*-
from collections import OrderedDict, defaultdict, deque
import itertools


# This first part of the code is basically getting the required
# information to properly identify the argument later on to check
# its priority.

# We seem to redo a lot of things pytest is already doing. It would
# be easier to have an argument to pytest's fixture decorator and
# pass the priority directly inside the created FixtureDef

# But if we are not changing pytest code then it seems this is how
# we should do it


import inspect
from _pytest.fixtures import getfixturemarker, FixtureFunctionMarker
# TODO: Check if we need get_real_method instead (holder?)
from _pytest.compat import get_real_func
from py.path import local


def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0], None)
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


def parameter_priority(priority):

    def get_param_spec_decorator(func):
        # Just inspect the function to create the key to
        # uniquely identify the argument and its priority

        # Returns the fixture function unchanged

        marker = getfixturemarker(func)
        if not isinstance(marker, FixtureFunctionMarker):
            return func

        scopenum = scopes.index(marker.scope)

        real_func = get_real_func(func)
        argname = real_func.__name__
        fspath = local(real_func.__globals__['__file__'])
        cls = get_class_that_defined_method(real_func)

        if scopenum == 0:  # session
            key = argname
        elif scopenum == 1:  # package
            key = (argname, fspath.dirpath())
        elif scopenum == 2:  # module
            key = (argname, fspath)
        elif scopenum == 3:  # class
            key = (argname, fspath, cls)

        argname_prioinfo[scopenum][key] = priority

        return func

    return get_param_spec_decorator


# This is where we store the priorities for each argument
# from the test definition with our parameter_priority
# decorator. From now onwards this is all we need.
# For each scopenum, save the argnames and its priorities
argname_prioinfo = {0: {},
                    1: {},
                    2: {},
                    3: {}}


# Below this point is the same pytest sorting algorithm but
# upgraded to consider not only scopes as a priority, but each
# possible (scope, priority) pair - effectively creating "virtual scopes"
# for sorting.


scopes = "session package module class function".split()
scopenum_function = scopes.index("function")


def pytest_collection_modifyitems(items):
    # separate parametrized setups
    items[:] = reorder_items(items)


def get_parametrized_fixture_keys(item, scopenum, priority):
    """ return list of keys for all parametrized arguments which match
    the specified scope. """
    assert scopenum < scopenum_function  # function
    try:
        cs = item.callspec
    except AttributeError:
        pass
    else:
        # cs.indices.items() is random order of argnames.  Need to
        # sort this so that different calls to
        # get_parametrized_fixture_keys will be deterministic.
        for argname, param_index in sorted(cs.indices.items()):
            if cs._arg2scopenum[argname] != scopenum:
                continue
            if scopenum == 0:  # session
                key = (argname, param_index)
                arg_priority = argname_prioinfo[scopenum].get(key[0], lowest_priority)
            elif scopenum == 1:  # package
                key = (argname, param_index, item.fspath.dirpath())
                arg_priority = argname_prioinfo[scopenum].get((key[0], key[2]), lowest_priority)
            elif scopenum == 2:  # module
                key = (argname, param_index, item.fspath)
                arg_priority = argname_prioinfo[scopenum].get((key[0], key[2]), lowest_priority)
            elif scopenum == 3:  # class
                key = (argname, param_index, item.fspath, item.cls)
                arg_priority = argname_prioinfo[scopenum].get((key[0], key[2], key[3]), lowest_priority)


            if arg_priority != priority:
                continue

            yield key


# algorithm for sorting on a per-parametrized resource setup basis
# it is called for scopenum==0 (session) first and performs sorting
# down to the lower scopes such as to minimize number of "high scope"
# setups and teardowns

# Priorities are tuple (scopenum, priority)
# There could be more than 4 priorities (any number actually)...
lowest_priority = 3

priorities = list(itertools.product(
    range(0, scopenum_function),
    range(0, lowest_priority)
))

def reorder_items(items):
    argkeys_cache = {}
    items_by_argkey = {}
    for scopenum in range(0, scopenum_function):
        for priority in range(0, lowest_priority):
            argkeys_cache[scopenum, priority] = d = {}
            items_by_argkey[scopenum, priority] = item_d = defaultdict(deque)
            for item in items:
                keys = OrderedDict.fromkeys(get_parametrized_fixture_keys(item, scopenum, priority))
                if keys:
                    d[item] = keys
                    for key in keys:
                        item_d[key].append(item)
    items = OrderedDict.fromkeys(items)
    return list(reorder_items_atpriority(items, argkeys_cache, items_by_argkey, 0))


def fix_cache_order(item, argkeys_cache, items_by_argkey):
    for priority in priorities:
        for key in argkeys_cache[priority].get(item, []):
            items_by_argkey[priority][key].appendleft(item)


def reorder_items_atpriority(items, argkeys_cache, items_by_argkey, priority_index):
    if priority_index >= len(priorities) or len(items) < 3:
        return items
    priority = priorities[priority_index]

    ignore = set()
    items_deque = deque(items)
    items_done = OrderedDict()
    scoped_items_by_argkey = items_by_argkey[priority]
    scoped_argkeys_cache = argkeys_cache[priority]
    while items_deque:
        no_argkey_group = OrderedDict()
        slicing_argkey = None
        while items_deque:
            item = items_deque.popleft()
            if item in items_done or item in no_argkey_group:
                continue
            argkeys = OrderedDict.fromkeys(
                k for k in scoped_argkeys_cache.get(item, []) if k not in ignore
            )
            if not argkeys:
                no_argkey_group[item] = None
            else:
                slicing_argkey, _ = argkeys.popitem()
                # we don't have to remove relevant items from later in the deque because they'll just be ignored
                matching_items = [
                    i for i in scoped_items_by_argkey[slicing_argkey] if i in items
                ]
                for i in reversed(matching_items):
                    fix_cache_order(i, argkeys_cache, items_by_argkey)
                    items_deque.appendleft(i)
                break
        if no_argkey_group:
            no_argkey_group = reorder_items_atpriority(
                no_argkey_group, argkeys_cache, items_by_argkey, priority_index + 1
            )
            for item in no_argkey_group:
                items_done[item] = None
        ignore.add(slicing_argkey)
    return items_done
