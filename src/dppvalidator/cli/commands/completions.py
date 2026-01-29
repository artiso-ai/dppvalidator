"""Shell completion generation for dppvalidator CLI."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import _SubParsersAction

BASH_COMPLETION = """# dppvalidator bash completion
# Add to ~/.bashrc: eval "$(dppvalidator completions bash)"

_dppvalidator_completions() {
    local cur prev words cword
    _init_completion || return

    local commands="validate export schema completions"
    local validate_opts="--strict --format --fail-fast --max-errors --help"
    local export_opts="--output --format --indent --help"
    local schema_opts="--version --help"
    local completions_opts="--help"
    local formats_validate="text json table"
    local formats_export="jsonld json"
    local shells="bash zsh fish"

    case "${prev}" in
        dppvalidator)
            COMPREPLY=($(compgen -W "${commands} --version --help --quiet --verbose" -- "${cur}"))
            return
            ;;
        validate)
            if [[ "${cur}" == -* ]]; then
                COMPREPLY=($(compgen -W "${validate_opts}" -- "${cur}"))
            else
                COMPREPLY=($(compgen -f -- "${cur}"))
            fi
            return
            ;;
        export)
            if [[ "${cur}" == -* ]]; then
                COMPREPLY=($(compgen -W "${export_opts}" -- "${cur}"))
            else
                COMPREPLY=($(compgen -f -- "${cur}"))
            fi
            return
            ;;
        schema)
            COMPREPLY=($(compgen -W "list info download ${schema_opts}" -- "${cur}"))
            return
            ;;
        completions)
            COMPREPLY=($(compgen -W "${shells}" -- "${cur}"))
            return
            ;;
        --format|-f)
            case "${words[1]}" in
                validate)
                    COMPREPLY=($(compgen -W "${formats_validate}" -- "${cur}"))
                    ;;
                export)
                    COMPREPLY=($(compgen -W "${formats_export}" -- "${cur}"))
                    ;;
            esac
            return
            ;;
        --output|-o)
            COMPREPLY=($(compgen -f -- "${cur}"))
            return
            ;;
        --version)
            COMPREPLY=($(compgen -W "0.6.0 0.6.1" -- "${cur}"))
            return
            ;;
    esac

    if [[ "${cur}" == -* ]]; then
        case "${words[1]}" in
            validate)
                COMPREPLY=($(compgen -W "${validate_opts}" -- "${cur}"))
                ;;
            export)
                COMPREPLY=($(compgen -W "${export_opts}" -- "${cur}"))
                ;;
            schema)
                COMPREPLY=($(compgen -W "${schema_opts}" -- "${cur}"))
                ;;
            *)
                COMPREPLY=($(compgen -W "--help" -- "${cur}"))
                ;;
        esac
    else
        COMPREPLY=($(compgen -f -- "${cur}"))
    fi
}

complete -F _dppvalidator_completions dppvalidator
"""

ZSH_COMPLETION = """#compdef dppvalidator
# dppvalidator zsh completion
# Add to ~/.zshrc: eval "$(dppvalidator completions zsh)"

_dppvalidator() {
    local -a commands
    local -a validate_opts export_opts schema_opts

    commands=(
        'validate:Validate a Digital Product Passport'
        'export:Export a DPP to JSON-LD or JSON'
        'schema:Manage DPP schemas'
        'completions:Generate shell completions'
    )

    validate_opts=(
        '--strict[Treat warnings as errors]'
        '--format[Output format (text, json, table)]:format:(text json table)'
        '--fail-fast[Stop on first error]'
        '--max-errors[Maximum errors to report]:count:'
        '--help[Show help]'
    )

    export_opts=(
        '--output[Output file path]:file:_files'
        '--format[Export format]:format:(jsonld json)'
        '--indent[JSON indentation]:indent:'
        '--help[Show help]'
    )

    schema_opts=(
        '--version[Schema version]:version:(0.6.0 0.6.1)'
        '--help[Show help]'
    )

    _arguments -C \\
        '-V[Show version]' \\
        '--version[Show version]' \\
        '-q[Quiet mode]' \\
        '--quiet[Quiet mode]' \\
        '-v[Verbose mode]' \\
        '--verbose[Verbose mode]' \\
        '1:command:->command' \\
        '*::arg:->args'

    case $state in
        command)
            _describe -t commands 'dppvalidator command' commands
            ;;
        args)
            case $words[1] in
                validate)
                    _arguments \\
                        $validate_opts \\
                        '*:file:_files -g "*.json *.jsonld"'
                    ;;
                export)
                    _arguments \\
                        $export_opts \\
                        '*:file:_files -g "*.json *.jsonld"'
                    ;;
                schema)
                    local -a schema_commands
                    schema_commands=(
                        'list:List available schemas'
                        'info:Show schema information'
                        'download:Download a schema'
                    )
                    _arguments \\
                        '1:schema command:->schema_cmd' \\
                        $schema_opts
                    case $state in
                        schema_cmd)
                            _describe -t commands 'schema command' schema_commands
                            ;;
                    esac
                    ;;
                completions)
                    _arguments '1:shell:(bash zsh fish)'
                    ;;
            esac
            ;;
    esac
}

