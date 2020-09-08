# Inspired by https://github.com/akashg90
from functools import wraps
import inspect
from collections import namedtuple

class PreconditionError(TypeError):
    pass

ConditionInfo = namedtuple('ConditionInfo', ['app_args', 'closure_args', 'condition'])

def preconditions(*conditions):
    stripped_source = lambda obj: inspect.getsource(obj).strip()

    if conditions is None:
        def null_decorator(f):
            f.nopre = f
        return null_decorator

    condition_info = []
    for c in conditions:
        spec = inspect.getfullargspec(c)
        if spec.varargs or spec.varkw:
            raise PreconditionError(f'Invalid precondition must not accer * nor ** args: {stripped_source(c)}')
        i = -len(spec.defaults or ())
        if i == 0:
            appargs, closureargs = spec.args, []
        else:
            appargs, closureargs = spec.args[:i], spec.args[i:]
        condition_info.append(ConditionInfo(appargs, closureargs, c))


    def decorate(f):
        fspec = inspect.getfullargspec(f)

        for ci in condition_info:
            for app_arg in ci.app_args:
                if app_arg not in fspec.args:
                    raise PreconditionError(
                        f'Invalid precondition refers to unknown parameter {app_arg}:\n    {stripped_source(ci.condition)}\n    Known parameters: {fspec.args}')
            for closure_arg in ci.closure_args:
                if closure_arg in fspec.args:
                    raise PreconditionError(
                        f'Invalid precondition masks parameter {closure_arg}:\n    {stripped_source(ci.condition)}\n    Known parameters: {fspec.args}')

        @wraps(f)
        def g(*a, **kw):
            args = inspect.getcallargs(f, *a, **kw)
            for ci in condition_info:
                cond_response = ci.condition(*[args[aa] for aa in ci.app_args])
                if isinstance(cond_response, tuple):
                    cond, err = cond_response
                else:
                    cond, err = cond_response, PreconditionError(
                        f'Precondition failed in call {g}{inspect.formatargvalues(fspec.args, fspec.varargs, fspec.varkw, args)}\n    {stripped_source(ci.condition)}')

                if cond is None:
                    raise err

            return f(*a, **kw)

        g.nopre = f
        return g
    return decorate