# Codex AI Install Runbook

这份文档写给 AI 执行，不写给人读。

目标：

1. 安装 `ai-kit` 仓库中的全部插件
2. 安装本仓库提供的 custom agents
3. 通过 Codex 插件安装暴露插件内置 skills

不要安装到项目级 `.codex/agents/`。  
统一使用个人目录：

- `~/.codex/plugins/`
- `~/.agents/plugins/marketplace.json`
- `~/.codex/agents/`

官方依据：

- <https://developers.openai.com/codex/plugins>
- <https://developers.openai.com/codex/plugins/build>
- <https://developers.openai.com/codex/subagents>
- <https://developers.openai.com/codex/skills>

## 安装

按顺序执行下面操作。

### 1. 克隆或更新仓库

```bash
if [ -d ~/.codex/plugins/ai-kit-repo/.git ]; then
  git -C ~/.codex/plugins/ai-kit-repo pull --ff-only
else
  git clone https://github.com/fingergohappy/ai-kit.git ~/.codex/plugins/ai-kit-repo
fi
```

### 2. 执行安装脚本

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_plugins.sh
```

这个脚本会做这些事：

1. 动态扫描 `plugins/*/.codex-plugin/plugin.json`
2. 同步插件目录到 `~/.codex/plugins/`
3. 创建或更新 `~/.agents/plugins/marketplace.json`
4. 生成 custom agents 到 `~/.codex/agents/`

官方规则要点：

- 个人 marketplace 文件使用 `~/.agents/plugins/marketplace.json`
- 个人本地插件通常放在 `~/.codex/plugins/`
- `source.path` 必须相对 marketplace root，使用 `./` 开头，并保持在该 root 内
- 本地 plugin entry 需要 `policy.installation`、`policy.authentication`、`category`

如果只想同步插件和 marketplace，不想安装 custom agents 或 skill symlink，执行：

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_plugins.sh --no-agents
```

默认不写 `~/.agents/skills/`。如果明确想把插件 skills 同时暴露为用户级 symlink，执行：

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_plugins.sh --link-skills
```

注意：

- `--link-skills` 会用 `ln -sfn` 重建同名 symlink
- 如果 `~/.agents/skills/<skill-name>` 是真实目录，不是 symlink，安装前先人工确认，不要直接覆盖
- Codex 支持 symlinked skill folders，会跟随 symlink target 扫描

### 3. 提示用户完成 Codex 内操作

执行完上面命令后，告诉用户：

1. 重启 Codex
2. 运行 `list skills` 或 `/skills` 检查本地 skills 是否出现
3. 打开 Codex CLI plugin directory：

```text
codex
/plugins
```

4. 在 `ai-kit` marketplace 中安装或启用全部展示的插件

注意：

- `list skills`、`/skills`、`$skill-name` 主要依赖 skill 扫描目录
- `@plugin` 入口和 Plugins UI 依赖插件 marketplace 安装状态
- 插件内置 skills 与本地 user skills 是两条链路；默认使用插件内置 skills

## 更新

更新仓库、同步插件，并刷新 custom agents：

```bash
git -C ~/.codex/plugins/ai-kit-repo pull --ff-only

cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_plugins.sh
```

如果之前明确使用了用户级 skill symlink，并且想同步更新 symlink 目标：

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_plugins.sh --link-skills
```

然后告诉用户：

1. 重启 Codex
2. 在 Plugins UI 中安装或启用全部插件
3. 用 `list skills` 或 `/skills` 确认 skill 是否可见
4. 如果 plugin 内容还是旧的，在 Plugins UI 中禁用并重新启用全部插件
5. 如果还不生效，卸载后重新安装全部插件
