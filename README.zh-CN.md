# DuoShe（夺舍）

[English](README.md)

`duo-she` 是一个同时兼容 Claude Code 和 Codex 的 AI Skill。

它会把模型切换成一个偏“执行接管”的教练角色：少一点空泛 brainstorming，多一点明确决策、可交付任务、真实复盘，以及在用户明确提出时提供持续盯进度的能力。

运行约束：skill 自身文件默认视为只读。DuoShe 产生的项目状态、通道配置、token、邮箱信息、提醒状态和 dashboard 都统一写到当前项目的 `.duo-she/` 目录里。

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

## 实际运行方式

DuoShe 的标准闭环是：

1. 先锁定目标、约束、截止时间和时间预算
2. 再拆成阶段计划、近期待办和当前任务
3. 给用户一条带交付物和验收标准的明确任务
4. 要求用户按时带证据回来
5. 把结果归类成 `done`、`partial`、`blocked` 或 `reschedule`
6. 更新保存状态并下发下一条任务

如果用户一开始就把上下文说得很完整，DuoShe 可以走 fast path：跳过冗长问诊，直接锁定目标并下发第一条任务。

## 推荐回复格式

推荐用户这样回：

- `done + evidence`
- `partial + evidence`
- `blocked + blocker`
- `reschedule + new time`

自由格式回复仍然可以工作，但结构化回复更利于自动适配和提醒节奏控制。

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

如果要初始化 Telegram 或 Email，请从项目根目录执行 setup 脚本，这样配置才会落到 `.duo-she/`。

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

- `.duo-she/duo-she-plan.md`
- `.duo-she/duo-she-state.json`
- `.duo-she/<channel>-state.json`
- `.duo-she/telegram.json`
- `.duo-she/email.json`

它们的职责分别是：

- `.duo-she/duo-she-plan.md`：给人看的清单和时间线
- `.duo-she/duo-she-state.json`：保存阶段、任务、复盘、阻塞和总进度
- `.duo-she/<channel>-state.json`：保存 Telegram、Email 或自动提醒的发送状态与提醒计数
- `.duo-she/telegram.json` 和 `.duo-she/email.json`：保存项目本地的消息通路配置、token 和邮箱信息

这些属于运行时数据，应该统一放在当前项目目录下的 `.duo-she/` 中，而不是 skill 自己的目录里。

## 可选跟进渠道

默认模式是手动回报。

如果用户明确要求持续跟进，DuoShe 可以使用：

- Codex 里的 automations
- 通过内置 orchestrator `scripts/run_telegram_followup.py` 接入的 Telegram
- 通过内置 orchestrator `scripts/run_email_followup.py` 接入的 Email

Telegram 和 Email 都需要一次性初始化以及本地凭据配置。

提醒节奏默认带静默时段：

- 默认 quiet hours：`22:00-08:00`
- 默认 workday end：`22:00`
- 如果任务跨夜未回，第二天早上的第一条提醒应该是 reset，而不是继续追发过期的 urgent

## 维护说明

`CLAUDE.md` 是唯一的规范源文件。

修改它之后，用下面的命令重建 `SKILL.md`：

```bash
python3 scripts/sync_skill.py
```

如果只想检查同步状态而不改文件，可以运行：

```bash
python3 scripts/sync_skill.py --check
```

仓库里的 GitHub Actions 也会自动做这项检查。

## 仓库地址

- GitHub：[hellomrleeus/duo-she](https://github.com/hellomrleeus/duo-she)
- Clone 地址：`git@github.com:hellomrleeus/duo-she.git`
