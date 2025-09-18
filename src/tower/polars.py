try:
    import polars as _polars

    # Re-export everything from polars
    from polars import *

    # Or if you prefer, you can be explicit about what you re-export
    # from polars import DataFrame, Series, etc.
except ImportError:
    _polars = None
    # Set specific names to None if you're using explicit imports
