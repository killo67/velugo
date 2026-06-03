# newAgg

MVP for collecting and displaying the latest online India newspaper headlines.

## Run The MVP

Open `src/index.html` in a browser. The page is static and uses the seeded data in `assets/data/india-headlines.js`, so no dev server is required.

For production-style validation, build and run the static container:

```bash
docker build -t newagg .
docker run --rm -p 8080:80 newagg
```

Then open:

```text
http://localhost:8080
```

The container serves the static app at `/`, generated data under `/assets/data/`, and exposes `/healthz` for a lightweight health check.

## Refresh Headlines

The refresh script is dependency-free and writes both the browser-loadable data file and a JSON edition artifact:

```bash
# Standard daily run (RSS excerpts only, ~8s)
python3 scripts/fetch_india_headlines.py

# Recommended: with full article text extraction (~25s, parallel HTTP fetches)
python3 scripts/fetch_india_headlines.py --extract-text
```

With `--extract-text`, the script fetches each article page in parallel (6 workers) and adds an `articleText` field (~1500 chars) to each headline. Sources that support it: The Hindu, Hindustan Times, Mint. PIB always includes full text regardless of this flag.

Useful options:

```bash
python3 scripts/fetch_india_headlines.py --extract-text          # recommended daily
python3 scripts/fetch_india_headlines.py --extract-text --enrich # full enrichment (~45s, requires ANTHROPIC_API_KEY)
python3 scripts/fetch_india_headlines.py --date 2026-04-22 --allow-partial
python3 scripts/fetch_india_headlines.py --min-headlines 20
python3 scripts/fetch_india_headlines.py --limit 50
```

With `--enrich`, each headline is classified with a UPSC topic, exam angle, relevance score, and a "why it matters" explanation. Results are cached in the edition JSON — safe to re-run if interrupted.

**Option A — Claude API** (`--enrich`): ~$0.03–0.05 per edition, fastest (~45s).

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or for daily automation: echo "ANTHROPIC_API_KEY=sk-ant-..." > scripts/.env
python3 scripts/fetch_india_headlines.py --extract-text --enrich
```

**Option B — Local Ollama** (`--enrich-local`): free, no API key, runs on your machine.

```bash
# One-time setup
brew install ollama
ollama pull qwen2.5:7b    # 4.4 GB — recommended
# ollama pull phi4-mini   # 2.3 GB — faster alternative

# Run (Ollama starts automatically after brew install)
python3 scripts/fetch_india_headlines.py --extract-text --enrich-local
python3 scripts/fetch_india_headlines.py --enrich-local --local-model phi4-mini
```

**Option C — Mock data** (`--enrich-mock`): no cost, no model, instant. For UI testing only.

```bash
python3 scripts/fetch_india_headlines.py --enrich-mock
```

The script uses public RSS feeds and keeps items dated today in Asia/Kolkata by default. It writes:

- `assets/data/india-headlines.js` — browser-loadable bundle (today's edition)
- `assets/data/editions/YYYY-MM-DD.json` — daily archive artifact
- `assets/data/editions/index.json` — list of all available editions (used by the archive nav UI)

The generated artifacts include source-level health and policy metadata. The static page surfaces this under source health so failed or out-of-scope feeds are visible.

Treat the output as a collection aid, then verify source links before editorial use.

## Automate Daily Fetch

### macOS (launchd)

The plist fires `run-daily.sh` at 6:30 AM in your Mac's local timezone. If your Mac is set to IST (`Asia/Kolkata`), no adjustment is needed.

**One-time setup:**

```bash
# 1. Get the absolute path to the project
PROJECT_DIR="$(pwd)"   # run from the newAgg directory

# 2. Install the plist, substituting the real path
sed "s|PROJECT_DIR|$PROJECT_DIR|g" \
  scripts/com.newagg.daily-fetch.plist \
  > ~/Library/LaunchAgents/com.newagg.daily-fetch.plist

