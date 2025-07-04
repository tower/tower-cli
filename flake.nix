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

        version = "0.3.18";
        maintainer = "Tower Computing Inc. <support@tower.dev>";
        homepage = "https://github.com/tower/tower-cli";
        description = "Tower CLI and runtime environment";
        longDescription = ''
          Tower CLI and runtime environment
          Tower is the best way to host Python data apps in production.
          This package provides the Tower CLI tool for managing and deploying
          applications to the Tower platform.
        '';

        commonNativeBuildInputs = with pkgs; [ pkg-config ];
        commonBuildInputs = with pkgs; [ openssl zlib ];

        isMuslTarget = target: target == "x86_64-unknown-linux-musl" || target == "aarch64-unknown-linux-musl";

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

        tower = naersk-native.buildPackage {
          src = ./.;
          
          cargoBuildOptions = x: x;

          nativeBuildInputs = commonNativeBuildInputs;
          buildInputs = commonBuildInputs;

          meta = with pkgs.lib; {
            inherit description;
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
          CARGO_BUILD_RUSTFLAGS = if (isMuslTarget target)
            then "-C target-feature=+crt-static" 
            else "";

          nativeBuildInputs = commonNativeBuildInputs ++ pkgs.lib.optionals (isMuslTarget target) [
            crossPkgs.stdenv.cc
          ];

          buildInputs = with crossPkgs; commonBuildInputs;

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

        tower-linux-x86 = mkCrossTarget "x86_64-unknown-linux-musl";
        tower-linux-arm64 = mkCrossTarget "aarch64-unknown-linux-musl";
        tower-macos-arm = if system == "aarch64-darwin" then tower else mkCrossTarget "aarch64-apple-darwin";

      in {
        packages = {
          default = tower;
          tower = tower;
          tower-linux-x86 = tower-linux-x86;
          tower-linux-arm64 = tower-linux-arm64;
          tower-macos-arm = tower-macos-arm;
          
          tower-deb-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-${version}-amd64.deb";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-linux-x86}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower
              arch: amd64
              platform: linux
              version: ${version}
              section: utils
              priority: optional
              maintainer: ${maintainer}
              description: |
                ${longDescription}
              vendor: Tower Computing Inc.
              homepage: ${homepage}
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
              nfpm package --config nfpm.yaml --packager deb --target $out/tower_${version}_amd64.deb
            '';
          };

          tower-cli-deb-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-${version}-arm64.deb";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-linux-arm64}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower
              arch: arm64
              platform: linux
              version: ${version}
              section: utils
              priority: optional
              maintainer: ${maintainer}
              description: |
                ${longDescription}
              vendor: Tower Computing Inc.
              homepage: ${homepage}
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
              nfpm package --config nfpm.yaml --packager deb --target $out/tower_${version}_arm64.deb
            '';
          };
          
          tower-rpm-x86 = pkgs.stdenv.mkDerivation {
            name = "tower-${version}-x86_64.rpm";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-linux-x86}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower
              arch: x86_64
              platform: linux
              version: ${version}
              release: 1
              maintainer: ${maintainer}
              description: |
                ${longDescription}
              vendor: Tower Computing Inc.
              homepage: ${homepage}
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
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-${version}-1.x86_64.rpm
            '';
          };

          tower-rpm-arm64 = pkgs.stdenv.mkDerivation {
            name = "tower-${version}-aarch64.rpm";
            nativeBuildInputs = with pkgs; [ nfpm ];
            
            unpackPhase = "true";
            
            buildPhase = ''
              mkdir -p package/usr/bin
              cp ${tower-linux-arm64}/bin/tower package/usr/bin/
              chmod 755 package/usr/bin/tower
              
              cat > nfpm.yaml << 'EOF'
              name: tower
              arch: aarch64
              platform: linux
              version: ${version}
              release: 1
              maintainer: ${maintainer}
              description: |
                ${longDescription}
              vendor: Tower Computing Inc.
              homepage: ${homepage}
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
              nfpm package --config nfpm.yaml --packager rpm --target $out/tower-${version}-1.aarch64.rpm
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
          
          buildInputs = commonBuildInputs;

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
            program = "${tower}/bin/tower";
          };
        };
      }
    );
}
