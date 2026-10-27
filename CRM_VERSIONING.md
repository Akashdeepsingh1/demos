# CRM version control — how updates, notes, and feedback are kept safe

## The repository
`~/workspace/website-business/` is a git repository (local). Every change to
the CRM system — the builder (`crm_build.py`), the CRM pages, the prospect
data (`prospects.csv`, `state.json`), the pitch book, the dashboard, and the
SEO/AEO files — is committed here, so no update is ever lost and any earlier
version can be restored.

- **Canonical daily file:** `crm.html`. Open this one in your browser day to
  day. Rebuilding it never wipes your notes (see below).
- **Dated snapshots:** `crm-kanban-YYYY-MM-DD.html` are backups of a build,
  not daily files. Opening a different filename can hide your notes — see
  "Why notes can look lost" below.
- **Remote:** not pushed anywhere yet. The existing GitHub Pages repo
  (`Akashdeepsingh1/demos`) is public, so pushing the CRM there would expose
  the lead list and pricing. A private GitHub repo is the right remote; it
  needs the owner's go-ahead before anything is pushed.

## Where your notes actually live
Your stages, dates, outcomes, notes, and corrections are stored in your
browser's local storage (keys `abhaa-crm-v1` for tracking and
`abhaa-crm-feedback` for the feedback queue) — not inside the CRM file.
That means:
- Rebuilding or updating `crm.html` does **not** touch your notes, as long as
  you keep opening the same file.
- Opening a *different* file (e.g. `crm.html` vs `crm-kanban-2026-10-26.html`),
  a different browser, or a different device starts with empty notes, because
  the browser ties storage to the exact page you opened.
- Clearing browser data wipes them.

## Backing up and moving notes
- **Export notes** (button in the CRM controls) downloads
  `crm-notes-backup.json`: every stage, date, outcome, note, correction, and
  queued feedback item. Export regularly, and always before switching files,
  browsers, or devices.
- **Import notes** (button next to it) reads a backup and merges it in:
  imported values win per field, existing notes you did not overwrite are
  kept, and corrections merge the same way. Invalid files change nothing.
- Rule of thumb: if your notes ever look empty, do not re-enter them — use
  Import notes with your latest backup first.

## Feedback workflow (feedback is version-controlled too)
1. On any CRM card, **Correct info** updates the card immediately and queues
   the fix.
2. **Feedback queue → Export** downloads `crm-feedback.json` (the queue is
   also included in every notes backup).
3. Send the export to Muse. Muse applies it to `prospects.csv`, regenerates
   the CRM, dashboard, and pitch book, saves the feedback file under
   `feedback/YYYY-MM-DD.json`, and commits with a message like
   `Apply CRM feedback (2026-10-26): corrected review counts`.
4. That commit is the audit trail: every feedback batch, what changed, and
   when — nothing is applied silently and nothing is lost.

## Build freshness check
Every CRM build prints a stamp under the title, e.g.
`Build 2026-10-26 16:39 PDT`. If the stamp is older than the latest build,
you are looking at a stale copy — close it and reopen the current file.