# 3. Load it (starts watching; runs at next trigger time)
launchctl load ~/Library/LaunchAgents/com.newagg.daily-fetch.plist
```

**Verify it's scheduled:**

```bash
launchctl list | grep newagg
```

A `0` in the first column means it ran successfully last time. `-` means it hasn't run yet.

**Run it manually right now** (useful for testing):

```bash
launchctl start com.newagg.daily-fetch
# or directly:
bash scripts/run-daily.sh
```

**Uninstall:**

```bash
launchctl unload ~/Library/LaunchAgents/com.newagg.daily-fetch.plist
rm ~/Library/LaunchAgents/com.newagg.daily-fetch.plist
```

**Logs** are written to `logs/fetch-YYYY-MM-DD.log` (one per day) and `logs/launchd-stdout.log`.

---

### Linux / VPS (cron)

```bash
# Open crontab
crontab -e

# Add this line — runs at 1:00 AM UTC = 6:30 AM IST
0 1 * * * cd /path/to/newAgg && bash scripts/run-daily.sh >> logs/cron.log 2>&1
```

Replace `/path/to/newAgg` with the absolute project path. Logs land in `logs/`.

---

### What the daily run does

`scripts/run-daily.sh` calls:

```bash
python3 scripts/fetch_india_headlines.py --extract-text --allow-partial --notify
python3 scripts/post_telegram.py          # posts if TELEGRAM_BOT_TOKEN is set; saves .md only otherwise
```

- `--extract-text` — full article body extraction (~25s)
- `--allow-partial` — writes artifacts even on low-volume days (weekends/holidays) instead of exiting with an error
- `--notify` — sends a macOS desktop notification on completion (silently skipped on Linux)

---

## Telegram Distribution

The daily run automatically posts a structured brief to a Telegram channel if credentials are configured. The brief includes:

- **Must-Know Today** — top 7 headlines by UPSC relevance, each linking to its source
- **Ongoing Stories** — headlines tracked across multiple days (Day N badge)
- **Key Facts for Prelims** — aggregated fact chips (constitutional refs, appointments, money, stats)
- **GS Paper Breakdown** — headline count by GS1/GS2/GS3/GS4

A Markdown copy is also saved to `assets/data/briefs/YYYY-MM-DD.md` on every run (even without Telegram credentials) — suitable for sharing on WhatsApp, Notion, or email.

### One-time Telegram setup

**Step 1 — Create a bot**

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts (choose a name and username)
3. BotFather replies with your bot token — copy it:
   ```
   123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```

**Step 2 — Create a channel and add the bot**

1. In Telegram: New Channel → set name (e.g. *newAgg UPSC Daily*) → Public channel → set username (e.g. `@newagg_daily`)
2. Go to channel settings → Administrators → Add Administrator → search your bot username → give it **Post Messages** permission

**Step 3 — Configure credentials**

Add both values to `scripts/.env` (create the file if it doesn't exist):

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHANNEL_ID=@newagg_daily
```

The channel ID can also be the numeric chat ID (e.g. `-1001234567890`) — useful for private channels. To find a private channel's numeric ID, forward a message from it to **@userinfobot**.

**Step 4 — Test before going live**

```bash
# Preview both Telegram messages and the Markdown brief (no network calls)
python3 scripts/post_telegram.py --dry-run

# Generate and save the Markdown brief only (no Telegram post)
python3 scripts/post_telegram.py --save-only

# Post to Telegram
python3 scripts/post_telegram.py
```

**Step 5 — Verify it's working**

After the first real post, open your channel — you should see two consecutive messages. The first contains the Must-Know section; the second contains Ongoing Stories, Prelims Facts, and the GS breakdown.

### Manual brief for a past edition

```bash
python3 scripts/post_telegram.py --date 2026-06-01 --dry-run   # preview
python3 scripts/post_telegram.py --date 2026-06-01             # post
```

### Brief output locations

| File | Purpose |
|------|---------|
| `assets/data/briefs/YYYY-MM-DD.md` | Shareable Markdown brief (generated every run) |
| `logs/fetch-YYYY-MM-DD.log` | Full fetch + brief generation log |

---

## Validate Changes

Run syntax checks:

```bash
node --check src/app.js
node --check assets/data/india-headlines.js
PYTHONPYCACHEPREFIX=/tmp/newagg-pycache python3 -m py_compile scripts/fetch_india_headlines.py
```

Then validate the production container:

```bash
docker build -t newagg .
docker run --rm -p 8080:80 newagg
curl -I http://localhost:8080/healthz
```
