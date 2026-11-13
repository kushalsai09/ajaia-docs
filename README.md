# Ajaia Docs — collaborative document workspace

An intentionally scoped Google Docs-inspired full-stack demo. Create and edit rich-text documents, import `.txt` and basic `.md` files, and share documents between two seeded demo accounts. No paid services, database credentials, or package installations are needed to run locally.

## Requirements

- Python 3.10+ (standard library only)
- A modern browser (Chrome or Edge recommended)

## Run locally

```bash
python app.py
```

Open **http://localhost:8000**. On first run the app creates `data/docs.sqlite3` automatically. Set `PORT=8080` to change the port; set `DATABASE_PATH=/path/to/docs.sqlite3` to change persistent storage location.

To run tests:

```bash
python -m unittest -v
```

## Reviewer walkthrough

1. Open the app as **Alex Morgan** (the default seeded demo user).
2. Click **New document**, rename it, type text, apply bold, headings and lists. Changes autosave after a brief pause.
3. Navigate back, reopen the document, and confirm formatting is retained.
4. Click **Share**, select **Sam Rivera**, and grant access.
5. Switch users in the lower-left account menu and choose **Shared with me**. Open and edit the same document as Sam.
6. Switch back to Alex, refresh, and confirm Sam's edits are persisted. As owner, Alex can revoke Sam's access.
7. Use **Import .txt / .md** to import a UTF-8 text or Markdown file as a new editable document.

## Supported editor features

- Create, rename, edit, reopen, delete (owner only)
- Bold / italic / underline, H1–H3, bullets / numbered lists, clear formatting
- Autosave, manual `Ctrl/Cmd+S`, word count, save status
- Import `.txt` or `.md` up to **500 KB**; Markdown supports `#`–`###` headings, `-` / `*` bullets, numbered lists, and plain paragraphs. Inline Markdown emphasis is treated as plain text.
- Owner, shared-with-me document views; editor permission for shared users, owner-only share/delete
- HTML content sanitized on the server (basic formatting tags only)
- Optimistic version check to prevent silently overwriting concurrent edits (returns HTTP 409)

## Limitations (intentional)

- **Demo identity switching, not authentication.** The browser supplies a demo user ID. This is not secure access control for production use. Never enter sensitive data or expose this demo to untrusted users.
- **Not real-time collaboration.** Each user edits individually. If someone else saved since your last load, the server rejects the stale save with a conflict error. Refreshing reloads the latest version; there is no merge UI yet.
- **Editor uses `contenteditable` and built-in browser formatting commands** rather than a large dependency. Cross-browser rich-text behavior can vary; Chrome/Edge are the recommended reviewers' browsers.
- Text-only paste is intentional to avoid untrusted pasted formatting.
- SQLite is persistent on local disk, but **cloud hosting must configure a persistent disk/volume**. Do not rely on temporary filesystems for long-lived demo data.
- No `.docx` support, external email invitations, full Markdown parser, or live cursors.

## Deploy

The included `Dockerfile` builds a standalone container. The service binds to `0.0.0.0:$PORT` (default 8000). Choose a host capable of attaching persistent storage; set `DATABASE_PATH=/data/docs.sqlite3` and mount a persistent volume at `/data`. Expose the service port as your host requires. A host with no persistent volume can be used only as an **ephemeral demo**; documents may disappear after restarts.

**Public-demo warning:** User switching is mock authentication. If publishing externally, use dummy data, keep the demo temporary, and clearly label it as an insecure assessment demo. For a real internal rollout, replace demo users with authentication and trusted server-side identity checks.

A live URL requires deploying the container in your own hosting account; this package does not claim a deployment exists.

## Project files

- `app.py` — HTTP API, SQLite schema, sanitization and file parsing
- `index.html`, `styles.css`, `script.js` — responsive browser interface
- `test_app.py` — end-to-end API tests using an ephemeral SQLite database
- `Dockerfile`, `.dockerignore` — portable container build
- `ARCHITECTURE.md` — product/engineering tradeoffs
- `AI_WORKFLOW.md` — AI usage and verification
- `SUBMISSION.md` — deliverable checklist and outstanding links
- `walkthrough_video_url.txt` — video link placeholder (must be replaced with a real URL)
