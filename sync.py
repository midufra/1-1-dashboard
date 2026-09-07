#!/usr/bin/env python3
"""
Pulls Goals, Projects, and Tasks from Notion and writes docs/data.json
for the static dashboard to read. Run on a schedule via GitHub Actions.
"""
import os
import sys
import json
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_VERSION = "2025-09-03"

# --- Fill in your own data source IDs below ---
PROJECTS_DS = "2de367a5-461c-813b-9afb-000b14a010e2"
TASKS_DS = "2de367a5-461c-81dd-9653-000b49cbcae1"
GOALS_DS = "e877714e-d11e-418c-aecd-e104cbec6c4c"
WEEKLY_FOCUS_DS = "92df558c-e12f-4123-a0a5-5fbe305470eb"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

DONE_STATUSES = {"Done", "Canceled"}


def query_all(data_source_id, body=None):
    """Query a data source, following pagination until exhausted."""
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    results = []
    payload = dict(body or {})
    payload["page_size"] = 100
    while True:
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"ERROR querying {data_source_id}: {resp.status_code} {resp.text}", file=sys.stderr)
            resp.raise_for_status()
        data = resp.json()
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return results


def get_title(props, key):
    try:
        arr = props[key]["title"]
        return "".join(t["plain_text"] for t in arr) if arr else ""
    except (KeyError, TypeError):
        return ""


def get_rich_text(props, key):
    try:
        arr = props[key]["rich_text"]
        return "".join(t["plain_text"] for t in arr) if arr else ""
    except (KeyError, TypeError):
        return ""


def get_select(props, key):
    try:
        return props[key]["select"]["name"]
    except (KeyError, TypeError):
        return None


def get_status(props, key):
    try:
        return props[key]["status"]["name"]
    except (KeyError, TypeError):
        return None


def get_checkbox(props, key):
    try:
        return bool(props[key]["checkbox"])
    except (KeyError, TypeError):
        return False


def get_relation_ids(props, key):
    try:
        return [r["id"] for r in props[key]["relation"]]
    except (KeyError, TypeError):
        return []


def main():
    print("Fetching Tasks...")
    tasks = query_all(TASKS_DS)

    # Build project_id -> {done, total} from tasks linked directly to that project.
    task_stats = {}
    for t in tasks:
        props = t["properties"]
        status = get_status(props, "Status")
        for pid in get_relation_ids(props, "Project"):
            stats = task_stats.setdefault(pid, {"done": 0, "total": 0})
            stats["total"] += 1
            if status in DONE_STATUSES:
                stats["done"] += 1

    print("Fetching Projects...")
    # Fetch every project (not just top-level ones) so mini-projects/sub-projects
    # can be rolled up into their parent's completion percentage. Without this,
    # a top-level project's % only reflected tasks filed directly on it, so it
    # kept climbing back down every time new work landed there directly instead
    # of ever reaching 100 - splitting work into mini-projects is what lets a
    # parent project actually finish.
    all_projects_raw = query_all(PROJECTS_DS)

    all_lookup = {}
    for p in all_projects_raw:
        props = p["properties"]
        pid = p["id"]
        stats = task_stats.get(pid, {"done": 0, "total": 0})
        own_pct = round(100 * stats["done"] / stats["total"]) if stats["total"] else None
        all_lookup[pid] = {
            "id": pid,
            "name": get_title(props, "Project name"),
            "status": get_status(props, "Status"),
            "stage": get_select(props, "Stage"),
            "pillar": get_select(props, "Pillar"),
            "summary": get_rich_text(props, "Summary"),
            "own_completion": own_pct,
            "task_counts": stats,
            "goal_ids": get_relation_ids(props, "Goal"),
            "parent_ids": get_relation_ids(props, "Parent project"),
            "sub_ids": get_relation_ids(props, "Sub-project"),
        }

    def rolled_up_completion(pid, seen=None):
        """A project with mini-projects underneath finishes by finishing them:
        its completion is the average of its sub-projects' completion (recursing
        for grandchildren). A project with no sub-projects falls back to its own
        directly-linked tasks, same as before."""
        seen = seen or set()
        if pid in seen or pid not in all_lookup:
            return all_lookup.get(pid, {}).get("own_completion")
        seen.add(pid)
        entry = all_lookup[pid]
        subs = [sid for sid in entry["sub_ids"] if sid in all_lookup]
        if not subs:
            return entry["own_completion"]
        child_pcts = [rolled_up_completion(sid, seen) for sid in subs]
        child_pcts = [c for c in child_pcts if c is not None]
        return round(sum(child_pcts) / len(child_pcts)) if child_pcts else entry["own_completion"]

    projects = []
    project_lookup = {}
    for pid, entry in all_lookup.items():
        if entry["parent_ids"]:
            continue  # only top-level projects surface on the dashboard
        pct = rolled_up_completion(pid)
        out_entry = {
            "id": pid,
            "name": entry["name"],
            "status": entry["status"],
            "stage": entry["stage"],
            "pillar": entry["pillar"],
            "summary": entry["summary"],
            "completion": pct,
            "task_counts": entry["task_counts"],
            "goal_ids": entry["goal_ids"],
        }
        projects.append(out_entry)
        project_lookup[pid] = out_entry

    print("Fetching Goals...")
    goals_raw = query_all(GOALS_DS)
    goals = []
    for g in goals_raw:
        props = g["properties"]
        linked_ids = get_relation_ids(props, "Projects")
        linked_projects = [project_lookup[pid] for pid in linked_ids if pid in project_lookup]
        completions = [p["completion"] for p in linked_projects if p["completion"] is not None]
        avg = round(sum(completions) / len(completions)) if completions else 0
        goals.append({
            "id": g["id"],
            "name": get_title(props, "Goal name"),
            "completion": avg,
            "project_ids": linked_ids,
        })

    print("Fetching Weekly Focus...")
    focus_filter = {"filter": {"property": "Active", "checkbox": {"equals": True}}}
    focus_raw = query_all(WEEKLY_FOCUS_DS, focus_filter)
    weekly_focus = []
    for f in focus_raw:
        props = f["properties"]
        text = get_title(props, "Text")
        raw_type = get_select(props, "Type") or "Topic"
        if not text:
            continue
        weekly_focus.append({
            "type": "help" if raw_type.lower().startswith("help") else "topic",
            "text": text,
        })

    # --- History log + monthly recap ---
    # Read whatever already exists so we accumulate real weekly snapshots
    # over time, and preserve any recap text a person has written in.
    existing_history = []
    monthly_recap = ""
    if os.path.exists("docs/data.json"):
        try:
            with open("docs/data.json") as f:
                old = json.load(f)
                existing_history = old.get("history", [])
                monthly_recap = old.get("monthly_recap", "")
        except Exception:
            pass

    today = __import__("datetime").datetime.utcnow().date().isoformat()
    today_entry = {
        "date": today,
        "projects": [
            {"name": p["name"], "status": p["status"], "summary": p["summary"]}
            for p in projects if p["stage"] == "Now"
        ],
    }
    # One entry per day max (re-runs same day just update it)
    if existing_history and existing_history[-1]["date"] == today:
        existing_history[-1] = today_entry
    else:
        existing_history.append(today_entry)
    existing_history = existing_history[-56:]  # keep roughly the last 8 weeks

    out = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "goals": goals,
        "projects": projects,
        "weekly_focus": weekly_focus,
        "history": existing_history,
        "monthly_recap": monthly_recap,
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote docs/data.json — {len(goals)} goals, {len(projects)} projects, {len(weekly_focus)} focus items")


if __name__ == "__main__":
    main()
