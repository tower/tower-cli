from enum import Enum


class CreateCatalogParamsType(str, Enum):
    APACHE_POLARIS = "apache-polaris"
    CLOUDFLARE_R2_CATALOG = "cloudflare-r2-catalog"
    LAKEKEEPER = "lakekeeper"
    SNOWFLAKE_OPEN_CATALOG = "snowflake-open-catalog"

    def __str__(self) -> str:
        return str(self.value)
