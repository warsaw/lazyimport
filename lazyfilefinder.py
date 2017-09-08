import importlib.machinery
import importlib.util
import sys


def load_lazydb(infile):
    lazydb = {}
    for line in infile:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        module, _, imported = line.partition(':')

        module = module.rstrip()
        try:
            imports = lazydb[module]
        except KeyError:
            imports = lazydb[module] = []

        imported, _, name = imported.partition('|')
        modname, _, attr = imported.partition(':')
        imports.append((modname, attr, name))

    return lazydb


def install(filename):
    try:
        infile = open(filename)
    except FileNotFoundError:
        return

    with infile:
        lazydb = load_lazydb(infile)

    for i, finder in enumerate(sys.meta_path):
        if type(finder) is importlib.machinery.FileFinder:
            break
    else:
        return

    finder = LazyFileFinder(finder.path, *finder._loaders, lazydb)
    sys.meta_path[i] = finder


class LazyFileFinder(importlib.machinery.FileFinder):

    def __init__(self, path, *loader_details, lazydb):
        super().__init__(path, *loader_details)
        self.lazydb = lazydb

    def find_spec(self, fullname, target=None):
        spec = super().find_spec(fullname, target)
        if spec is None:
            return None

        lazy = self.lazydb.get(fullname)
        if lazy:
            spec.loader = importlib.util.LazyLoader.factory(spec.loader)
            spec.loader_state = {
                    'imports': lazy,
                    }
        return spec


class LazyFileLoader(importlib.util.LazyLoader):

    def exec_module(self, module):
        imports = module.__spec__.loader_state.get('imports')
        for modname, attr, name in imports or ():
            imported = importlib.import_module(modname, module.__package__)
            if attr:
                setattr(module, name or attr, getattr(imported, attr))
            else:
                setattr(module, name or modname, imported)

        super().exec_module(module)
