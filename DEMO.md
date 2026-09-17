# LifeBoard — CS50x Final Project Video Guide

The CS50x final-project video must be no more than 3 minutes. This file is a recording guide, not part of the running application.

## Before recording

Prepare the application with:

- one owner account;
- one member account;
- one board with at least three categories;
- at least one `individual` category;
- at least one `shared` category;
- a few yes/no answers already recorded;
- at least one previous week containing data.

Keep a second browser profile or private window ready for the member account if possible.

Fill these required opening details before recording:

```text
LifeBoard
Name: <YOUR NAME>
GitHub: lucastrevvos
edX: <YOUR EDX USERNAME>
Location: <CITY, COUNTRY>
Recorded: <DATE>
```

Also replace `<VIDEO_URL>` in the root `README.md` after the video has been uploaded.

## Suggested 3-minute sequence

### 0:00–0:12 — Required opening card

Show the required information above clearly on screen. Do not spend long introducing yourself; the rest of the time is needed for the product demo.

### 0:12–0:30 — Problem and concept

Suggested narration:

> LifeBoard digitizes a physical Monday-to-Sunday board used to track recurring areas of daily life. It supports both personal activities and answers that are shared by everyone on a board.

Show the board page and weekly grid.

### 0:30–0:55 — Authentication and boards

Briefly show:

- authenticated account/header;
- board list;
- creating or opening a board;
- pending invitations if you already have one prepared.

Do not spend time typing a full registration flow unless necessary.

### 0:55–1:25 — Individual versus shared categories

Open the board management area and show at least:

- one individual category;
- one shared category;
- owner/member role;
- category creation controls.

Suggested narration:

> Individual categories store a separate daily answer for each member. Shared categories have one board-level daily answer that everyone sees.

### 1:25–1:55 — Weekly response grid

In the weekly grid:

- mark one cell yes;
- mark another cell no;
- point out pending as the unanswered state;
- briefly show the shared category behavior.

Suggested narration:

> Pending is represented by the absence of a response row, so an unanswered day is never confused with an explicit no.

### 1:55–2:15 — Historical navigation

Use:

- Previous week;
- Next week or Today.

Show that answers persist after navigating away and back.

### 2:15–2:35 — Category management

As owner:

- move one category up or down;
- show the weekly board refresh in the new order;
- mention soft deactivation, but only demonstrate it if you have a disposable category.

Suggested narration:

> Reordering is validated and saved atomically by the backend. Deactivation is a soft delete, so existing response records are preserved.

### 2:35–2:50 — Collaboration

Switch briefly to the member account or show a prepared member window.

Demonstrate that:

- the member can use the board;
- the member does not receive owner-only category controls;
- an individual answer can differ between members.

### 2:50–3:00 — Technical close

Suggested narration:

> LifeBoard uses FastAPI, explicit PostgreSQL with psycopg, signed cookie sessions, and a Next.js TypeScript frontend. GitHub Actions runs the backend PostgreSQL tests plus frontend lint and build checks.

End immediately after the technical summary.

## What not to spend video time on

Do not try to demonstrate every endpoint, test, migration, or error state. The README contains those details. The video should make the product understandable and prove that the core workflow works.

## Final submission checklist

- [ ] Video is 3:00 or shorter.
- [ ] Opening card shows project title.
- [ ] Opening card shows your name.
- [ ] Opening card shows GitHub username.
- [ ] Opening card shows edX username.
- [ ] Opening card shows city and country.
- [ ] Opening card shows recording date.
- [ ] Video is uploaded as public or unlisted, not private.
- [ ] `<VIDEO_URL>` in `README.md` is replaced with the final URL.
- [ ] `README.md` is included at the repository/project root.
- [ ] `.env` and `.env.local` are not submitted with secrets.
- [ ] Backend tests pass.
- [ ] Frontend lint passes.
- [ ] Frontend production build passes.
- [ ] Run `submit50 cs50/problems/2026/x/project` from the project directory.
- [ ] Submit the CS50 final-project form linked from the official project page.
- [ ] Visit the CS50x gradebook after submission and verify completion processing.
