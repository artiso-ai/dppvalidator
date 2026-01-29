# Windsurf Cascade Reference Guide

> Source: https://docs.windsurf.com/llms-full.txt

______________________________________________________________________

# Cascade Overview

Cascade is Windsurf's agentic AI assistant with Code/Chat modes, tool calling, voice input, checkpoints, real-time awareness, and linter integration.

**Open Cascade:** Press `Cmd/Ctrl+L` or click the Cascade icon. Any selected text in the editor or terminal will automatically be included.

## Cascade Code / Cascade Chat

- **Code mode**: Create and modify your codebase
- **Chat mode**: Optimized for questions (can propose code you can accept and insert)

## Plans and Todo Lists

Cascade has built-in planning capabilities:

- A specialized planning agent continuously refines the long-term plan
- Creates Todo lists to track progress on complex tasks
- Automatically updates plans as it picks up new information (like Memories)

## Queued Messages

Queue up new messages while Cascade is working:

- Press `Enter` again on empty text box to send immediately
- Delete any message from the queue before it's sent

## Tool Calling

Cascade has tools: Search, Analyze, Web Search, MCP, and terminal.

> Cascade can make up to 20 tool calls per prompt. If the trajectory stops, press `continue` (counts as new prompt credit).

Configure `Auto-Continue` to have Cascade automatically continue.

## Named Checkpoints and Reverts

- Hover over original prompt and click revert arrow to revert changes
- Create named snapshots/checkpoints of current project state

> **Warning**: Reverts are currently irreversible!

## Real-time Awareness

Cascade is aware of your real-time actions—no need to prompt with context on prior actions.

## Ignoring Files

Add files to `.codeiumignore` at workspace root. Declare paths in gitignore format.

**Global ignore**: Place `.codeiumignore` in `~/.codeium/` folder for all workspaces.

______________________________________________________________________

# AGENTS.md

Create `AGENTS.md` files to provide directory-scoped instructions to Cascade. Instructions automatically apply based on file location.

## How It Works

| File Location           | Scope                                                        |
| ----------------------- | ------------------------------------------------------------ |
| Workspace root          | Applies to all files (always on)                             |
| `/frontend/`            | Applies when working with files in `/frontend/**`            |
| `/frontend/components/` | Applies when working with files in `/frontend/components/**` |

## Creating an AGENTS.md File

Create `AGENTS.md` or `agents.md` in desired directory. Plain markdown, no frontmatter required.

### Example Structure

```
my-project/
├── AGENTS.md                    # Global instructions
├── frontend/
│   ├── AGENTS.md                # Frontend-specific
│   └── src/components/
│       └── AGENTS.md            # Components-specific
├── backend/
│   └── AGENTS.md                # Backend-specific
└── docs/
    └── AGENTS.md                # Documentation
```

### Example Content

```markdown
# Component Guidelines

When working with components in this directory:

- Use functional components with hooks
- Follow naming convention: ComponentName.tsx for components
- Each component should have ComponentName.test.tsx
- Use CSS modules: ComponentName.module.css
- Export as named exports, not default exports
```

## Best Practices

- Keep instructions focused on directory's purpose
- Use clear formatting (bullet points, headers, code blocks)
- Be specific with concrete examples
- Avoid redundancy—subdirectories inherit from parents

## AGENTS.md vs Rules

| Feature  | AGENTS.md                      | Rules                                            |
| -------- | ------------------------------ | ------------------------------------------------ |
| Location | In project directories         | `.windsurf/rules/` or global                     |
| Scoping  | Automatic based on location    | Manual (glob, always on, model decision, manual) |
| Format   | Plain markdown                 | Markdown with frontmatter                        |
| Best for | Directory-specific conventions | Cross-cutting concerns, complex activation logic |

______________________________________________________________________

# Memories & Rules

Persist context across Cascade conversations with auto-generated memories and user-defined rules.

## Memories

