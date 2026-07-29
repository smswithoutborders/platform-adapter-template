#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
#
# Fetches platform-adapter-template's files into a working directory,
# existing files are skipped (not overwritten) unless --force is given.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/smswithoutborders/platform-adapter-template/main/create-adapter.sh | bash -s -- [target-dir] [--force]
#   ./create-adapter.sh [target-dir] [--force]
#
# With no target-dir, files are fetched into the current directory.

set -euo pipefail

TEMPLATE_TARBALL="https://codeload.github.com/smswithoutborders/platform-adapter-template/tar.gz/refs/heads/main"

TARGET_DIR="."
FORCE=0
for arg in "$@"; do
  case "$arg" in
  --force) FORCE=1 ;;
  *) TARGET_DIR="$arg" ;;
  esac
done

for cmd in curl tar mktemp; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "error: '$cmd' is required but not installed" >&2
    exit 1
  }
done

mkdir -p "$TARGET_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Fetching template..."
curl -fsSL "$TEMPLATE_TARBALL" | tar -xz -C "$TMP_DIR" --strip-components=1

skipped=()
while IFS= read -r -d '' src; do
  rel="${src#"$TMP_DIR"/}"
  dest="$TARGET_DIR/$rel"
  if [ -e "$dest" ] && [ "$FORCE" -ne 1 ]; then
    skipped+=("$rel")
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
done < <(find "$TMP_DIR" -type f -print0)

if [ "${#skipped[@]}" -gt 0 ]; then
  echo "warning: skipped existing file(s), rerun with --force to overwrite:"
  printf '  %s\n' "${skipped[@]}"
fi

echo "Template files ready in $TARGET_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "note: git not found, skipping repo setup. Run 'git init' manually when ready."
  exit 0
fi

if [ -d "$TARGET_DIR/.git" ]; then
  echo "note: $TARGET_DIR is already a git repo, skipping git setup."
  exit 0
fi

if ! { : </dev/tty; } 2>/dev/null; then
  echo "note: no interactive terminal detected, skipping git setup."
  echo "Run 'git init' in $TARGET_DIR when ready, then add your remote."
  exit 0
fi

read -rp "Initialize a git repository in $TARGET_DIR? [y/N] " init_git </dev/tty
if [[ "$init_git" =~ ^[Yy]$ ]]; then
  git -C "$TARGET_DIR" init -q
  read -rp "Remote URL (leave blank to skip): " remote_url </dev/tty
  if [ -n "$remote_url" ]; then
    git -C "$TARGET_DIR" remote add origin "$remote_url"
    echo "Remote 'origin' set to $remote_url"
  fi
  echo "Git repo initialized in $TARGET_DIR"
else
  echo "Skipped git setup. Run 'git init' in $TARGET_DIR when ready."
fi
