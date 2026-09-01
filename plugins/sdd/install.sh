#!/usr/bin/env bash
# 把 sdd 系列 skill 安装进一个项目, 三个工具的 skills 目录各放一份:
#   Claude Code  .claude/skills/<name>/SKILL.md   调用 /<name>
#   Codex        .agents/skills/<name>/SKILL.md   调用 $<name>
#   pi           .pi/skills/<name>/SKILL.md       按 pi 的 skill 调用方式
# 默认软链接 (改一处处处生效); --copy 拷贝 (要随仓库提交时用).
#
# 用法: install.sh [--copy] [项目根目录, 默认当前目录]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(sdd draft req create-cr spec implement-cr review-cr auto-cr)
MODE=link
ROOT="$PWD"
for a in "$@"; do
  case "$a" in
    --copy) MODE=copy ;;
    --link) MODE=link ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) ROOT="$(cd "$a" && pwd)" ;;
  esac
done

for dir in .claude/skills .agents/skills .pi/skills; do
  mkdir -p "$ROOT/$dir"
  for s in "${SKILLS[@]}"; do
    dst="$ROOT/$dir/$s"
    rm -rf "$dst"
    if [ "$MODE" = copy ]; then
      cp -R "$HERE/skills/$s" "$dst"
    else
      ln -s "$HERE/skills/$s" "$dst"
    fi
  done
  echo "已安装 ($MODE): $ROOT/$dir/{${SKILLS[*]// /,}}"
done

echo
echo "下一步:"
echo "  1. 初始化文档目录 (只需一次):  python3 $HERE/skills/sdd/scripts/sdd.py init --root $ROOT/docs/sdd   (只建目录与 INDEX, 约定在 sdd/references/conventions.md)"
echo "  2. 在 Claude Code 里试 /sdd, Codex 里 \$sdd, pi 里按其 skill 调用方式."
if [ "$MODE" = link ]; then
  echo "  注意: 软链接指向 $HERE, 别的机器 clone 后不会有; 要随仓库走请用 --copy."
fi
