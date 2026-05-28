#!/usr/bin/env python3
"""Alfred Run Script: open the selected note inside Obsidian."""

import os
import subprocess
import sys

from search import find_vault_containing_file, obsidian_uri


def read_target():
    if len(sys.argv) > 1:
        return sys.argv[1].strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main():
    target = read_target()
    if not target:
        return

    if target.startswith("obsidian:/open"):
        target = "obsidian://" + target[len("obsidian:/") :]
        subprocess.run(["open", target], check=False)
        return

    if target.startswith("obsidian://"):
        subprocess.run(["open", target], check=False)
        return

    if not os.path.isfile(target):
        return

    vault = find_vault_containing_file(target)
    if vault:
        uri = obsidian_uri(target, vault)
        subprocess.run(["open", uri], check=False)
        return

    subprocess.run(["open", "-a", "Obsidian", target], check=False)


if __name__ == "__main__":
    main()