- Cascade automatically generates memories during conversation
- Ask Cascade to "create a memory of ..."
- Memories are workspace-specific
- Creating/using memories do NOT consume credits

## Rules

Define explicit rules for Cascade at global or workspace level:

- **`global_rules.md`** — Applied across all workspaces
- **`.windsurf/rules/`** — Workspace-level directory with rules tied to globs or descriptions

### Rules Discovery

- Current workspace and sub-directories
- Git repository structure (up to git root)
- Multiple workspace support (deduplicated)

### Rules Storage Locations

- `.windsurf/rules` in current workspace
- `.windsurf/rules` in any sub-directory
- `.windsurf/rules` in parent directories up to git root

### Activation Modes

| Mode               | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| **Manual**         | Activate via `@mention` in Cascade input                        |
| **Always On**      | Always applied                                                  |
| **Model Decision** | Model decides based on natural language description             |
| **Glob**           | Applied to files matching pattern (e.g., `*.js`, `src/**/*.ts`) |

### Best Practices

- Keep rules simple, concise, and specific
- Format using bullet points, numbered lists, markdown
- Use XML tags to group similar rules:

```markdown
<coding_guidelines>

- My project's programming language is python
- Use early returns when possible
- Always add documentation for new functions
  </coding_guidelines>
```

Rules files limited to **12000 characters** each.

______________________________________________________________________

# Skills

Skills help Cascade handle complex, multi-step tasks by bundling instructions, templates, and supporting files.

## How to Create a Skill

### Using the UI

1. Open Cascade panel → three dots → Customizations
1. Click `Skills` section
1. Click `+ Workspace` or `+ Global`
1. Name the skill (lowercase, numbers, hyphens only)

### Manual Creation

**Workspace Skill:**

```
.windsurf/skills/<skill-name>/SKILL.md
```

**Global Skill:**

```
~/.codeium/windsurf/skills/<skill-name>/SKILL.md
```

## SKILL.md Format

```markdown
---
name: deploy-to-production
description: Guides deployment process to production with safety checks
---

## Pre-deployment Checklist

1. Run all tests
2. Check for uncommitted changes
3. Verify environment variables

## Deployment Steps

Follow these steps to deploy safely...
```

### Required Frontmatter

- **name**: Unique identifier (used for @-mentions)
- **description**: Brief explanation for model to decide when to invoke

## Adding Supporting Resources

```
.windsurf/skills/deploy-to-production/
├── SKILL.md
├── deployment-checklist.md
├── rollback-procedure.md
└── config-template.yaml
```

## Invoking Skills

| Method        | Description                                            |
| ------------- | ------------------------------------------------------ |
| **Automatic** | Cascade invokes when request matches skill description |
| **Manual**    | Type `@skill-name` in Cascade input                    |

## Skill Scopes

| Scope     | Location                      | Availability           |
| --------- | ----------------------------- | ---------------------- |
| Workspace | `.windsurf/skills/`           | Current workspace only |
| Global    | `~/.codeium/windsurf/skills/` | All workspaces         |

______________________________________________________________________

# Workflows

Automate repetitive tasks with reusable workflows defined as markdown files.

## How It Works

Invoke workflows using `/[workflow-name]` command. Cascade sequentially processes each step.

> **Tip**: You can call other workflows from within a workflow! `/workflow-1` can include "Call /workflow-2"

## Creating a Workflow

1. Click `Customizations` icon → `Workflows` panel
1. Click `+ Workflow`

Workflows saved as markdown in `.windsurf/workflows/`

## Workflow Discovery

- `.windsurf/workflows/` in current workspace and sub-directories
- Parent directories up to git root (for git repos)
- Deduplicated across multiple workspaces

Workflow files limited to **12000 characters** each.

## Example Workflows

### /address-pr-comments

