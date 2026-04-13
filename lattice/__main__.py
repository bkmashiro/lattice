"""Allow running Lattice as a module: python -m lattice"""

from lattice.cli import main
import sys

sys.exit(main())
