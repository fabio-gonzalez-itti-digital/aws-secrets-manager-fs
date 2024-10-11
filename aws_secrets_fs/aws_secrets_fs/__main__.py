# Version check.
import sys
if sys.version_info < (3, 10):
    raise RuntimeError("Este paquete requiere Python 3.10+")

# Main.
from . import main
main.main()