```markdown
1. Check out the PR branch: `gh pr checkout [id]`

2. Get comments on PR:
   gh api --paginate repos/[owner]/[repo]/pulls/[id]/comments | jq '...'

3. For EACH comment:
   a. Print: "(index). From [user] on [file]:[lines] — [body]"
   b. Analyze the file and line range
   c. If unclear, ask for clarification
   d. Make change BEFORE moving to next comment

4. Summarize what you did
```

Other use cases: `/git-workflows`, `/dependency-management`, `/code-formatting`, `/run-tests-and-fix`, `/deployment`, `/security-scan`

## System-Level Workflows (Enterprise)

| OS        | Location                                               |
| --------- | ------------------------------------------------------ |
| macOS     | `/Library/Application Support/Windsurf/workflows/*.md` |
| Linux/WSL | `/etc/windsurf/workflows/*.md`                         |
| Windows   | `C:\ProgramData\Windsurf\workflows\*.md`               |

### Workflow Precedence

1. **System** (highest) — Organization-wide
1. **Workspace** — Project-specific
1. **Global** — User-defined
1. **Built-in** — Default Windsurf workflows

______________________________________________________________________

# Model Context Protocol (MCP)

Integrate MCP servers with Cascade to access custom tools like GitHub, databases, and APIs.

## Adding a New MCP

1. Click `MCPs` icon in Cascade panel, or
1. `Windsurf Settings` > `Cascade` > `MCP Servers`

Supports three transport types: `stdio`, `Streamable HTTP`, `SSE`

Also supports OAuth for each transport type.

## mcp_config.json

Location: `~/.codeium/windsurf/mcp_config.json`

### Example Configuration (GitHub)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

### Remote HTTP MCPs

```json
{
  "mcpServers": {
    "remote-http-mcp": {
      "serverUrl": "<your-server-url>/mcp",
      "headers": {
        "API_KEY": "value"
      }
    }
  }
}
```

### Config Interpolation

Use environment variables: `"API_KEY": "Bearer ${env:AUTH_TOKEN}"`

## Configuring MCP Tools

Each MCP has tools. Cascade limit: **100 total tools** at any time.

Toggle tools on MCP settings page.

______________________________________________________________________

# Cascade Hooks

Execute custom shell commands at key points in Cascade's workflow.

## What You Can Build

- **Logging & Analytics**: Track file reads, code changes, commands
- **Security Controls**: Block sensitive file access, dangerous commands
- **Quality Assurance**: Run linters, formatters, tests after modifications
- **Custom Workflows**: Integrate with issue trackers, deployment pipelines
- **Team Standardization**: Enforce coding standards

## How Hooks Work

1. **Receives context** via JSON on stdin
1. **Executes your script** (Python, Bash, Node.js, etc.)
1. **Returns result** via exit code and output streams

**Pre-hooks** can **block actions** by exiting with code `2`.

## Configuration Locations

| Level                | Location                                           |
| -------------------- | -------------------------------------------------- |
| **System** (macOS)   | `/Library/Application Support/Windsurf/hooks.json` |
| **System** (Linux)   | `/etc/windsurf/hooks.json`                         |
| **System** (Windows) | `C:\ProgramData\Windsurf\hooks.json`               |
| **User**             | `~/.codeium/windsurf/hooks.json`                   |
| **Workspace**        | `.windsurf/hooks.json`                             |

Hooks from all locations are **merged**: system → user → workspace

### Basic Structure

```json
{
  "hooks": {
    "pre_read_code": [
      {
        "command": "python3 /path/to/script.py",
        "show_output": true
      }
    ],
    "post_write_code": [
      {
        "command": "python3 /path/to/another/script.py",
        "show_output": true
      }
    ]
  }
}
```

### Configuration Options

| Parameter           | Type    | Description                          |
| ------------------- | ------- | ------------------------------------ |
| `command`           | string  | Shell command to execute             |
| `show_output`       | boolean | Display stdout/stderr in Cascade UI  |
| `working_directory` | string  | Optional. Defaults to workspace root |

## Hook Events

