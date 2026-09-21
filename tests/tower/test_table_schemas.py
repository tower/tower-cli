from importlib.metadata import version

import pyarrow as pa
import pytest
from pyiceberg import types as iceberg_types
from pyiceberg.catalog.memory import InMemoryCatalog
from pyiceberg.exceptions import ValidationError as IcebergValidationError
from pyiceberg.io.pyarrow import UnsupportedPyArrowTypeException

import tower._tables as tables_module
from tower._context import TowerContext


_PYICEBERG_SUPPORTS_FLOAT16 = tuple(
    int(component) for component in version("pyiceberg").split(".")[:2]
) >= (0, 12)


class RecordingCatalog:
    def __init__(self):
        self.schemas = []

    def create_namespace_if_not_exists(self, namespace):
        pass

    def create_table(self, identifier, schema):
        self.schemas.append(schema)
        return object()

    def create_table_if_not_exists(self, identifier, schema):
        self.schemas.append(schema)
        return object()


def make_reference(catalog, name="events"):
    context = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
    )
    return tables_module.TableReference(
        context,
        catalog,
        name,
        namespace="default",
    )


@pytest.fixture
def in_memory_schema_catalog(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "PYICEBERG_DOWNCAST_NS_TIMESTAMP_TO_US_ON_WRITE",
        "false",
    )
    catalog = InMemoryCatalog("schema-tests", warehouse=tmp_path.as_uri())
    catalog.create_namespace("default")
    return catalog


@pytest.mark.parametrize("method", ["create", "create_if_not_exists"])
def test_table_creation_passes_original_arrow_schema_to_catalog(method):
    catalog = RecordingCatalog()
    schema = pa.schema([pa.field("id", pa.int64(), nullable=False)])
    reference = make_reference(catalog)

    getattr(reference, method)(schema)

    assert catalog.schemas == [schema]
    assert catalog.schemas[0] is schema


@pytest.mark.parametrize("catalog_type", ["s3-tables", "apache-polaris"])
def test_external_string_catalog_creation_preserves_original_arrow_schema(
    monkeypatch, catalog_type
):
    context = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
        api_key="api-key",
    )
    catalog = RecordingCatalog()
    schema = pa.schema([pa.field("id", pa.int64(), nullable=False)])
    loaded_catalogs = []

    def unexpected_call(*args, **kwargs):
        raise AssertionError("external catalogs must not vend Tower credentials")

    def load_catalog(name):
        loaded_catalogs.append(name)
        return catalog

    monkeypatch.setattr(
        tables_module.TowerContext, "build", staticmethod(lambda: context)
    )
    monkeypatch.setattr(
        tables_module,
        "_describe_tower_catalog_type",
        lambda ctx, name, environment: catalog_type,
    )
    monkeypatch.setattr(tables_module, "_has_pyiceberg_catalog_config", unexpected_call)
    monkeypatch.setattr(tables_module, "get_tower_catalog_credentials", unexpected_call)
    monkeypatch.setattr(tables_module, "load_catalog", load_catalog)

    reference = tables_module.tables("events", catalog="external", namespace="default")
    reference.create(schema)

    assert loaded_catalogs == ["external"]
    assert reference._tower_vended is False
    assert reference._catalog is catalog
    assert catalog.schemas == [schema]
    assert catalog.schemas[0] is schema


