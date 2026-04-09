#!/usr/bin/env python3
"""Shared follow-up orchestration for DuoShe notification channels."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_REPLY_CONTRACT = "done + evidence | partial + evidence | blocked + blocker | reschedule + new time"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout).strip() or "Subprocess failed.")
    try:
        return json.loads(proc.stdout.strip() or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Expected JSON from subprocess, got: {proc.stdout}") from exc


def safe_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise SystemExit(f"Unknown timezone: {name}") from exc


def now_iso(timezone_name: str) -> str:
    return datetime.now(safe_timezone(timezone_name)).isoformat()


def state_paths(project_root: Path, channel: str) -> dict[str, Path]:
    duo_dir = project_root / ".duo-she"
    return {
        "duo_dir": duo_dir,
        "campaign": duo_dir / "duo-she-state.json",
        "channel": duo_dir / f"{channel}-state.json",
        "config": duo_dir / f"{channel}.json",
    }


def channel_scripts(root: Path, channel: str) -> dict[str, Path]:
    return {
        "send": root / f"send_{channel}.py",
        "check": root / f"check_{channel}_reply.py",
        "evaluate": root / "evaluate_follow_up.py",
    }


def config_ready(channel: str, config: dict[str, Any]) -> bool:
    if channel == "telegram":
        required = ("bot_token", "chat_id")
    elif channel == "email":
        required = (
            "smtp_host",
            "smtp_port",
            "imap_host",
            "imap_port",
            "username",
            "password",
            "from_email",
            "to_email",
            "reply_from",
        )
    else:
        raise SystemExit(f"Unsupported channel: {channel}")
    return all(str(config.get(key, "")).strip() for key in required)


def ensure_campaign_state(state: dict[str, Any], timezone_name: str) -> dict[str, Any]:
    state.setdefault("state_version", 2)
    state.setdefault("timezone", timezone_name)
    state.setdefault("status", "active")
    state.setdefault("progress_percent", 0)
    state.setdefault("blockers", [])
    return state


def mission_id(campaign: dict[str, Any]) -> str:
    current = campaign.get("current_mission") or {}
    return current.get("mission_id") or current.get("id") or "duo-she-followup"


def task_id(campaign: dict[str, Any], channel: str) -> str:
    current = campaign.get("current_mission") or {}
    base = current.get("mission_id") or current.get("id") or "duo-she"
    return f"{base}-{channel}"


def current_mission(campaign: dict[str, Any]) -> dict[str, Any]:
    mission = campaign.get("current_mission")
    return mission if isinstance(mission, dict) else {}


def mission_title(campaign: dict[str, Any]) -> str:
    mission = current_mission(campaign)
    return mission.get("title") or mission.get("task") or "Current DuoShe mission"


def reply_contract(campaign: dict[str, Any], channel_state: dict[str, Any]) -> str:
    mission = current_mission(campaign)
    return (
        mission.get("reply_format")
        or channel_state.get("reply_contract")
        or DEFAULT_REPLY_CONTRACT
    )


def deadline_minutes(campaign: dict[str, Any], override: int | None) -> int:
    if override is not None:
        return override
    mission = current_mission(campaign)
    estimated = mission.get("estimated_minutes")
    if isinstance(estimated, int) and estimated > 0:
        return estimated
    return 60


def render_initial_message(campaign: dict[str, Any], channel_state: dict[str, Any], channel: str) -> str:
    mission = current_mission(campaign)
    deliverable = mission.get("deliverable") or "Bring back a concrete update."
    acceptance = mission.get("acceptance") or []
    acceptance_text = "; ".join(str(item) for item in acceptance) if acceptance else "Reply with a concrete status update."
    evidence_hint = mission.get("evidence_hint") or "Attach evidence, a blocker, or a new time."
    lines = [
        f"DuoShe {channel.capitalize()} follow-up",
        "",
        f"任务: {mission_title(campaign)}",
        f"交付物: {deliverable}",
        f"验收: {acceptance_text}",
        f"证据提示: {evidence_hint}",
        f"请回复: {reply_contract(campaign, channel_state)}",
    ]
    return "\n".join(lines)


def render_nudge_message(campaign: dict[str, Any], channel_state: dict[str, Any], stage: str, channel: str) -> str:
    header = {
        "gentle": "到点了，给我一个状态。",
        "firm": "别沉默，沉默也是状态。",
        "urgent": "现在只回状态，不要失联。",
        "reset": "原时间窗已经失效，现在重置状态。",
        "repeat": "还没收到你的回复，现在给状态。",
    }.get(stage, "请回我一个状态。")
    lines = [
        f"DuoShe {channel.capitalize()} {stage} nudge",
        "",
        header,
        f"当前任务: {mission_title(campaign)}",
        f"请回复: {reply_contract(campaign, channel_state)}",
    ]
    return "\n".join(lines)


def render_subject(campaign: dict[str, Any], prefix: str) -> str:
    return f"{prefix}: {mission_title(campaign)}"


def clear_blockers(campaign: dict[str, Any]) -> None:
    campaign["blockers"] = []


def set_blocker(campaign: dict[str, Any], detail: str, evidence_ref: str, timezone_name: str) -> None:
    ensure_campaign_state(campaign, timezone_name)
    campaign["status"] = "blocked"
    campaign["blockers"] = [{"type": "channel_config_missing", "detail": detail}]
    campaign["last_review"] = {
        "status": "blocked",
        "completion_percent": campaign.get("progress_percent", 0),
        "evidence_ref": evidence_ref,
        "blocker_type": "channel_config_missing",
        "notes": detail,
        "next_decision": "Add the project-local channel config and rerun the follow-up orchestrator.",
    }
    campaign["next_check_in"] = ""


def mark_sent(campaign: dict[str, Any], channel: str, channel_state: dict[str, Any], timezone_name: str) -> None:
    ensure_campaign_state(campaign, timezone_name)
    clear_blockers(campaign)
    due_at = channel_state.get("due_at")
    due_text = ""
    if due_at:
        due_text = datetime.fromtimestamp(int(due_at), safe_timezone(timezone_name)).isoformat()
    campaign["status"] = "awaiting_reply"
    campaign["last_review"] = {
        "status": "sent",
        "completion_percent": campaign.get("progress_percent", 0),
        "evidence_ref": str(channel_state.get("_path", "")),
        "blocker_type": "",
        "notes": f"Sent {channel} follow-up for the current mission.",
        "next_decision": "Wait for the user reply or send the next nudge when the evaluator says it is due.",
    }
    campaign["next_check_in"] = due_text


def mark_waiting(
    campaign: dict[str, Any],
    channel: str,
    channel_state: dict[str, Any],
    timezone_name: str,
    notes: str,
    next_check_ts: int | None,
) -> None:
    ensure_campaign_state(campaign, timezone_name)
    clear_blockers(campaign)
    campaign["status"] = "awaiting_reply"
    campaign["last_review"] = {
        "status": "awaiting_reply",
        "completion_percent": campaign.get("progress_percent", 0),
        "evidence_ref": str(channel_state.get("_path", "")),
        "blocker_type": "",
        "notes": notes,
        "next_decision": "Run the orchestrator again at the next check-in time.",
    }
    if next_check_ts:
        campaign["next_check_in"] = datetime.fromtimestamp(next_check_ts, safe_timezone(timezone_name)).isoformat()


def mark_reply(
    campaign: dict[str, Any],
    channel: str,
    channel_state: dict[str, Any],
    timezone_name: str,
) -> None:
    ensure_campaign_state(campaign, timezone_name)
    clear_blockers(campaign)
    status = channel_state.get("reply_status") or "freeform"
    text = channel_state.get("reply_text") or ""
    recorded_at = now_iso(timezone_name)
    campaign.setdefault("channel_replies", {})
    campaign["channel_replies"][channel] = {
        "status": status,
        "text": text,
        "recorded_at": recorded_at,
    }
    mission = current_mission(campaign)
    if mission:
        mission["last_reply_status"] = status
        mission["last_reply_at"] = recorded_at
        if text:
            mission["last_reply_text"] = text
    campaign["status"] = "blocked" if status == "blocked" else "active"
    if status == "blocked":
        campaign["blockers"] = [{"type": "user_blocked", "detail": text or "User reported a blocker."}]
    campaign["last_review"] = {
        "status": status,
        "completion_percent": campaign.get("progress_percent", 0),
        "evidence_ref": str(channel_state.get("_path", "")),
        "blocker_type": "user_blocked" if status == "blocked" else "",
        "notes": f"Captured {channel} reply: {text}".strip(),
        "next_decision": "Return to the main DuoShe review loop and assign the next mission.",
    }
    campaign["next_check_in"] = ""


def default_config_note(channel: str) -> str:
    return f"Missing .duo-she/{channel}.json with the required credentials."


def parse_args(channel: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Run the DuoShe {channel} follow-up orchestrator.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--state-file")
    parser.add_argument("--channel-state-file")
    parser.add_argument("--config")
    parser.add_argument("--text", help="Override the initial outbound message.")
    parser.add_argument("--subject", help="Override the initial email subject.")
    parser.add_argument("--deadline-minutes", type=int)
    parser.add_argument("--timezone")
    parser.add_argument("--quiet-hours")
    parser.add_argument("--workday-end")
    return parser.parse_args()


def main(channel: str) -> int:
    args = parse_args(channel)
    project_root = Path(args.project_root).expanduser().resolve()
    paths = state_paths(project_root, channel)
    scripts = channel_scripts(Path(__file__).resolve().parent, channel)

    campaign_path = Path(args.state_file).expanduser() if args.state_file else paths["campaign"]
    channel_state_path = Path(args.channel_state_file).expanduser() if args.channel_state_file else paths["channel"]
    config_path = Path(args.config).expanduser() if args.config else paths["config"]

    campaign = load_json(campaign_path, {})
    channel_state = load_json(channel_state_path, {})
    timezone_name = (
        args.timezone
        or campaign.get("timezone")
        or channel_state.get("timezone")
        or "Asia/Shanghai"
    )
    ensure_campaign_state(campaign, timezone_name)
    channel_state["_path"] = str(channel_state_path)

    config = load_json(config_path, {})
    if not config_ready(channel, config):
        set_blocker(campaign, default_config_note(channel), str(config_path), timezone_name)
        save_json(campaign_path, campaign)
        print(json.dumps({"status": "blocked", "reason": "missing_config", "config_path": str(config_path)}, ensure_ascii=False))
        return 0

    quiet_hours = args.quiet_hours or channel_state.get("quiet_hours") or "22:00-08:00"
    workday_end = args.workday_end or channel_state.get("workday_end") or quiet_hours.split("-", 1)[0]

    if not channel_state.get("last_sent_at"):
        outbound_text = args.text or render_initial_message(campaign, channel_state, channel)
        task = task_id(campaign, channel)
        mission = mission_id(campaign)
        deadline = deadline_minutes(campaign, args.deadline_minutes)
        if channel == "telegram":
            send_cmd = [
                "python3",
                str(scripts["send"]),
                "--config",
                str(config_path),
                "--state-file",
                str(channel_state_path),
                "--task-id",
                task,
                "--mission-id",
                mission,
                "--goal-snapshot",
                str(campaign.get("goal", "")),
                "--deadline-minutes",
                str(deadline),
                "--timezone",
                timezone_name,
                "--quiet-hours",
                quiet_hours,
                "--workday-end",
                workday_end,
                "--reply-contract",
                reply_contract(campaign, channel_state),
                "--text",
                outbound_text,
            ]
        else:
            send_cmd = [
                "python3",
                str(scripts["send"]),
                "--config",
                str(config_path),
                "--state-file",
                str(channel_state_path),
                "--task-id",
                task,
                "--mission-id",
                mission,
                "--goal-snapshot",
                str(campaign.get("goal", "")),
                "--deadline-minutes",
                str(deadline),
                "--timezone",
                timezone_name,
                "--quiet-hours",
                quiet_hours,
                "--workday-end",
                workday_end,
                "--reply-contract",
                reply_contract(campaign, channel_state),
                "--subject",
                args.subject or render_subject(campaign, "DuoShe follow-up"),
                "--text",
                outbound_text,
            ]
        payload = run_json(send_cmd)
        channel_state = load_json(channel_state_path, {})
        channel_state["_path"] = str(channel_state_path)
        mark_sent(campaign, channel, channel_state, timezone_name)
        save_json(campaign_path, campaign)
        print(json.dumps({"status": "sent", "payload": payload}, ensure_ascii=False))
        return 0

    reply = run_json(
        [
            "python3",
            str(scripts["check"]),
            "--config",
            str(config_path),
            "--state-file",
            str(channel_state_path),
        ]
    )
    channel_state = load_json(channel_state_path, {})
    channel_state["_path"] = str(channel_state_path)
    if reply.get("replied"):
        mark_reply(campaign, channel, channel_state, timezone_name)
        save_json(campaign_path, campaign)
        print(json.dumps({"status": "reply_recorded", "reply": reply}, ensure_ascii=False))
        return 0

    now_ts = int(datetime.now(safe_timezone(timezone_name)).timestamp())
    decision = run_json(
        [
            "python3",
            str(scripts["evaluate"]),
            "--state-file",
            str(channel_state_path),
            "--now",
            str(now_ts),
        ]
    )

    if decision.get("action") == "send":
        nudge_text = render_nudge_message(campaign, channel_state, decision.get("stage", "repeat"), channel)
        if channel == "telegram":
            send_cmd = [
                "python3",
                str(scripts["send"]),
                "--config",
                str(config_path),
                "--text",
                nudge_text,
            ]
        else:
            send_cmd = [
                "python3",
                str(scripts["send"]),
                "--config",
                str(config_path),
                "--subject",
                render_subject(campaign, f"DuoShe {decision.get('stage', 'follow-up')}"),
                "--text",
                nudge_text,
            ]
        payload = run_json(send_cmd)
        channel_state = load_json(channel_state_path, {})
        channel_state["last_prompt"] = nudge_text
        channel_state["last_sent_at"] = now_ts
        save_json(channel_state_path, channel_state)
        run_json(
            [
                "python3",
                str(scripts["evaluate"]),
                "--state-file",
                str(channel_state_path),
                "--now",
                str(now_ts),
                "--mark-sent",
            ]
        )
        next_decision = run_json(
            [
                "python3",
                str(scripts["evaluate"]),
                "--state-file",
                str(channel_state_path),
                "--now",
                str(now_ts),
            ]
        )
        channel_state = load_json(channel_state_path, {})
        channel_state["_path"] = str(channel_state_path)
        next_check_ts = now_ts + int(next_decision.get("wait_seconds", 0)) if next_decision.get("wait_seconds") else None
        mark_waiting(
            campaign,
            channel,
            channel_state,
            timezone_name,
            f"Sent {decision.get('stage', 'follow-up')} {channel} nudge.",
            next_check_ts,
        )
        save_json(campaign_path, campaign)
        print(json.dumps({"status": "nudge_sent", "decision": decision, "payload": payload}, ensure_ascii=False))
        return 0

    next_check_ts = now_ts + int(decision.get("wait_seconds", 0)) if decision.get("wait_seconds") else None
    note = f"Waiting for {channel} reply."
    if decision.get("reason"):
        note += f" Evaluator status: {decision['reason']}."
    mark_waiting(campaign, channel, channel_state, timezone_name, note, next_check_ts)
    save_json(campaign_path, campaign)
    print(json.dumps({"status": "awaiting_reply", "decision": decision}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit("Import this module from run_telegram_followup.py or run_email_followup.py.")
