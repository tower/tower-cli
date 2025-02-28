#!/bin/bash

echo "Downloading OpenAPI specification..." && \
curl -s -O https://api.tower.dev/v1/openapi.json && \

echo "Generating API code..." && \
podman run --rm \
-v ${PWD}:/local openapitools/openapi-generator-cli generate \
-c /local/generator_config.yaml && \

echo "Copying generated files to target directory..." && \
rsync -avm --delete --exclude={'.gitignore','.openapi*','.travis.yml','*.sh'} tower-api/ ../crates/tower-api/ && \

echo "Cleaning up..." && \
rm -r openapi.json tower-api
