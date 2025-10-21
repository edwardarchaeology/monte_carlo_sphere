import importlib, sys
try:
    importlib.import_module('main')
    print('imported main OK')
except Exception as e:
    print('import main failed:', type(e).__name__, e)
    sys.exit(1)
