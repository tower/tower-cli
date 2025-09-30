try:
    import pyiceberg as _pyiceberg

    # Re-export everything
    from pyiceberg import *
except ImportError:
    _pyiceberg = None


# Dynamic dispatch for submodules, as relevant.
def __getattr__(name):
    """Forward attribute access to the original module."""
    return getattr(_pyiceberg, name)


# Optionally, also set up the module to handle subpackage imports
# This requires Python 3.7+
def __dir__():
    return dir(_pyiceberg)
