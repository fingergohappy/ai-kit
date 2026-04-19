# Codex AI Install Runbook

这份文档写给 AI 执行，不写给人读。

目标：

1. 个人安装 `ai-kit` 的 Codex 插件
2. 安装本仓库提供的 custom agents
3. 让 `list skills` 能直接看到 `spec-*` / `tmux-send` / `commit` 等 skills

不要安装到项目级 `.codex/agents/`。  
统一使用个人目录：

- `~/.codex/plugins/`
- `~/.agents/plugins/marketplace.json`
- `~/.codex/agents/`
- `~/.agents/skills/`

官方依据：

- <https://developers.openai.com/codex/plugins/build>
- <https://developers.openai.com/codex/subagents>
- <https://developers.openai.com/codex/skills>

## 安装

按顺序执行下面操作。

### 1. 准备目录

```bash
mkdir -p ~/.codex/plugins ~/.codex/agents ~/.agents/plugins ~/.agents/skills
```

### 2. 克隆或更新仓库

```bash
if [ -d ~/.codex/plugins/ai-kit-repo/.git ]; then
  git -C ~/.codex/plugins/ai-kit-repo pull --ff-only
else
  git clone https://github.com/fingergohappy/ai-kit.git ~/.codex/plugins/ai-kit-repo
fi
```

### 3. 同步插件目录

```bash
rm -rf ~/.codex/plugins/spec-workflow ~/.codex/plugins/tmux ~/.codex/plugins/git
cp -R ~/.codex/plugins/ai-kit-repo/plugins/spec-workflow ~/.codex/plugins/spec-workflow
cp -R ~/.codex/plugins/ai-kit-repo/plugins/tmux ~/.codex/plugins/tmux
cp -R ~/.codex/plugins/ai-kit-repo/plugins/git ~/.codex/plugins/git
```

### 4. 合并个人 marketplace 配置

执行下面脚本。它会创建或更新 `~/.agents/plugins/marketplace.json`，保留其他已有插件条目，只替换 `spec-workflow`、`tmux`、`git` 这三个条目。

```bash
python3 - <<'PY'
from pathlib import Path
import json

path = Path.home() / ".agents" / "plugins" / "marketplace.json"
path.parent.mkdir(parents=True, exist_ok=True)

payload = {
    "name": "ai-kit",
    "interface": {
        "displayName": "ai-kit",
    },
    "plugins": [],
}

if path.exists():
    with path.open() as f:
        payload = json.load(f)

payload.setdefault("name", "ai-kit")
payload.setdefault("interface", {})
payload["interface"].setdefault("displayName", "ai-kit")
payload.setdefault("plugins", [])

entries = [
    {
        "name": "spec-workflow",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/spec-workflow",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    },
    {
        "name": "tmux",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/tmux",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Developer Tools",
    },
    {
        "name": "git",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/git",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Coding",
    },
]

existing = []
seen = {entry["name"] for entry in entries}
for item in payload["plugins"]:
    if isinstance(item, dict) and item.get("name") not in seen:
        existing.append(item)

payload["plugins"] = existing + entries

with path.open("w") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")

print(path)
PY
```

### 5. 安装 custom agents，并把 plugin skills 暴露到 `~/.agents/skills/`

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_agents.sh
```

这个脚本现在会同时做两件事：

1. 生成 custom agents 到 `~/.codex/agents/`
2. 为 `plugins/*/skills/*` 在 `~/.agents/skills/` 下创建同名 symlink

这样即使你还没在 Codex 的 Plugins 面板里真正点安装，`list skills` 也能直接看到：

- `spec-feature`
- `spec-change`
- `spec-implement`
- `spec-review`
- `spec-feedback`
- `spec-handle-feedback`
- `spec-check-review`
- `spec-fix-review`
- `tmux-send`
- `commit`
- `rebase-to-root`

### 6. 提示用户完成 Codex 内操作

执行完上面命令后，告诉用户：

1. 重启 Codex
2. 先运行 `list skills` 检查 skills 是否已出现
3. 如果需要使用 Codex 的 Plugins 目录、`@plugin` 入口或插件安装界面，再在插件目录里启用或安装：
   - `spec-workflow`
   - `tmux`
   - `git`

注意：

- `list skills` / `$skill-name` 依赖的是 `~/.agents/skills/`
- 插件目录里的 install/enable 影响的是 Codex Plugins UI 里的插件状态
- 这两条链路是相关但不等价的；前者更直接决定当前会话里能不能看到 skill

## 更新

更新时执行：

```bash
git -C ~/.codex/plugins/ai-kit-repo pull --ff-only
rm -rf ~/.codex/plugins/spec-workflow ~/.codex/plugins/tmux ~/.codex/plugins/git
cp -R ~/.codex/plugins/ai-kit-repo/plugins/spec-workflow ~/.codex/plugins/spec-workflow
cp -R ~/.codex/plugins/ai-kit-repo/plugins/tmux ~/.codex/plugins/tmux
cp -R ~/.codex/plugins/ai-kit-repo/plugins/git ~/.codex/plugins/git
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_agents.sh
```

然后告诉用户：

1. 重启 Codex
2. 先用 `list skills` 确认 `spec-feature` 等 skill 已刷新
3. 如果插件内容还是旧的，禁用并重新启用对应插件
4. 如果还不生效，卸载后重新安装对应插件

## 验证

执行：

```bash
test -f ~/.agents/plugins/marketplace.json
test -f ~/.codex/plugins/spec-workflow/.codex-plugin/plugin.json
test -f ~/.codex/plugins/tmux/.codex-plugin/plugin.json
test -f ~/.codex/plugins/git/.codex-plugin/plugin.json
test -f ~/.codex/agents/git-operator.toml
test -f ~/.codex/agents/tmux-operator.toml
test -L ~/.agents/skills/spec-feature
test -L ~/.agents/skills/tmux-send
test -L ~/.agents/skills/commit
```

安装完成后：

- `list skills` 应该能看到 `spec-feature` / `tmux-send` / `commit` 等 skill
- prompt 中可直接显式调用：
  - `$spec-feature`
  - `$spec-review`
  - `$tmux-send`
  - `$commit`
- 如果插件也在 Codex Plugins UI 中完成了 install/enable，则插件命名空间应为：
  - `spec-workflow:*`
  - `tmux:*`
  - `git:*`
