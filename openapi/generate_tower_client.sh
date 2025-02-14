#!/bin/bash

echo "Downloading OpenAPI specification..." && \
curl -s -O http://localhost:8081/v1/openapi.json && \

echo "Generating API code..." && \
podman run --rm \
-v ${PWD}:/local openapitools/openapi-generator-cli generate \
-c /local/generator_config.yaml && \

echo "Copying generated files to target directory..." && \
rsync -av --exclude={'.gitignore','.openapi*','.travis.yml','*.sh'} tower-api/ ../crates/tower-api/ && \

echo "Cleaning up..." && \
rm -r openapi.json tower-api
