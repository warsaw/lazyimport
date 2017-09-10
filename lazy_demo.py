# This is an example of how the compiler could generate code for a lazy module.
# It would be enabled by a compiler directive like __lazy_init__ = 1.  This
# makes use of my exec_mod branch of CPython, see:
#
#       https://github.com/nascheme/cpython/tree/exec_mod

def _lazy_init(mod):
    # create singleton class, set __class__ of module 'name'
    class Lazy(type(__builtins__)):
        _lazy_defs = {}
        def _lazy_def(self, name, code):
            # store code for defn of 'name'
            #print('define', name, code)
            self._lazy_defs[name] = code

        def __getattr__(self, name):
            if name in self._lazy_defs:
                code = self._lazy_defs[name]
                exec(code, self)
                del self._lazy_defs[name]
            return object.__getattribute__(self, name)
    mod.__class__ = Lazy

mod = type(__builtins__)('main')
# create class that has correct hooks
_lazy_init(mod)

source = '''\
a = 1
del a
a = 2
'''
c = compile(source, 'none', 'exec')
# create lazy version of 'a', could also be function def, class def, import
# use AST analysis to determine which are safe for laziness
mod._lazy_def('a', c)

print('lazy defs', mod._lazy_defs)
print('mod dict', mod.__dict__)
print('mod dir()', dir(mod))
print('mod.a is', mod.a)

# now make some code that uses 'a', will fail in standard Python because
# LOAD_NAME does not trigger getattr hook.
source = '''\
print(f'a is {a}')
'''
c = compile(source, 'none', 'exec')
exec(c, mod)

# another example of using global defs.
source = '''\
c = [a]
print(f'c is {c}')
'''
c = compile(source, 'none', 'exec')
exec(c, mod)
