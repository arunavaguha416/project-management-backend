import json
from projects.utils.ollama_client import ollama_generate, is_ollama_running


def build_quick_brief(sprint, tasks) -> dict:
    total = len(tasks)
    done = sum(1 for t in tasks if (t.status or "").upper() == "DONE")
    blocked = sum(1 for t in tasks if (t.status or "").upper() == "BLOCKED")
    in_progress = sum(1 for t in tasks if (t.status or "").upper() == "IN_PROGRESS")
    todo = total - done - blocked - in_progress

    summary = f"{done}/{total} done. {in_progress} in progress, {blocked} blocked."
    highlights = []
    risks = []
    next_actions = []

    if total == 0:
        summary = "No tasks found for this sprint yet."
        risks.append("Sprint has no tasks assigned.")
        next_actions.append("Add tasks to the sprint backlog.")
    else:
        if done == 0:
            risks.append("No tasks completed yet.")
        if blocked > 0:
            risks.append(f"{blocked} blocked task(s) need attention.")
        if in_progress == 0 and todo > 0:
            risks.append("Work has not started on any tasks.")
        if done > 0:
            highlights.append(f"{done} task(s) completed so far.")
        if in_progress > 0:
            next_actions.append("Unblock in-progress tasks and push to review.")
        if blocked > 0:
            next_actions.append("Resolve blockers and reassign if needed.")

    return {
        "summary": summary,
        "highlights": highlights,
        "risks": risks,
        "next_actions": next_actions
    }


def _extract_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == -1:
        raise ValueError("Invalid JSON from Ollama")
    return json.loads(raw[start:end])


def build_sprint_brief(sprint, tasks, fallback: dict | None = None) -> dict:
    if not is_ollama_running():
        return fallback or {
            "summary": "Ollama is offline. Showing baseline sprint insights.",
            "highlights": [],
            "risks": [],
            "next_actions": []
        }

    if not tasks:
        return fallback or {
            "summary": "No tasks found for this sprint yet.",
            "highlights": [],
            "risks": ["Sprint has no tasks assigned"],
            "next_actions": ["Add tasks to the sprint backlog"]
        }

    task_lines = []
    for t in tasks:
        task_lines.append(
            f"- {t.title} | status={t.status} | priority={t.priority} | assignee={getattr(t.assigned_to, 'name', 'Unassigned')}"
        )

    total = len(tasks)
    done = sum(1 for t in tasks if (t.status or "").upper() == "DONE")
    blocked = sum(1 for t in tasks if (t.status or "").upper() == "BLOCKED")
    in_progress = sum(1 for t in tasks if (t.status or "").upper() == "IN_PROGRESS")

    prompt = f"""
You are an expert agile coach. Produce a concise sprint brief from the data below.

RULES:
- Output ONLY valid JSON
- Keep sentences short and action-focused
- Do not invent data

SCHEMA:
{{
  "summary": "",
  "highlights": [""],
  "risks": [""],
  "next_actions": [""]
}}

SPRINT:
name: {sprint.name}
goal: {sprint.goal or 'N/A'}
status: {sprint.status}
stats: total={total}, done={done}, in_progress={in_progress}, blocked={blocked}

TASKS:
{chr(10).join(task_lines[:15])}
"""

    raw = ollama_generate(prompt, timeout=6)
    return _extract_json(raw)
