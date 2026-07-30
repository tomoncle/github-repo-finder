---
name: github-repo-finder
description: Find recently created GitHub repositories by creation date and keywords, especially for new open-source projects, Three.js-related repos, AI/agent/skill repos, or any request to search GitHub by "created in the last N days" instead of modified activity.
---

# Github Repo Finder

## Overview

Use this skill to search GitHub for repositories created within a date window, then narrow results by keywords such as `three.js`, `AI`, `skill`, `Claude`, or `agent`.

Use the bundled script when the user wants recent repos, especially when they care about creation time rather than updates.

## Quick Start

Run the search script with a creation window, star threshold, and keywords:

```bash
python3 scripts/search_recent_repos.py --days 2 --min-stars 500 --keywords ai skill --format table
```

## Workflow

1. Pick the creation window with `--days` or `--since`.
2. Add one or more keywords with `--keywords`.
3. Require a minimum star count with `--min-stars` when the user asks for popular repos.
4. Add required phrases with `--must-have` when the result must mention a term.
5. Add exclusions with `--exclude` to remove noise.
6. Use `--format table` when the user wants console table output.
7. Review the output and share only repositories whose `created_at` falls inside the requested window.

## Query Rules

- Prefer `created:` filters in GitHub search; do not use `pushed:` or `updated:` for this task.
- Treat the creation date in the API response as the source of truth.
- If the user asks for "最近两天", interpret it as the last 2 calendar days in UTC unless they specify a timezone.
- If the search is broad, sort by `created` and then optionally re-rank by stars.
- Keep the output focused on public repos unless the user asks otherwise.

## Output Format

For each repository, show:

- `full_name`
- `created_at`
- `stargazers_count`
- short description
- `html_url`

When the user wants a console table, print columns in this order:

- `项目地址`
- `创建时间`
- `Star数量`
- `仓库名称`

If the user wants a deeper pass, also mention whether the repo looks AI-related, skill-related, or Three.js-related.

## Scripts

### `scripts/search_recent_repos.py`
Search GitHub repositories by creation date and keyword filters.

Use it when you need a repeatable way to answer questions like:

- "最近两天 GitHub 上新建的 Three.js 项目有哪些"
- "最近两天创建的 AI skill 仓库有哪些"
- "找最近 3 天创建的 Claude/Codex 相关开源项目"

Prefer the script over manual browsing when the user may ask the same class of question again.

## Notes

- Use `GITHUB_TOKEN` or `GH_TOKEN` if unauthenticated rate limits get in the way.
- If `AGENT_HTTP_PROXY` is set, the script tries the proxy first and automatically falls back to a direct connection if the proxy fails. No manual intervention needed.
- The script auto-prepends `http://` to `AGENT_HTTP_PROXY` if no scheme is present.
- All connections use a 10-second timeout to avoid hanging on unreachable endpoints.
- Keep searches narrow before broadening the keyword list.
- Return only repositories created inside the requested time window.
