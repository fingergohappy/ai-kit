#!/usr/bin/env python3
"""Convert Claude-style markdown agents into Codex custom agent TOML files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE_ROOT = "plugins"
DEFAULT_OUTPUT_ROOT = "codex-agents"
DEFAULT_MODEL_MAP = {
    "haiku": "gpt-5.4-mini",
    "sonnet": "gpt-5.4",
    "opus": "gpt-5.4",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Claude-style markdown agents under plugins/*/agents/*.md "
            "into Codex custom agent TOML files."
        )
    )
    parser.add_argument(
        "--source-root",
        default=DEFAULT_SOURCE_ROOT,
        help="Root directory to scan for plugin agents (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_ROOT,
        help=(
            "Directory for generated Codex agent TOML files "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Convert only the named plugin. Repeat to include multiple plugins.",
    )
    parser.add_argument(
        "--map-claude-models",
        action="store_true",
        help=(
            "Map common Claude model aliases to Codex models "
            f"({', '.join(f'{k}={v}' for k, v in DEFAULT_MODEL_MAP.items())})."
        ),
    )
    parser.add_argument(
        "--model-map",
        action="append",
        default=[],
        metavar="SRC=DST",
        help="Add or override a model mapping. Repeat as needed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned outputs without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing generated TOML files.",
    )
    return parser.parse_args()


def parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown

    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, markdown

    metadata_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :]).lstrip()
    metadata: dict[str, str] = {}

    i = 0
    while i < len(metadata_lines):
        line = metadata_lines[i]
        if not line.strip() or ":" not in line:
            i += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value in {"|", ">"}:
            block: list[str] = []
            i += 1
            while i < len(metadata_lines):
                next_line = metadata_lines[i]
                if next_line.startswith(" ") or next_line.startswith("\t") or not next_line:
                    block.append(next_line[1:] if next_line.startswith(" ") else next_line)
                    i += 1
                    continue
                i -= 1
                break
            metadata[key] = "\n".join(block).rstrip()
        else:
            metadata[key] = strip_quotes(value)
        i += 1

    return metadata, body


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def discover_skill_names(plugin_root: Path) -> list[str]:
    for candidate in ("codex-skills", "skills"):
        skills_root = plugin_root / candidate
        if skills_root.is_dir():
            names = sorted(path.name for path in skills_root.iterdir() if path.is_dir())
            if names:
                return names
    return []


def namespace_skill_references(text: str, plugin_name: str, skill_names: Iterable[str]) -> str:
    converted = text
    for skill_name in sorted(skill_names, key=len, reverse=True):
        converted = re.sub(
            rf"`{re.escape(skill_name)}`",
            f"`{plugin_name}:{skill_name}`",
            converted,
        )
        converted = re.sub(
            rf"(?<![\w:-]){re.escape(skill_name)} skill(?![\w:-])",
            f"{plugin_name}:{skill_name} skill",
            converted,
        )
    return converted


def strip_redundant_heading(body: str, agent_name: str) -> str:
    lines = body.splitlines()
    if not lines:
        return body

    first = lines[0].strip().lower()
    normalized_name = agent_name.replace("-", " ").replace("_", " ").lower()
    if first.startswith("#") and normalized_name in first.lstrip("# ").strip():
        return "\n".join(lines[1:]).lstrip()
    return body


def build_model_map(args: argparse.Namespace) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if args.map_claude_models:
        mapping.update(DEFAULT_MODEL_MAP)
    for item in args.model_map:
        if "=" not in item:
            raise ValueError(f"Invalid --model-map value: {item!r}. Expected SRC=DST.")
        source, target = item.split("=", 1)
        source = source.strip()
        target = target.strip()
        if not source or not target:
            raise ValueError(f"Invalid --model-map value: {item!r}. Expected SRC=DST.")
        mapping[source] = target
    return mapping


def resolve_model(source_model: str | None, model_map: dict[str, str]) -> tuple[str | None, str | None]:
    if not source_model:
        return None, None

    normalized = source_model.strip()
    if not normalized or normalized == "inherit":
        return None, None

    if normalized in model_map:
        return model_map[normalized], None

    if normalized.startswith("gpt-") or normalized.startswith("o"):
        return normalized, None

    return None, normalized


def toml_basic_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    return f'"{escaped}"'


def toml_multiline_string(value: str) -> str:
    escaped = value.replace('"""', '\\"""')
    return f'"""\n{escaped}\n"""'


def build_toml(
    *,
    source_path: Path,
    agent_name: str,
    description: str,
    developer_instructions: str,
    resolved_model: str | None,
    unmapped_model: str | None,
) -> str:
    lines = [
        f"# Generated from {source_path.as_posix()}",
        "# Review before installing into ~/.codex/agents/ or a project-level .codex/agents/.",
        f"name = {toml_basic_string(agent_name)}",
        f"description = {toml_basic_string(description)}",
    ]
    if resolved_model:
        lines.append(f"model = {toml_basic_string(resolved_model)}")
    elif unmapped_model:
        lines.append(
            f"# Source model {toml_basic_string(unmapped_model)} was not mapped; "
            "add model = \"...\" manually if needed."
        )

    lines.append(f"developer_instructions = {toml_multiline_string(developer_instructions.rstrip())}")
    lines.append("")
    return "\n".join(lines)


def convert_agent(agent_path: Path, model_map: dict[str, str]) -> tuple[str, str]:
    plugin_root = agent_path.parents[1]
    plugin_name = plugin_root.name
    metadata, body = parse_frontmatter(agent_path.read_text())
    agent_name = metadata.get("name", agent_path.stem)
    description = metadata.get("description", "").strip()
    skill_names = discover_skill_names(plugin_root)
    body = namespace_skill_references(body, plugin_name, skill_names)
    body = strip_redundant_heading(body, agent_name)
    resolved_model, unmapped_model = resolve_model(metadata.get("model"), model_map)

    if metadata.get("tools"):
        tool_note = f"Source agent tools hint: {metadata['tools']}."
        if tool_note not in body:
            body = f"{tool_note}\n\n{body}".strip()

    return agent_name, build_toml(
        source_path=agent_path,
        agent_name=agent_name,
        description=description,
        developer_instructions=body,
        resolved_model=resolved_model,
        unmapped_model=unmapped_model,
    )


def iter_agent_paths(source_root: Path, plugins: set[str]) -> list[Path]:
    paths = sorted(source_root.glob("*/agents/*.md"))
    if plugins:
        paths = [path for path in paths if path.parents[1].name in plugins]
    return paths


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).resolve()
    output_root = Path(args.output).resolve()
    plugins = set(args.plugin)
    model_map = build_model_map(args)

    agent_paths = iter_agent_paths(source_root, plugins)
    if not agent_paths:
        print(f"No agent markdown files found under {source_root}.")
        return 1

    if not args.dry_run:
        output_root.mkdir(parents=True, exist_ok=True)

    generated = 0
    for agent_path in agent_paths:
        agent_name, toml_text = convert_agent(agent_path, model_map)
        output_path = output_root / f"{agent_name}.toml"

        if output_path.exists() and not args.force and not args.dry_run:
            raise FileExistsError(
                f"{output_path} already exists. Use --force to overwrite."
            )

        if args.dry_run:
            print(f"would_write:{output_path}")
            continue

        output_path.write_text(toml_text)
        print(f"wrote:{output_path}")
        generated += 1

    if args.dry_run:
        print(f"dry_run_complete:{len(agent_paths)}")
    else:
        print(f"generated:{generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
