#!/bin/bash
#
# This script generates the Python API client using the OpenAPI specification.
#

TOWER_OPENAPI_URL="https://api.tower.dev/v1/openapi-3.0.yaml"
OUTPUT_DIR="src/tower"

# Save a copy of the spec for contract testing
mkdir -p specs
curl -sL ${TOWER_OPENAPI_URL} -o specs/openapi.yaml

# We have to remove the previously-generated source in case some things were
# removed, etc.
rm -rf ${OUTPUT_DIR}/tower_api_client

cd ${OUTPUT_DIR} && uv run openapi-python-client generate --meta none \
	--url ${TOWER_OPENAPI_URL}