| Event                   | Trigger                           | Can Block? |
| ----------------------- | --------------------------------- | ---------- |
| `pre_read_code`         | Before reading file               | ✓          |
| `post_read_code`        | After reading file                | ✗          |
| `pre_write_code`        | Before writing/modifying file     | ✓          |
| `post_write_code`       | After writing/modifying file      | ✗          |
| `pre_run_command`       | Before executing terminal command | ✓          |
| `post_run_command`      | After executing command           | ✗          |
| `pre_mcp_tool_use`      | Before invoking MCP tool          | ✓          |
| `post_mcp_tool_use`     | After MCP tool invocation         | ✗          |
| `pre_user_prompt`       | Before processing user prompt     | ✓          |
| `post_cascade_response` | After Cascade completes response  | ✗          |

### Common Input Structure

```json
{
  "agent_action_name": "pre_read_code",
  "trajectory_id": "unique-id",
  "execution_id": "unique-id",
  "timestamp": "ISO 8601",
  "tool_info": { ... }
}
```

## Exit Codes

| Code      | Meaning        | Effect                         |
| --------- | -------------- | ------------------------------ |
| `0`       | Success        | Action proceeds                |
| `2`       | Blocking Error | Pre-hooks **block** the action |
| Any other | Error          | Action proceeds                |

## Example: Restricting File Access

**hooks.json:**

```json
{
  "hooks": {
    "pre_read_code": [
      {
        "command": "python3 /path/to/block_read_access.py",
        "show_output": true
      }
    ]
  }
}
```

**block_read_access.py:**

```python
#!/usr/bin/env python3
import sys, json

ALLOWED_PREFIX = "/Users/yourname/my-project/"


def main():
    data = json.loads(sys.stdin.read())
    if data.get("agent_action_name") == "pre_read_code":
        file_path = data.get("tool_info", {}).get("file_path", "")
        if not file_path.startswith(ALLOWED_PREFIX):
            print(f"Access denied: Only {ALLOWED_PREFIX} allowed", file=sys.stderr)
            sys.exit(2)  # Block the action


if __name__ == "__main__":
    main()
```

## Example: Blocking Dangerous Commands

```python
#!/usr/bin/env python3
import sys, json

DANGEROUS_COMMANDS = ["rm -rf", "sudo rm", "format", "del /f"]


def main():
    data = json.loads(sys.stdin.read())
    if data.get("agent_action_name") == "pre_run_command":
        command = data.get("tool_info", {}).get("command_line", "")
        for dangerous_cmd in DANGEROUS_COMMANDS:
            if dangerous_cmd in command:
                print(f"Blocked: '{dangerous_cmd}' not allowed", file=sys.stderr)
                sys.exit(2)


if __name__ == "__main__":
    main()
```

______________________________________________________________________

# Quick Reference

## File Locations Summary

| Feature        | Workspace              | Global/User                           | System          |
| -------------- | ---------------------- | ------------------------------------- | --------------- |
| **AGENTS.md**  | Any directory          | N/A                                   | N/A             |
| **Rules**      | `.windsurf/rules/`     | `global_rules.md`                     | Enterprise only |
| **Skills**     | `.windsurf/skills/`    | `~/.codeium/windsurf/skills/`         | N/A             |
| **Workflows**  | `.windsurf/workflows/` | N/A                                   | OS-specific     |
| **Hooks**      | `.windsurf/hooks.json` | `~/.codeium/windsurf/hooks.json`      | OS-specific     |
| **MCP Config** | N/A                    | `~/.codeium/windsurf/mcp_config.json` | N/A             |
| **Ignore**     | `.codeiumignore`       | `~/.codeium/.codeiumignore`           | N/A             |

## Invocation Methods

| Feature       | Method                     |
| ------------- | -------------------------- |
| **Rules**     | `@rule-name` or automatic  |
| **Skills**    | `@skill-name` or automatic |
| **Workflows** | `/workflow-name`           |
| **MCP Tools** | Automatic when enabled     |
