{
  description = "Think Better - AI-powered decision-making and problem-solving framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # The release version lives in ./VERSION; the Release workflow refuses
        # to tag a version that does not match it, so a build of a release tag
        # always reports that release. Other commits report the VERSION value
        # plus their commit hash. See CONTRIBUTING.md, "Releasing".
        version = pkgs.lib.fileContents ./VERSION;
        commit = self.shortRev or self.dirtyShortRev or "unknown";
        # Commit date of the source (lastModifiedDate is YYYYMMDDhhmmss), so
        # the build date is reproducible, as in GoReleaser builds.
        lastModified = self.lastModifiedDate or "19700101000000";
        buildDate = "${builtins.substring 0 4 lastModified}-${builtins.substring 4 2 lastModified}-${builtins.substring 6 2 lastModified}";

        think-better = pkgs.buildGoModule {
          pname = "think-better";
          inherit version;

          src = ./.;

          vendorHash = null; # no external dependencies

          # Skills are mirrored into internal/skills via `go generate` and committed;
          # TestEmbeddedInSync guarantees they match .agents/.
          env.CGO_ENABLED = 0;

          subPackages = [ "cmd/think-better" ];

          ldflags = [
            "-s" "-w"
            "-X main.version=v${version}"
            "-X main.commit=${commit}"
            "-X main.buildDate=${buildDate}"
          ];

          # Wrap the binary so Python 3 is available at runtime (used by analysis scripts)
          nativeBuildInputs = [ pkgs.makeWrapper ];
          postFixup = ''
            wrapProgram $out/bin/think-better \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.python3 ]}
          '';

          meta = with pkgs.lib; {
            description = "AI-powered decision-making and problem-solving framework";
            homepage = "https://github.com/HoangTheQuyen/think-better";
            license = licenses.mit;
            mainProgram = "think-better";
          };
        };
      in
      {
        packages = {
          default = think-better;
          think-better = think-better;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            go
            python3
            gnumake
          ];
        };
      }
    );
}
