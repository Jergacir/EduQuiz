"""
controllers.auth package shim

This file delegates imports to the sibling module file controllers/auth.py
so that `import controllers.auth` yields the full implementation (including
routes like procesarlogin) even if Python prefers the package path.
"""

# Delegate everything from the module implementation file.
from controllers.auth import *  # noqa: F401,F403
