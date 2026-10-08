package cli

import (
	"flag"
	"fmt"
	"io"
	"strings"
)

// promptAttempts is how often promptChoice asks again after an invalid answer.
const promptAttempts = 3

// shortFlags maps one-letter aliases to the flag they stand for; help lists
// them together ("-y, --yes").
var shortFlags = map[string]string{"y": "yes"}

// printFlagDefaults lists the flags of fs the way the docs write them
// ("--ai string" rather than the flag package's "-ai string").
func printFlagDefaults(w io.Writer, fs *flag.FlagSet) {
	fs.VisitAll(func(f *flag.Flag) {
		if long, ok := shortFlags[f.Name]; ok && fs.Lookup(long) != nil {
			return // listed with the long name
		}
		names := "--" + f.Name
		for short, long := range shortFlags {
			if long == f.Name && fs.Lookup(short) != nil {
				names = "-" + short + ", " + names
			}
		}
		valueName, usage := flag.UnquoteUsage(f)
		if valueName != "" {
			names += " " + valueName
		}
		_, _ = fmt.Fprintf(w, "  %s\n", names)
		_, _ = fmt.Fprintf(w, "    \t%s", strings.ReplaceAll(usage, "\n", "\n    \t"))
		switch f.DefValue {
		case "", "false", "0", "[]":
		default:
			_, _ = fmt.Fprintf(w, " (default %q)", f.DefValue)
		}
		_, _ = fmt.Fprintln(w)
	})
}

// addYesFlag registers --yes and its short form -y.
func addYesFlag(fs *flag.FlagSet, yes *bool, usage string) {
	fs.BoolVar(yes, "yes", false, usage)
	fs.BoolVar(yes, "y", false, "Same as --yes")
}

// listFlag is a flag that can be repeated and takes comma-separated values.
type listFlag []string

func (l *listFlag) String() string { return strings.Join(*l, ",") }

func (l *listFlag) Set(v string) error {
	for _, p := range strings.Split(v, ",") {
		if p = strings.TrimSpace(p); p != "" {
			*l = append(*l, p)
		}
	}
	return nil
}
