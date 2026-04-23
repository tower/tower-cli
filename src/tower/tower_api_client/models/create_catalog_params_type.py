from enum import Enum


class CreateCatalogParamsType(str, Enum):
    APACHE_POLARIS = "apache-polaris"
    CLOUDFLARE_R2_CATALOG = "cloudflare-r2-catalog"
    LAKEKEEPER = "lakekeeper"
    S3_TABLES = "s3-tables"
    SNOWFLAKE_OPEN_CATALOG = "snowflake-open-catalog"
    TOWER_CATALOG = "tower-catalog"

    def __str__(self) -> str:
        return str(self.value)