def test_pyiceberg_assigns_nested_field_ids_docs_and_nullability(
    in_memory_schema_catalog,
):
    schema = pa.schema(
        [
            pa.field(
                "id",
                pa.int64(),
                nullable=False,
                metadata={b"doc": b"identifier"},
            ),
            pa.field(
                "profile",
                pa.struct(
                    [
                        pa.field(
                            "name",
                            pa.string(),
                            nullable=False,
                            metadata={b"doc": b"display name"},
                        ),
                        pa.field(
                            "tags",
                            pa.list_(pa.field("element", pa.string(), nullable=True)),
                            nullable=True,
                        ),
                    ]
                ),
                nullable=True,
                metadata={b"doc": b"profile doc"},
            ),
            pa.field(
                "attributes",
                pa.map_(
                    pa.string(),
                    pa.field("value", pa.int32(), nullable=True),
                ),
                nullable=True,
            ),
        ]
    )

    make_reference(in_memory_schema_catalog, "nested").create(schema)
    iceberg_schema = in_memory_schema_catalog.load_table("default.nested").schema()

    assert {field.name: field.field_id for field in iceberg_schema.fields} == {
        "id": 1,
        "profile": 2,
        "attributes": 3,
    }

    assert iceberg_schema.find_field("id").required is True
    assert iceberg_schema.find_field("id").doc == "identifier"
    assert iceberg_schema.find_field("profile").required is False
    assert iceberg_schema.find_field("profile").doc == "profile doc"
    assert iceberg_schema.find_field("profile.name").field_id == 4
    assert iceberg_schema.find_field("profile.name").required is True
    assert iceberg_schema.find_field("profile.name").doc == "display name"
    assert iceberg_schema.find_field("profile.tags").field_id == 5
    assert iceberg_schema.find_field("profile.tags.element").field_id == 6
    assert iceberg_schema.find_field("profile.tags.element").required is False
    assert iceberg_schema.find_field("attributes.key").field_id == 7
    assert iceberg_schema.find_field("attributes.key").required is True
    assert iceberg_schema.find_field("attributes.value").field_id == 8
    assert iceberg_schema.find_field("attributes.value").required is False


@pytest.mark.parametrize(
    ("name", "arrow_type", "iceberg_type"),
    [
        ("timestamp_s", pa.timestamp("s"), iceberg_types.TimestampType()),
        ("timestamp_ms", pa.timestamp("ms"), iceberg_types.TimestampType()),
        ("timestamp_us", pa.timestamp("us"), iceberg_types.TimestampType()),
        (
            "timestamp_utc",
            pa.timestamp("us", tz="UTC"),
            iceberg_types.TimestamptzType(),
        ),
        ("time_us", pa.time64("us"), iceberg_types.TimeType()),
        ("date", pa.date32(), iceberg_types.DateType()),
        (
            "decimal",
            pa.decimal128(38, 10),
            iceberg_types.DecimalType(38, 10),
        ),
    ],
)
def test_pyiceberg_accepts_supported_arrow_precision(
    in_memory_schema_catalog, name, arrow_type, iceberg_type
):
    schema = pa.schema([pa.field("value", arrow_type)])

    make_reference(in_memory_schema_catalog, name).create(schema)

    table = in_memory_schema_catalog.load_table(f"default.{name}")
    assert table.schema().find_field("value").field_type == iceberg_type


def test_float16_schema_follows_pyiceberg_version(in_memory_schema_catalog):
    schema = pa.schema([pa.field("value", pa.float16())])

    if not _PYICEBERG_SUPPORTS_FLOAT16:
        with pytest.raises(UnsupportedPyArrowTypeException):
            make_reference(in_memory_schema_catalog, "float16").create(schema)
        return

    make_reference(in_memory_schema_catalog, "float16").create(schema)

    table = in_memory_schema_catalog.load_table("default.float16")
    assert table.schema().find_field("value").field_type == iceberg_types.FloatType()


@pytest.mark.parametrize(
    ("name", "arrow_type"),
    [
        ("timestamp_ns", pa.timestamp("ns")),
        ("timestamp_non_utc", pa.timestamp("us", tz="Europe/Berlin")),
        ("time32", pa.time32("s")),
        ("time_ns", pa.time64("ns")),
        ("date64", pa.date64()),
        ("decimal256", pa.decimal256(38, 10)),
    ],
)
def test_pyiceberg_rejects_lossy_or_unsupported_arrow_types(
    in_memory_schema_catalog, name, arrow_type
):
    schema = pa.schema([pa.field("value", arrow_type)])

    with pytest.raises(UnsupportedPyArrowTypeException):
        make_reference(in_memory_schema_catalog, name).create(schema)


def test_pyiceberg_rejects_negative_decimal_scale(in_memory_schema_catalog):
    schema = pa.schema([pa.field("value", pa.decimal128(10, -2))])

    with pytest.raises(IcebergValidationError, match=r"decimal\(10, -2\)"):
        make_reference(in_memory_schema_catalog, "negative_scale").create(schema)
