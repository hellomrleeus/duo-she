# Installing DuoShe for Codex

Enable the `duo-she` skill in Codex via native skill discovery.

## Prerequisites

- Codex
- Git, if you are installing from a repository
- Python 3, if you want Telegram or email delivery

## Install with Codex Skill Installer

If the skill is hosted on GitHub, this is the easiest path.

Ask Codex:

```text
Use $skill-installer to install https://github.com/hellomrleeus/duo-she
```

After installation, restart Codex to pick up the new skill.

This repository root is already the `duo-she` skill folder, so you do not need a deeper subdirectory path.

## Manual Installation

### Option 1: Clone the repository and copy the skill folder

Clone the source repository:

```bash
git clone git@github.com:hellomrleeus/duo-she.git
```

Then copy the `duo-she` directory into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /path/to/duo-she "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

### Option 2: Clone the repository and symlink the skill folder

Clone the source repository:

```bash
git clone git@github.com:hellomrleeus/duo-she.git
```

Use a symlink if you want edits in the source directory to update immediately:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s /path/to/duo-she "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

Restart Codex after installing.

## Verify

```bash
ls -la "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

You should see:

- `CLAUDE.md`
- `SKILL.md`
- `agents/openai.yaml`
- `scripts/`
- `references/`

## Optional Channel Setup

`duo-she` works without external channels, but Telegram and email delivery require one-time setup.

### Telegram

```bash
cd /path/to/project
python3 "${CODEX_HOME:-$HOME/.codex}/skills/duo-she/scripts/setup_telegram.py" \
  --bot-token ... \
  --chat-id ...
```

This saves config to:

```bash
.duo-she/telegram.json
```

### Email

```bash
cd /path/to/project
python3 "${CODEX_HOME:-$HOME/.codex}/skills/duo-she/scripts/setup_email.py"
```

This saves config to:

```bash
.duo-she/email.json
```

## Updating

If you installed from a GitHub repo and kept it cloned locally:

```bash
cd /path/to/repo && git pull
```

If you installed by copying files, replace the installed folder with the updated `duo-she` directory.

## Maintainer note

`CLAUDE.md` is the canonical instruction file in this repository.

After editing it, regenerate `SKILL.md` with:

```bash
python3 scripts/sync_skill.py
```

To verify sync without rewriting the file:

```bash
python3 scripts/sync_skill.py --check
```

## Uninstalling

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

Optional project-local runtime cleanup:

```bash
rm -rf .duo-she
```
