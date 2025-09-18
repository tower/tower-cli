try:
    import pyarrow as _pyarrow

    # Re-export everything
    from pyarrow import *
except ImportError:
    _pyarrow = None
