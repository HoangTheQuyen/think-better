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

        version =
          if self ? shortRev
          then self.shortRev
          else "dev";

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
            "-X main.version=${version}"
            "-X main.commit=${version}"
            "-X main.buildDate=1970-01-01"
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
