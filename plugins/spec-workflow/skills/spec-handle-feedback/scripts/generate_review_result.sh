#!/usr/bin/env bash
# generate_review_result.sh - Generate formatted review result from template
# Usage:
#   generate_review_result.sh --status <通过|需要修复> --round <N> --issues-file <path> [--suggestions-file <path>]
#
# issues-file: one issue per line, e.g. "[CRITICAL] 问题描述 → 修复建议"
# suggestions-file: optional, free-form text for suggestions section
#
# Output: formatted review result written to a temp file, path printed to stdout

set -euo pipefail

STATUS=""
ROUND=""
ISSUES_FILE=""
SUGGESTIONS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status)           STATUS="$2";           shift 2 ;;
    --round)            ROUND="$2";            shift 2 ;;
    --issues-file)      ISSUES_FILE="$2";      shift 2 ;;
    --suggestions-file) SUGGESTIONS_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$STATUS" ]]      && { echo "Error: --status required (通过|需要修复)" >&2; exit 1; }
[[ -z "$ROUND" ]]       && { echo "Error: --round required" >&2; exit 1; }
[[ -z "$ISSUES_FILE" ]] && { echo "Error: --issues-file required" >&2; exit 1; }
[[ ! -f "$ISSUES_FILE" ]] && { echo "Error: issues file not found: $ISSUES_FILE" >&2; exit 1; }

OUTFILE=$(mktemp /tmp/spec-review-result.XXXXXX)

{
  echo "## 审查结果"
  echo ""
  echo "- 状态: ${STATUS}"
  echo "- 修复轮次: ${ROUND}"
  echo ""
  echo "### 问题列表"
  echo ""
  cat "$ISSUES_FILE"
  echo ""
  echo "### 建议"
  echo ""
  if [[ -n "$SUGGESTIONS_FILE" ]] && [[ -f "$SUGGESTIONS_FILE" ]]; then
    cat "$SUGGESTIONS_FILE"
  else
    echo "无"
  fi
} > "$OUTFILE"

echo "$OUTFILE"
