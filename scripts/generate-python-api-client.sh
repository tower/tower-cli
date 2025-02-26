#!/bin/bash
#
# This script generates the Python API client using the OpenAPI specification.
#

TOWER_OPENAPI_URL="https://api.tower.dev/v1/openapi-3.0.yaml"
OUTPUT_DIR="src/tower"

cd ${OUTPUT_DIR} && openapi-python-client update --meta none \
	--url ${TOWER_OPENAPI_URL}
