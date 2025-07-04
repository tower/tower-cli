{
  description = "Tower CLI and runtime environment for Tower with build targets and devShell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    fenix = {
      url = "github:nix-community/fenix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    naersk = {
      url = "github:nix-community/naersk";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, fenix, naersk }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" "x86_64-darwin" "aarch64-linux" ] (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        rustToolchain = fenix.packages.${system}.stable.toolchain;
        rustToolchainWithMusl = fenix.packages.${system}.stable.withComponents [
          "cargo"
          "rustc"
          "rust-std"
        ] // {
          targets.x86_64-unknown-linux-musl = fenix.packages.${system}.targets.x86_64-unknown-linux-musl.stable.rust-std;
        };

        python = pkgs.python312;
        naersk-native = naersk.lib.${system}.override {
          cargo = rustToolchain;
          rustc = rustToolchain;
        };

        tower-cli = naersk-native.buildPackage {
          src = ./.;
          
          cargoBuildOptions = x: x;

          nativeBuildInputs = with pkgs; [
            pkg-config
          ];

          buildInputs = with pkgs; [
            openssl
            zlib
          ];

          meta = with pkgs.lib; {
            description = "Tower CLI and runtime environment";
            license = licenses.mit;
            platforms = [ "x86_64-linux" "aarch64-darwin" "x86_64-darwin" ];
            mainProgram = "tower";
          };
        };

        mkCrossTarget = target: let
          crossSystemConfig = {
            "x86_64-unknown-linux-musl" = "x86_64-unknown-linux-musl";
            "aarch64-unknown-linux-musl" = "aarch64-unknown-linux-musl";
            "aarch64-apple-darwin" = "aarch64-apple-darwin";
          }.${target};
          
          crossPkgs = import nixpkgs {
            inherit system;
            crossSystem = { config = crossSystemConfig; };
          };

          crossRustToolchain = fenix.packages.${system}.combine [
            fenix.packages.${system}.stable.rustc
            fenix.packages.${system}.stable.cargo
            fenix.packages.${system}.targets.${target}.stable.rust-std
          ];

          naersk-cross = naersk.lib.${system}.override {
            cargo = crossRustToolchain;
            rustc = crossRustToolchain;
          };

        in naersk-cross.buildPackage {
          src = ./.;
          
          cargoBuildOptions = x: x;

          CARGO_BUILD_TARGET = target;
          CARGO_BUILD_RUSTFLAGS = if (target == "x86_64-unknown-linux-musl" || target == "aarch64-unknown-linux-musl")
            then "-C target-feature=+crt-static" 
            else "";

          nativeBuildInputs = with pkgs; [
            pkg-config
          ] ++ pkgs.lib.optionals (target == "x86_64-unknown-linux-musl" || target == "aarch64-unknown-linux-musl") [
            crossPkgs.stdenv.cc
          ];

          buildInputs = with crossPkgs; [
            openssl
            zlib
          ];

          CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER = 
            if target == "x86_64-unknown-linux-musl" 
            then "${crossPkgs.stdenv.cc.targetPrefix}cc"
            else null;
          
          CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER = 
            if target == "aarch64-unknown-linux-musl" 
            then "${crossPkgs.stdenv.cc.targetPrefix}cc"
            else null;

          PKG_CONFIG_ALLOW_CROSS = "1";
          OPENSSL_NO_VENDOR = "1";
          OPENSSL_DIR = "${crossPkgs.openssl.dev}";
          OPENSSL_LIB_DIR = "${crossPkgs.openssl.out}/lib";
          OPENSSL_INCLUDE_DIR = "${crossPkgs.openssl.dev}/include";
        };

        tower-cli-linux-x86 = mkCrossTarget "x86_64-unknown-linux-musl";
        tower-cli-linux-arm64 = mkCrossTarget "aarch64-unknown-linux-musl";
        tower-cli-macos-arm = if system == "aarch64-darwin" then tower-cli else mkCrossTarget "aarch64-apple-darwin";

      in {
        packages = {
          default = tower-cli;
          tower-cli = tower-cli;
          tower-cli-linux-x86 = tower-cli-linux-x86;
          tower-cli-linux-arm64 = tower-cli-linux-arm64;
          tower-cli-macos-arm = tower-cli-macos-arm;
          
          tower-cli-deb-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-cli-0.3.18-amd64.deb";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-cli-linux-x86}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower-cli
              arch: amd64
              platform: linux
              version: 0.3.18
              section: utils
              priority: optional
              maintainer: Tower Computing Inc. <brad@tower.dev>
              description: |
                Tower CLI and runtime environment
                Tower is the best way to host Python data apps in production.
                This package provides the Tower CLI tool for managing and deploying
                applications to the Tower platform.
              vendor: Tower Computing Inc.
              homepage: https://github.com/tower/tower-cli
              license: MIT
              
              contents:
                - src: package/usr/bin/tower
                  dst: /usr/bin/tower
                  file_info:
                    mode: 0755
              EOF
            '';
            
            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager deb --target $out/tower-cli_0.3.18_amd64.deb
            '';
          };

          tower-cli-deb-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-cli-0.3.18-arm64.deb";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-cli-linux-arm64}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower-cli
              arch: arm64
              platform: linux
              version: 0.3.18
              section: utils
              priority: optional
              maintainer: Tower Computing Inc. <brad@tower.dev>
              description: |
                Tower CLI and runtime environment
                Tower is the best way to host Python data apps in production.
                This package provides the Tower CLI tool for managing and deploying
                applications to the Tower platform.
              vendor: Tower Computing Inc.
              homepage: https://github.com/tower/tower-cli
              license: MIT
              
              contents:
                - src: package/usr/bin/tower
                  dst: /usr/bin/tower
                  file_info:
                    mode: 0755
              EOF
            '';
            
            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager deb --target $out/tower-cli_0.3.18_arm64.deb
            '';
          };
          
          tower-cli-rpm-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-cli-0.3.18-x86_64.rpm";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-cli-linux-x86}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower-cli
              arch: x86_64
              platform: linux
              version: 0.3.18
              release: 1
              maintainer: Tower Computing Inc. <brad@tower.dev>
              description: |
                Tower CLI and runtime environment
                Tower is the best way to host Python data apps in production.
                This package provides the Tower CLI tool for managing and deploying
                applications to the Tower platform.
              vendor: Tower Computing Inc.
              homepage: https://github.com/tower/tower-cli
              license: MIT
              
              contents:
                - src: package/usr/bin/tower
                  dst: /usr/bin/tower
                  file_info:
                    mode: 0755
              EOF
            '';
            
            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-cli-0.3.18-1.x86_64.rpm
            '';
          };

          tower-cli-rpm-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-cli-0.3.18-aarch64.rpm";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-cli-linux-arm64}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower-cli
              arch: aarch64
              platform: linux
              version: 0.3.18
              release: 1
              maintainer: Tower Computing Inc. <brad@tower.dev>
              description: |
                Tower CLI and runtime environment
                Tower is the best way to host Python data apps in production.
                This package provides the Tower CLI tool for managing and deploying
                applications to the Tower platform.
              vendor: Tower Computing Inc.
              homepage: https://github.com/tower/tower-cli
              license: MIT
              
              contents:
                - src: package/usr/bin/tower
                  dst: /usr/bin/tower
                  file_info:
                    mode: 0755
              EOF
            '';
            
            installPhase = ''
              mkdir -p $out
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-cli-0.3.18-1.aarch64.rpm
            '';
          };
        };

        devShells.default = pkgs.mkShell {
          nativeBuildInputs = with pkgs; [
            rustToolchain
            python
            maturin
            python312Packages.pip
            pkg-config
            openssl
          ];
          
          buildInputs = with pkgs; [
            openssl
            zlib
          ];

          shellHook = ''
            export RUST_LOG=debug
            export PYTHONPATH=$PWD/src:$PYTHONPATH
            echo "Tower CLI development environment"
            echo "Python: $(python --version)"
            echo "Rust: $(rustc --version)"
          '';
        };

        apps = {
          default = {
            type = "app";
            program = "${tower-cli}/bin/tower";
          };
        };
      }
    );
}
