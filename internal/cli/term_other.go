//go:build !linux && !darwin && !freebsd && !windows

package cli

// isTerminal is false on platforms without a known terminal check, so
// think-better never prompts there (pass flags instead).
func isTerminal(uintptr) bool { return false }
