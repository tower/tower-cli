{
  description = "Tower CLI and runtime environment for Tower with build targets and devShell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    naersk = {
      url = "github:nix-community/naersk";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      rust-overlay,
      naersk,
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" "x86_64-darwin" "aarch64-linux" ] (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };

        maintainer = "Tower Computing Inc. <support@tower.dev>";
        homepage = "https://github.com/tower/tower-cli";
        description = "Tower CLI and runtime environment";
        longDescription = " |
          Tower CLI and runtime environment
          Tower is the best way to host Python data apps in production.
          This package provides the Tower CLI tool for managing and deploying
          applications to the Tower platform.
        ";

        getVersionScript = ''
          VERSION=${builtins.getEnv "VERSION"}
          if [ -z "$VERSION" ]; then
            VERSION="SNAPSHOT"
          fi
        '';

        mkNfpmConfig =
          { arch, packager }:
          ''
            name: tower
            arch: ${arch}
            platform: linux
            version: $VERSION
            ${if packager == "rpm" then "release: 1" else "section: utils\npriority: optional"}
            maintainer: ${maintainer}
            description: ${longDescription}
            vendor: Tower Computing Inc.
            homepage: "${homepage}"
            license: MIT

            contents:
              - src: package/usr/bin/tower
                dst: /usr/bin/tower
                file_info:
                  mode: 0755
              - src: package/usr/bin/uv-wrapper
                dst: /usr/bin/uv-wrapper
                file_info:
                  mode: 0755
          '';

        commonNativeBuildInputs = with pkgs; [ pkg-config ];
        commonBuildInputs = with pkgs; [
          openssl
          zlib
        ];

        isMuslTarget =
          target: target == "x86_64-unknown-linux-musl" || target == "aarch64-unknown-linux-musl";

        rustToolchain = pkgs.rust-bin.stable.latest.default;

        python = pkgs.python312;
        naersk-native = naersk.lib.${system}.override {
          cargo = rustToolchain;
          rustc = rustToolchain;
        };

        tower = naersk-native.buildPackage {
          src = ./.;

          cargoBuildOptions = x: x;

          nativeBuildInputs = commonNativeBuildInputs;
          buildInputs = commonBuildInputs;

          meta = with pkgs.lib; {
            inherit description;
            license = licenses.mit;
            platforms = [
              "x86_64-linux"
              "aarch64-darwin"
              "x86_64-darwin"
            ];
            mainProgram = "tower";
          };
        };

        mkCrossTarget =
          target:
          let
            crossSystemConfig =
              {
                "x86_64-unknown-linux-musl" = "x86_64-unknown-linux-musl";
                "aarch64-unknown-linux-musl" = "aarch64-unknown-linux-musl";
                "aarch64-apple-darwin" = "aarch64-apple-darwin";
              }
              .${target};

            crossPkgs = import nixpkgs {
              inherit system;
              crossSystem = {
                config = crossSystemConfig;
              };
            };

            crossRustToolchain = pkgs.rust-bin.stable.latest.default.override {
              targets = [ target ];
            };

            naersk-cross = naersk.lib.${system}.override {
              cargo = crossRustToolchain;
              rustc = crossRustToolchain;
            };

          in
          naersk-cross.buildPackage {
            src = ./.;

            cargoBuildOptions = x: x;

            CARGO_BUILD_TARGET = target;
            CARGO_BUILD_RUSTFLAGS = if (isMuslTarget target) then "-C target-feature=+crt-static" else "";

            nativeBuildInputs =
              commonNativeBuildInputs
              ++ pkgs.lib.optionals (isMuslTarget target) [
                crossPkgs.stdenv.cc
              ];

            buildInputs = with crossPkgs; commonBuildInputs;

            CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER =
              if target == "x86_64-unknown-linux-musl" then "${crossPkgs.stdenv.cc.targetPrefix}cc" else null;

            CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER =
              if target == "aarch64-unknown-linux-musl" then "${crossPkgs.stdenv.cc.targetPrefix}cc" else null;

            PKG_CONFIG_ALLOW_CROSS = "1";
            OPENSSL_NO_VENDOR = "1";
            OPENSSL_DIR = "${crossPkgs.openssl.dev}";
            OPENSSL_LIB_DIR = "${crossPkgs.openssl.out}/lib";
            OPENSSL_INCLUDE_DIR = "${crossPkgs.openssl.dev}/include";
          };

        tower-linux-x86 = mkCrossTarget "x86_64-unknown-linux-musl";
        tower-linux-arm64 = mkCrossTarget "aarch64-unknown-linux-musl";
        tower-macos-arm =
          if system == "aarch64-darwin" then tower else mkCrossTarget "aarch64-apple-darwin";

      in
      {
        packages = {
          default = tower;
          tower = tower;
          tower-linux-x86 = tower-linux-x86;
          tower-linux-arm64 = tower-linux-arm64;
          tower-macos-arm = tower-macos-arm;

          tower-deb-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-deb-amd64";
            nativeBuildInputs = with pkgs; [
              nfpm
              python
              git
            ];

            unpackPhase = "true";

            buildPhase = ''
              ${getVersionScript}

              mkdir -p package/usr/bin
              cp ${tower-linux-x86}/bin/tower package/usr/bin/
              cp ${tower-linux-x86}/bin/uv-wrapper package/usr/bin/
              chmod 755 package/usr/bin/tower package/usr/bin/uv-wrapper

              cat > nfpm.yaml << EOF
              ${mkNfpmConfig {
                arch = "amd64";
                packager = "deb";
              }}
              EOF
            '';

            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager deb --target $out/tower_''${VERSION}_amd64.deb
            '';
          };

          tower-deb-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-deb-arm64";
            nativeBuildInputs = with pkgs; [
              nfpm
              python
              git
            ];

            unpackPhase = "true";

            buildPhase = ''
              ${getVersionScript}

              mkdir -p package/usr/bin
              cp ${tower-linux-arm64}/bin/tower package/usr/bin/
              cp ${tower-linux-arm64}/bin/uv-wrapper package/usr/bin/
              chmod 755 package/usr/bin/tower package/usr/bin/uv-wrapper

              cat > nfpm.yaml << EOF
              ${mkNfpmConfig {
                arch = "arm64";
                packager = "deb";
              }}
              EOF
            '';

            installPhase = ''
              mkdir -p $out
              cat nfpm.yaml
              nfpm package --config nfpm.yaml --packager deb --target $out/tower_''${VERSION}_arm64.deb
            '';
          };

          tower-rpm-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-rpm-x86_64";
            nativeBuildInputs = with pkgs; [
              nfpm
              python
              git
            ];

            unpackPhase = "true";

            buildPhase = ''
              ${getVersionScript}

              mkdir -p package/usr/bin
              cp ${tower-linux-x86}/bin/tower package/usr/bin/
              cp ${tower-linux-x86}/bin/uv-wrapper package/usr/bin/
              chmod 755 package/usr/bin/tower package/usr/bin/uv-wrapper

              cat > nfpm.yaml << EOF
              ${mkNfpmConfig {
                arch = "x86_64";
                packager = "rpm";
              }}
              EOF
            '';

            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-''${VERSION}-1.x86_64.rpm
            '';
          };

          tower-rpm-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-rpm-aarch64";
            nativeBuildInputs = with pkgs; [
              nfpm
              python
              git
            ];

            unpackPhase = "true";

            buildPhase = ''
              ${getVersionScript}

              mkdir -p package/usr/bin
              cp ${tower-linux-arm64}/bin/tower package/usr/bin/
              cp ${tower-linux-arm64}/bin/uv-wrapper package/usr/bin/
              chmod 755 package/usr/bin/tower package/usr/bin/uv-wrapper

              cat > nfpm.yaml << EOF
              ${mkNfpmConfig {
                arch = "aarch64";
                packager = "rpm";
              }}
              EOF
            '';

            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-''${VERSION}-1.aarch64.rpm
            '';
          };
        };

        devShells.default = pkgs.mkShell {
          nativeBuildInputs = with pkgs; [
            rustToolchain
            python
            maturin
            python312Packages.pip
            uv
            behave
            pkg-config
            openssl
          ];

          buildInputs = commonBuildInputs;

          shellHook = ''
            export RUST_LOG=debug
            export PYTHONPATH=$PWD/src:$PYTHONPATH
            echo "Tower CLI development environment"
            echo "Python: $(python --version)"
            echo "Rust: $(rustc --version)"
            echo "Behave: $(behave --version 2>/dev/null || echo 'not available')"
          '';
        };

        apps = {
          default = {
            type = "app";
            program = "${tower}/bin/tower";
          };
        };
      }
    );
}
