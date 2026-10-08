//go:build darwin || freebsd

package cli

import "syscall"

const ioctlReadTermios = syscall.TIOCGETA
