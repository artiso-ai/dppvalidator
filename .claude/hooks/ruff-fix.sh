#!/usr/bin/env bash
# PostToolUse hook: auto-fix Python files edited by Claude with ruff.
#
# Reads the Claude Code hook event JSON from stdin, extracts the file path
# of the Edit/Write/MultiEdit tool call, and runs `uv run ruff check --fix`
# on it. Silent on success; never blocks Claude (exit 0 always).

set -u

# Hook input is JSON on stdin per Claude Code hooks contract.
input="$(cat)"

# Extract file_path from tool_input. PostToolUse fires for Edit, Write,
# MultiEdit, NotebookEdit. Each surfaces the path as tool_input.file_path
# (or notebook_path for NotebookEdit).
file_path="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input", {}) or {}
path = ti.get("file_path") or ti.get("notebook_path") or ""
print(path)
' 2>/dev/null)"

# Bail if no path or not a Python file we manage.
case "$file_path" in
  *.py) ;;
  *)    exit 0 ;;
esac

# Only auto-fix files inside the project tree.
project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
case "$file_path" in
  "$project_dir"/*) ;;
  /*) exit 0 ;;
  *)  file_path="$project_dir/$file_path" ;;
esac

# Run ruff fix; never block, even on failure.
cd "$project_dir" || exit 0
uv run ruff check --fix "$file_path" >/dev/null 2>&1 || true

exit 0
