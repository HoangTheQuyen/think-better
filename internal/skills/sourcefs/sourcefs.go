// Package sourcefs lists the skill source files that belong in the binary,
// skipping caches and editor/OS junk. It is shared by the embed generator
// and the drift test so both agree on what "in sync" means.
package sourcefs

import (
	"io/fs"
	"path"
	"strings"
)

var ignoredDirs = map[string]bool{"__pycache__": true, ".pytest_cache": true}

var ignoredFiles = map[string]bool{".DS_Store": true, "Thumbs.db": true}

// Files returns all relevant file paths in fsys, slash-separated and sorted.
func Files(fsys fs.FS) ([]string, error) {
	var files []string
	err := fs.WalkDir(fsys, ".", func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		name := d.Name()
		if d.IsDir() {
			if ignoredDirs[name] {
				return fs.SkipDir
			}
			return nil
		}
		if ignoredFiles[name] || strings.HasSuffix(name, ".pyc") || path.Ext(name) == ".swp" {
			return nil
		}
		files = append(files, p)
		return nil
	})
	return files, err
}
