import sys
import traceback
from pathlib import Path

# Ensure project venv site-packages are available if running from venv
print('Python executable:', sys.executable)
print('Sys.path[0]:', sys.path[0])

from PyInstaller.lib.modulegraph import modulegraph

class VerboseModuleGraph(modulegraph.ModuleGraph):
    def _scan_code(self, module, co, ast=None):
        try:
            name = getattr(module, 'identifier', None) or getattr(module, 'name', None) or module
        except Exception:
            name = module
        print('\n--- Scanning module code:', name)
        return super()._scan_code(module, co, ast)

def main():
    try:
        mg = VerboseModuleGraph()
        script = Path('main.py').resolve()
        print('Adding script:', script)
        mg.add_script(str(script))
        print('Analysis completed without exception')
    except Exception as e:
        print('\nException during modulegraph analysis:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
