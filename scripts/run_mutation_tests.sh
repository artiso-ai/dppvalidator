#!/bin/bash
# Mutation Testing Script for dppvalidator
#
# This script runs mutation testing on the validators module
# to verify test quality.
#
# Usage:
#   ./scripts/run_mutation_tests.sh           # Run full mutation testing
#   ./scripts/run_mutation_tests.sh results   # Show results only
#   ./scripts/run_mutation_tests.sh show 1    # Show mutant #1

set -e

MUTANTS_DIR=".mutmut-cache"

case "${1:-run}" in
    run)
        echo "=============================================="
        echo "  dppvalidator Mutation Testing"
        echo "=============================================="
        echo ""
        echo "Running mutation tests on validators module..."
        echo "This may take several minutes."
        echo ""

        # Remove old cache if exists
        rm -rf "$MUTANTS_DIR" mutants/

        # Run mutmut
        uv run mutmut run || true

        echo ""
        echo "=============================================="
        echo "  Mutation Testing Results"
        echo "=============================================="
        uv run mutmut results || true
        ;;

    results)
        echo "Mutation Testing Results:"
        uv run mutmut results
        ;;

    show)
        if [ -z "$2" ]; then
            echo "Usage: $0 show <mutant_id>"
            exit 1
        fi
        uv run mutmut show "$2"
        ;;

    *)
        echo "Usage: $0 {run|results|show <id>}"
        exit 1
        ;;
esac
