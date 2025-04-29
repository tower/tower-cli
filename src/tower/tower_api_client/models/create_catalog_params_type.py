from enum import Enum


class CreateCatalogParamsType(str, Enum):
    APACHE_POLARIS = "apache-polaris"
    SNOWFLAKE_OPEN_CATALOG = "snowflake-open-catalog"

    def __str__(self) -> str:
        return str(self.value)
