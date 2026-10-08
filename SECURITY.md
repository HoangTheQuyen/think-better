# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in **think-better**, please report it responsibly.

### How to Report

1. **DO NOT** open a public GitHub issue for security vulnerabilities.
2. Email your findings to: **hoangthequyen01@gmail.com**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours of your report.
- **Assessment** of severity and impact within 1 week.
- **Fix and disclosure** coordinated with you before public release.

### Scope

This policy applies to:
- The `think-better` CLI binary
- Embedded skill and workflow files
- Build and release infrastructure (GitHub Actions)

### Out of Scope

- Third-party AI assistants (Claude, Copilot, etc.) — report vulnerabilities to their respective vendors.
- Social engineering attacks.

## Verifying releases

Every release asset is built by the [Release workflow](.github/workflows/release.yml)
on GitHub Actions, after the full CI suite passed on the same commit.
Starting with v1.4.0, each release has:

- `checksums.txt`: SHA-256 of every asset (`install.sh` and `install.ps1` check it automatically).
- A [build provenance attestation](https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations)
  for every binary, archive and `checksums.txt`:

  ```sh
  gh attestation verify think-better-linux-amd64 --repo HoangTheQuyen/think-better
  ```

- `checksums.txt.sigstore.json`: a keyless [cosign](https://docs.sigstore.dev/) signature of `checksums.txt`:

  ```sh
  cosign verify-blob checksums.txt \
    --bundle checksums.txt.sigstore.json \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com \
    --certificate-identity-regexp '^https://github\.com/HoangTheQuyen/think-better/\.github/workflows/release\.yml@refs/(tags/v.+|heads/main)$'
  sha256sum --ignore-missing -c checksums.txt   # macOS: shasum -a 256 --ignore-missing -c checksums.txt
  ```

- `*.sbom.json`: an SPDX software bill of materials for each archive.

Builds are reproducible: timestamps come from the tagged commit, not the
build time, so checking out a tag and running
`goreleaser release --snapshot --clean --skip=sign` with the same Go
(`go.mod`) and GoReleaser (`release.yml`) versions gives byte-identical
`think-better-<os>-<arch>` binaries. CI checks that two builds match.

## Recognition

We appreciate security researchers who help keep think-better safe. Contributors who report valid vulnerabilities will be acknowledged in our release notes (with permission).
