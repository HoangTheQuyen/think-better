// Command gen mirrors the skill sources in .agents/ into internal/skills/
// so they can be embedded into the binary with go:embed.
//
// It is run via `go generate ./internal/skills` (or `make embed-prep`).
// The copies are committed so that `go install` works without a build step;
// TestEmbeddedInSync fails whenever they drift from .agents/.
package main

import (
	"flag"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/skills/sourcefs"
)

func main() {
	src := flag.String("src", "../../.agents", "path to the .agents source directory")
	dst := flag.String("dst", ".", "path to internal/skills")
	flag.Parse()

	if err := run(*src, *dst); err != nil {
		fmt.Fprintf(os.Stderr, "gen: %v\n", err)
		os.Exit(1)
	}
}

func run(src, dst string) error {
	for _, dir := range []string{"skills", "workflows"} {
		from := filepath.Join(src, dir)
		to := filepath.Join(dst, dir)
		if err := os.RemoveAll(to); err != nil {
			return err
		}
		files, err := sourcefs.Files(os.DirFS(from))
		if err != nil {
			return fmt.Errorf("reading %s: %w", from, err)
		}
		for _, f := range files {
			data, err := fs.ReadFile(os.DirFS(from), f)
			if err != nil {
				return err
			}
			out := filepath.Join(to, filepath.FromSlash(f))
			if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
				return err
			}
			if err := os.WriteFile(out, data, 0o644); err != nil {
				return err
			}
		}
		fmt.Printf("gen: %d files -> %s\n", len(files), to)
	}
	return nil
}
