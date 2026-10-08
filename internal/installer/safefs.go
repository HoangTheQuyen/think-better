package installer

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"strings"
)

// Every path think-better writes or deletes is given as a slash-separated
// path relative to a base directory (the project or the home directory).
// checkPath refuses paths that leave the base and paths that go through a
// symlink (or a Windows junction) anywhere below the base, so an install can
// never be redirected to write or delete files elsewhere. The base itself
// may be a symlink (e.g. a home directory on another volume).

// ErrUnsafePath is returned when a path goes through a symlink or leaves the base directory.
var ErrUnsafePath = errors.New("unsafe path")

// checkPath validates base/rel and returns the joined path. Components that
// do not exist yet are fine; existing ones must be real directories, and
// the final component, if it exists, must be a regular file or directory.
func checkPath(base, rel string) (string, error) {
	if !validRel(rel) {
		return "", fmt.Errorf("%w: %q is not inside %s", ErrUnsafePath, rel, base)
	}
	full := filepath.Join(base, filepath.FromSlash(rel))
	if r, err := filepath.Rel(base, full); err != nil || !filepath.IsLocal(r) {
		return "", fmt.Errorf("%w: %s is not inside %s", ErrUnsafePath, full, base)
	}

	parts := strings.Split(rel, "/")
	cur := base
	for i, p := range parts {
		cur = filepath.Join(cur, p)
		fi, err := os.Lstat(cur)
		if errors.Is(err, fs.ErrNotExist) {
			return full, nil // nothing below can exist either
		}
		if err != nil {
			return "", err
		}
		last := i == len(parts)-1
		switch {
		case fi.Mode()&fs.ModeSymlink != 0:
			return "", fmt.Errorf("%w: refusing to follow symlink %s", ErrUnsafePath, cur)
		case !last && !fi.IsDir():
			// Includes Windows junctions, which Lstat reports without ModeDir.
			return "", fmt.Errorf("%w: %s is not a plain directory (symlink, junction or file)", ErrUnsafePath, cur)
		case last && !fi.IsDir() && !isFileLike(fi.Mode()):
			return "", fmt.Errorf("%w: %s is not a regular file", ErrUnsafePath, cur)
		}
	}
	return full, nil
}

// isFileLike reports whether m is a regular file. On Windows, files with a
// non-link reparse point (e.g. OneDrive placeholders) are reported as
// ModeIrregular and count too: they hold data like regular files, and the
// final component is only ever replaced (renamed over) or removed, which
// never acts through a link. Directories with such reparse points keep
// ModeDir and are accepted as directories, while junctions (no ModeDir) are not.
func isFileLike(m fs.FileMode) bool {
	t := m.Type()
	return t == 0 || t == fs.ModeIrregular
}

// ensureDir creates base/rel (and parents) after checking no existing
// component is a symlink.
func ensureDir(base, rel string) error {
	full, err := checkPath(base, rel)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(full, 0o755); err != nil {
		return err
	}
	// Re-check: a component could have been swapped for a symlink meanwhile.
	_, err = checkPath(base, rel)
	return err
}

// writeFileSafe atomically writes data to base/rel with the given mode: the
// content goes to a temporary file in the same directory, which is then
// renamed over the target. The mode is applied even when the file existed.
func writeFileSafe(base, rel string, data []byte, mode os.FileMode) error {
	if err := ensureDir(base, path.Dir(rel)); err != nil {
		return err
	}
	full, err := checkPath(base, rel)
	if err != nil {
		return err
	}
	if fi, err := os.Lstat(full); err == nil && fi.IsDir() {
		return fmt.Errorf("cannot write %s: it is a directory", full)
	}

	tmp, err := os.CreateTemp(filepath.Dir(full), "."+filepath.Base(full)+".tmp-*")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer func() { _ = os.Remove(tmpName) }() // no-op after a successful rename

	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmpName, mode); err != nil {
		return err
	}
	return os.Rename(tmpName, full)
}

// setModeSafe sets the mode of an existing regular file base/rel.
func setModeSafe(base, rel string, mode os.FileMode) error {
	full, err := checkPath(base, rel)
	if err != nil {
		return err
	}
	fi, err := os.Lstat(full)
	if err != nil {
		return err
	}
	if fi.Mode().Perm() == mode.Perm() {
		return nil
	}
	return os.Chmod(full, mode)
}

// removeFileSafe deletes the regular file base/rel; a missing file is not an error.
func removeFileSafe(base, rel string) error {
	full, err := checkPath(base, rel)
	if err != nil {
		return err
	}
	fi, err := os.Lstat(full)
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if !isFileLike(fi.Mode()) {
		return fmt.Errorf("refusing to remove %s: not a regular file", full)
	}
	return os.Remove(full)
}

// removeEmptyDirs removes base/rel and then each parent directory while it
// is empty, stopping at stopRel (an ancestor of rel, "." for base), which is
// never removed. A directory that still has content or is a symlink stops
// the walk.
func removeEmptyDirs(base, rel, stopRel string) {
	for isBelow(rel, stopRel) {
		full, err := checkPath(base, rel)
		if err != nil {
			return
		}
		fi, err := os.Lstat(full)
		if err != nil || !fi.IsDir() {
			return
		}
		entries, err := os.ReadDir(full)
		if err != nil || len(entries) > 0 {
			return
		}
		if os.Remove(full) != nil {
			return
		}
		rel = path.Dir(rel)
	}
}

// isBelow reports whether slash path rel is strictly inside ancestor ("." is the base).
func isBelow(rel, ancestor string) bool {
	if rel == "." || rel == "" || rel == ancestor {
		return false
	}
	return ancestor == "." || strings.HasPrefix(rel, ancestor+"/")
}