_dppvalidator "$@"
"""

FISH_COMPLETION = """# dppvalidator fish completion
# Add to ~/.config/fish/completions/dppvalidator.fish

# Disable file completions for commands
complete -c dppvalidator -f

# Main commands
complete -c dppvalidator -n "__fish_use_subcommand" -a validate -d "Validate a Digital Product Passport"
complete -c dppvalidator -n "__fish_use_subcommand" -a export -d "Export a DPP to JSON-LD or JSON"
complete -c dppvalidator -n "__fish_use_subcommand" -a schema -d "Manage DPP schemas"
complete -c dppvalidator -n "__fish_use_subcommand" -a completions -d "Generate shell completions"

# Global options
complete -c dppvalidator -s V -l version -d "Show version"
complete -c dppvalidator -s q -l quiet -d "Suppress non-essential output"
complete -c dppvalidator -s v -l verbose -d "Enable verbose output"
complete -c dppvalidator -s h -l help -d "Show help"

# validate options
complete -c dppvalidator -n "__fish_seen_subcommand_from validate" -l strict -d "Treat warnings as errors"
complete -c dppvalidator -n "__fish_seen_subcommand_from validate" -l format -d "Output format" -xa "text json table"
complete -c dppvalidator -n "__fish_seen_subcommand_from validate" -l fail-fast -d "Stop on first error"
complete -c dppvalidator -n "__fish_seen_subcommand_from validate" -l max-errors -d "Maximum errors to report"
complete -c dppvalidator -n "__fish_seen_subcommand_from validate" -F

# export options
complete -c dppvalidator -n "__fish_seen_subcommand_from export" -s o -l output -d "Output file path" -rF
complete -c dppvalidator -n "__fish_seen_subcommand_from export" -l format -d "Export format" -xa "jsonld json"
complete -c dppvalidator -n "__fish_seen_subcommand_from export" -l indent -d "JSON indentation"
complete -c dppvalidator -n "__fish_seen_subcommand_from export" -F

# schema subcommands
complete -c dppvalidator -n "__fish_seen_subcommand_from schema; and not __fish_seen_subcommand_from list info download" -a list -d "List available schemas"
complete -c dppvalidator -n "__fish_seen_subcommand_from schema; and not __fish_seen_subcommand_from list info download" -a info -d "Show schema information"
complete -c dppvalidator -n "__fish_seen_subcommand_from schema; and not __fish_seen_subcommand_from list info download" -a download -d "Download a schema"
complete -c dppvalidator -n "__fish_seen_subcommand_from schema" -l version -d "Schema version" -xa "0.6.0 0.6.1"

# completions options
complete -c dppvalidator -n "__fish_seen_subcommand_from completions" -a "bash zsh fish" -d "Shell type"
"""


def add_parser(subparsers: _SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add completions subparser."""
    parser = subparsers.add_parser(
        "completions",
        help="Generate shell completions",
        description="Generate shell completion scripts for bash, zsh, or fish",
        epilog="""
Examples:
  # Bash (add to ~/.bashrc)
  eval "$(dppvalidator completions bash)"

  # Zsh (add to ~/.zshrc)
  eval "$(dppvalidator completions zsh)"

  # Fish (save to completions directory)
  dppvalidator completions fish > ~/.config/fish/completions/dppvalidator.fish
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "shell",
        choices=["bash", "zsh", "fish"],
        help="Shell type for completions",
    )


def run(args: argparse.Namespace) -> int:
    """Run the completions command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (always 0 on success)

    Note:
        This command intentionally uses print() instead of Console
        because shell completions must output raw text without formatting.
    """
    completions = {
        "bash": BASH_COMPLETION,
        "zsh": ZSH_COMPLETION,
        "fish": FISH_COMPLETION,
    }

    shell = args.shell
    if shell not in completions:
        print(f"Unknown shell: {shell}", file=sys.stderr)
        return 2

    print(completions[shell])
    return 0
