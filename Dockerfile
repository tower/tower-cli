FROM --platform=$BUILDPLATFORM alpine:3 AS fetch
ARG TARGETARCH
ARG VERSION
RUN apk add --no-cache curl tar xz \
 && case "$TARGETARCH" in \
      amd64) ARCH=x86_64 ;; \
      arm64) ARCH=aarch64 ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac \
 && curl -fsSL -o /tmp/tower.tar.xz \
      "https://github.com/tower/tower-cli/releases/download/v${VERSION}/tower-${ARCH}-unknown-linux-musl.tar.xz" \
 && mkdir -p /out \
 && tar -xJf /tmp/tower.tar.xz -C /out --strip-components=1 \
 && chmod +x /out/tower

FROM gcr.io/distroless/static-debian12
COPY --from=fetch /out/tower /usr/local/bin/tower
ENTRYPOINT ["/usr/local/bin/tower"]
