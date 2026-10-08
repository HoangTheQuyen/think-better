// Package skills provides the skill registry and embedded file access.
package skills

import (
	"bufio"
	"fmt"
	"io/fs"
	"path"
	"sort"
	"strings"
)

// SkillPackage represents a self-contained collection of files that form an AI assistant skill.
type SkillPackage struct {
	Name         string   // Unique identifier, equal to the directory name (e.g., "make-decision")
	Description  string   // Short human-readable summary shown in list output
	Dependencies []string // Runtime requirements (e.g., ["python3"])
}

// Registry contains all bundled skills, discovered from the embedded skills/
// directory. Each skill is a directory with a SKILL.md whose YAML frontmatter
// declares `name` (must match the directory) and `description`.
var Registry, discoveryErrors = discover(Content)

// FindSkill returns the skill with the given name (case-insensitive), or nil if not found.
func FindSkill(name string) *SkillPackage {
	lower := strings.ToLower(name)
	for i := range Registry {
		if Registry[i].Name == lower {
			return &Registry[i]
		}
	}
	return nil
}

// SkillNames returns the names of all registered skills.
func SkillNames() []string {
	names := make([]string, len(Registry))
	for i, s := range Registry {
		names[i] = s.Name
	}
	return names
}

// discover builds the registry from fsys/skills/*/SKILL.md. Invalid skills
// are skipped and reported as errors so a bad contribution fails tests and
// `ValidateEmbedded` instead of panicking at startup.
func discover(fsys fs.FS) ([]SkillPackage, []string) {
	entries, err := fs.ReadDir(fsys, "skills")
	if err != nil {
		return nil, []string{fmt.Sprintf("reading skills: %v", err)}
	}

	var pkgs []SkillPackage
	var errs []string
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := path.Join("skills", e.Name())
		pkg, err := loadSkill(fsys, dir, e.Name())
		if err != nil {
			errs = append(errs, err.Error())
			continue
		}
		pkgs = append(pkgs, pkg)
	}
	sort.Slice(pkgs, func(i, j int) bool { return pkgs[i].Name < pkgs[j].Name })
	return pkgs, errs
}

func loadSkill(fsys fs.FS, dir, dirName string) (SkillPackage, error) {
	data, err := fs.ReadFile(fsys, path.Join(dir, "SKILL.md"))
	if err != nil {
		return SkillPackage{}, fmt.Errorf("%s: missing SKILL.md", dirName)
	}
	meta, err := ParseFrontmatter(string(data))
	if err != nil {
		return SkillPackage{}, fmt.Errorf("%s/SKILL.md: %w", dirName, err)
	}
	if meta["name"] != dirName {
		return SkillPackage{}, fmt.Errorf("%s/SKILL.md: frontmatter name %q must match directory name", dirName, meta["name"])
	}
	if meta["description"] == "" {
		return SkillPackage{}, fmt.Errorf("%s/SKILL.md: frontmatter description is required", dirName)
	}

	pkg := SkillPackage{Name: dirName, Description: summary(meta["description"])}
	if scripts, _ := fs.Glob(fsys, path.Join(dir, "scripts", "*.py")); len(scripts) > 0 {
		pkg.Dependencies = []string{"python3"}
	}
	return pkg, nil
}

// ParseFrontmatter extracts top-level scalar keys from a `---` delimited YAML
// frontmatter block. It supports `key: value` and block scalars (`key: |` or
// `key: >`) followed by indented lines, which is all SKILL.md files use.
func ParseFrontmatter(doc string) (map[string]string, error) {
	sc := bufio.NewScanner(strings.NewReader(doc))
	if !sc.Scan() || strings.TrimSpace(sc.Text()) != "---" {
		return nil, fmt.Errorf("frontmatter must start with '---' on the first line")
	}

	meta := map[string]string{}
	var key string
	var block []string
	flush := func() {
		if key != "" && block != nil {
			meta[key] = strings.Join(block, " ")
		}
		key, block = "", nil
	}
	for sc.Scan() {
		line := sc.Text()
		if strings.TrimSpace(line) == "---" {
			flush()
			return meta, nil
		}
		if block != nil && (strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t") || strings.TrimSpace(line) == "") {
			if t := strings.TrimSpace(line); t != "" {
				block = append(block, t)
			}
			continue
		}
		flush()
		k, v, ok := strings.Cut(line, ":")
		if !ok || strings.HasPrefix(line, " ") {
			continue
		}
		k, v = strings.TrimSpace(k), strings.TrimSpace(v)
		if v == "|" || v == ">" || v == "|-" || v == ">-" {
			key, block = k, []string{}
			continue
		}
		meta[k] = strings.Trim(v, `"'`)
	}
	return nil, fmt.Errorf("frontmatter is not closed with '---'")
}

// summary returns the first sentence of a skill description, which by
// convention is the short summary; the rest lists trigger phrases.
func summary(desc string) string {
	if i := strings.Index(desc, ". "); i >= 0 {
		return desc[:i+1]
	}
	return desc
}
