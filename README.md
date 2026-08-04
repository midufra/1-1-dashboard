# Dashboard Sync

Pulls Goals/Projects/Tasks from Notion daily and publishes a live
status dashboard via GitHub Pages.

## One-time setup

1. **Create the repo.** Push these files to a new GitHub repo (public
   or private — GitHub Pages works with either on paid plans; public
   repos get Pages free).

2. **Add the Notion token as a secret.**
   Repo → Settings → Secrets and variables → Actions → New repository
   secret → name it `NOTION_TOKEN`, paste your Notion connection token.

3. **Enable GitHub Pages.**
   Repo → Settings → Pages → Source: "Deploy from a branch" → Branch:
   `main`, folder: `/docs` → Save.
   Your dashboard will be live at `https://<username>.github.io/<repo>/`.

4. **Run the sync once manually** to populate real data immediately
   instead of waiting for tomorrow's scheduled run:
   Repo → Actions tab → "Sync Notion dashboard data" → Run workflow.

## Changing the schedule

Edit the `cron` line in `.github/workflows/sync.yml`. Current default
is 7:00am UTC daily. Cron time is always UTC regardless of your
timezone.

## Data source IDs

If your Notion structure changes (new database, re-created relation,
etc.), update the IDs at the top of `sync.py`:
- `PROJECTS_DS`
- `TASKS_DS`
- `GOALS_DS`
