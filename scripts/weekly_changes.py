#!/usr/bin/env python3
"""
Summarise what changed in Notion over the past week, using the daily
docs/data.json snapshots the sync commits to git. Feeds the weekly 5:15
draft (see .claude/weekly-515.md).

    python scripts/weekly_changes.py            # last 7 days
    python scripts/weekly_changes.py --days 14
"""
import argparse
import json
import subprocess


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def snapshot_at(ref):
    return json.loads(git("show", f"{ref}:docs/data.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    old_ref = git("rev-list", "-1", f"--before={args.days} days ago", "HEAD", "--", "docs/data.json")
    if not old_ref:
        old_ref = git("rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    old, new = snapshot_at(old_ref), snapshot_at("HEAD")
    print(f"Comparing data.json from {old.get('generated_at')} to {new.get('generated_at')}\n")

    old_p = {p["id"]: p for p in old.get("projects", [])}
    new_p = {p["id"]: p for p in new.get("projects", [])}

    print("## Project changes")
    any_change = False
    for pid, p in new_p.items():
        name = p["name"].strip()
        o = old_p.get(pid)
        if o is None:
            print(f"- NEW: {name} (status {p['status']}, stage {p['stage']})")
            any_change = True
            continue
        diffs = []
        for key in ("status", "stage", "completion", "summary"):
            if o.get(key) != p.get(key):
                diffs.append(f"{key}: {o.get(key)!r} -> {p.get(key)!r}")
        oc, nc = o.get("task_counts", {}), p.get("task_counts", {})
        if oc != nc:
            diffs.append(f"tasks done {oc.get('done', 0)}/{oc.get('total', 0)} -> {nc.get('done', 0)}/{nc.get('total', 0)}")
        if diffs:
            any_change = True
            print(f"- {name}: " + "; ".join(diffs))
    for pid, o in old_p.items():
        if pid not in new_p:
            any_change = True
            print(f"- REMOVED or now a sub-project: {o['name'].strip()}")
    if not any_change:
        print("- No top-level project changes.")

    print("\n## Goals")
    old_g = {g["id"]: g for g in old.get("goals", [])}
    for g in new.get("goals", []):
        before = old_g.get(g["id"], {}).get("completion")
        print(f"- {g['name']}: {before}% -> {g['completion']}%")

    print("\n## Weekly Focus (Notion), now")
    for f in new.get("weekly_focus", []):
        print(f"- [{f['type']}] {f['text']}")
    old_focus = {f["text"] for f in old.get("weekly_focus", [])}
    dropped = [t for t in old_focus if t not in {f["text"] for f in new.get("weekly_focus", [])}]
    if dropped:
        print("\nDropped from Weekly Focus since then:")
        for t in dropped:
            print(f"- {t}")


if __name__ == "__main__":
    main()
