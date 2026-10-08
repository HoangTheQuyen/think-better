// Command gen mirrors the skill sources in .agents/ into internal/skills/
// so they can be embedded into the binary with go:embed.
//
// It is run via `go generate ./internal/skills` (or `make embed-prep`).
// The copies are committed so that `go install` works without a build step;
// TestEmbeddedInSync fails whenever they drift from .agents/.
package main

import (
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/skills/sourcefs"
)

var dirs = []string{"skills", "workflows"}

func main() {
	src := flag.String("src", "../../.agents", "path to the .agents source directory")
	dst := flag.String("dst", ".", "path to internal/skills")
	flag.Parse()

	if err := run(*src, *dst); err != nil {
		fmt.Fprintf(os.Stderr, "gen: %v\n", err)
		os.Exit(1)
	}
}

// run copies src/{skills,workflows} to dst. Everything is read and written
// to a staging directory first; the existing copies are only replaced once
// that succeeded, so a bad -src never leaves dst without its copies.
func run(src, dst string) error {
	sources := map[string][]string{}
	for _, dir := range dirs {
		from := filepath.Join(src, dir)
		if fi, err := os.Stat(from); err != nil {
			return fmt.Errorf("reading sources: %w", err)
		} else if !fi.IsDir() {
			return fmt.Errorf("reading sources: %s is not a directory", from)
		}
		files, err := sourcefs.Files(os.DirFS(from))
		if err != nil {
			return fmt.Errorf("reading %s: %w", from, err)
		}
		if len(files) == 0 {
			return fmt.Errorf("no files in %s", from)
		}
		sources[dir] = files
	}

	stage, err := os.MkdirTemp(dst, ".gen-")
	if err != nil {
		return err
	}
	defer func() { _ = os.RemoveAll(stage) }()

	for _, dir := range dirs {
		from := os.DirFS(filepath.Join(src, dir))
		for _, f := range sources[dir] {
			data, err := fs.ReadFile(from, f)
			if err != nil {
				return err
			}
			out := filepath.Join(stage, dir, filepath.FromSlash(f))
			if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
				return err
			}
			if err := os.WriteFile(out, data, 0o644); err != nil {
				return err
			}
		}
	}

	for _, dir := range dirs {
		if err := swap(filepath.Join(stage, dir), filepath.Join(dst, dir)); err != nil {
			return err
		}
		fmt.Printf("gen: %d files -> %s\n", len(sources[dir]), filepath.Join(dst, dir))
	}
	return nil
}

// swap replaces dir with the staged copy, keeping the old one until the
// staged copy is in place.
func swap(staged, dir string) error {
	old := dir + ".old"
	if err := os.RemoveAll(old); err != nil {
		return err
	}
	if err := os.Rename(dir, old); err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	if err := os.Rename(staged, dir); err != nil {
		_ = os.Rename(old, dir) // put the previous copies back
		return err
	}
	return os.RemoveAll(old)
}
