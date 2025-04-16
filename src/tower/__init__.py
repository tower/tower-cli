from ._client import (
    run_app,
    wait_for_run,
)

from ._features import enabled_features

if enabled_features.get("ai"):
    from ._llms import llms

if enabled_features.get("iceberg"):
    from ._tables import (
        create_table,
        load_table,
    )
