# DuoShe（夺舍）

[English](README.md)

`duo-she` 是一个同时兼容 Claude Code 和 Codex 的 AI Skill。

它会把模型切换成一个偏“执行接管”的教练角色：少一点空泛 brainstorming，多一点明确决策、可交付任务、真实复盘，以及在用户明确提出时提供持续盯进度的能力。

## 它能做什么

- 把模糊目标压缩成可验证、可衡量的结果
- 把工作拆成阶段计划、近期待办和当前任务
- 推动用户产出真实结果，而不是只给情绪价值
- 基于用户提交的证据做诚实复盘，并调整下一步
- 默认支持手动回报模式
- 在用户明确要求时支持 Codex 自动跟进、Telegram 和邮件催办

## 运行时兼容性

这个仓库同时面向两种运行时：

- Claude Code：使用 [`CLAUDE.md`](CLAUDE.md) 作为主要指令文件
- Codex：使用 [`SKILL.md`](SKILL.md) 和 [`agents/openai.yaml`](agents/openai.yaml) 进行 skill 发现和展示

两边行为刻意保持一致：

- 优先使用和运行时无关的能力，比如规划、研究、本地文件和脚本
- 只有在当前运行时真的支持时，才使用平台专属自动化能力
- 如果某个能力当前不可用，就明确说明并退回到最近似的可行方案

## 安装

### Codex

直接用 skill installer：

```text
Use $skill-installer to install https://github.com/hellomrleeus/duo-she
```

也可以手动从仓库安装：

```bash
git clone git@github.com:hellomrleeus/duo-she.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s /path/to/duo-she "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

更完整的 Codex 安装说明见 [`.codex/INSTALL.md`](.codex/INSTALL.md)。

### Claude Code

克隆仓库，并把它放到 Claude Code 可以读取指令文件的位置：

```bash
git clone git@github.com:hellomrleeus/duo-she.git
```

规范性的主指令文件是 [`CLAUDE.md`](CLAUDE.md)。

## 快速开始

示例提示词：

- `夺舍，我想在 30 天内把我的英语口语练到能完成一次模拟面试`
- `Use $duo-she to take over this goal and tell me exactly what to do this hour`
- `帮我把这个项目拆成未来 7 天的执行计划，然后只给我今天第一条任务`
- `每小时盯我一次，我做完回来给你看`

典型流程：

1. DuoShe 先锁定目标和约束条件
2. DuoShe 生成阶段性计划
3. DuoShe 下发当前任务
4. 用户带着证据回来汇报
5. DuoShe 复盘、调整并下发下一条任务

## 仓库结构

- [`CLAUDE.md`](CLAUDE.md)：Claude Code 使用的规范行为说明，也是这套指令的事实来源
- [`SKILL.md`](SKILL.md)：Codex 使用的 skill 入口，行为与 `CLAUDE.md` 对齐
- [`agents/openai.yaml`](agents/openai.yaml)：Codex UI 元数据
- [`references/task-map.md`](references/task-map.md)：持久化计划文件的结构说明
- [`references/telegram.md`](references/telegram.md)：Telegram 跟进流程
- [`references/email.md`](references/email.md)：邮件跟进流程
- [`references/follow-up-policy.md`](references/follow-up-policy.md)：提醒与升级节奏
- [`scripts/`](scripts/)：Telegram、邮件和 follow-up 相关的本地辅助脚本

## 持久化文件

当目标不是一句话就能完成时，DuoShe 可以在当前工作区生成：

- `duo-she-plan.md`
- `duo-she-state.json`

这些属于运行时数据，应该生成在当前工作目录，而不是 skill 自己的目录里。

## 可选跟进渠道

默认模式是手动回报。

如果用户明确要求持续跟进，DuoShe 可以使用：

- Codex 里的 automations
- 通过本地脚本接入的 Telegram
- 通过本地脚本接入的 Email

Telegram 和 Email 都需要一次性初始化以及本地凭据配置。

## 仓库地址

- GitHub：[hellomrleeus/duo-she](https://github.com/hellomrleeus/duo-she)
- Clone 地址：`git@github.com:hellomrleeus/duo-she.git`
