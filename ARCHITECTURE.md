# Architecture and prioritization

## Product slice

This is a single-workspace, two-user document application. Its core promise is: *write a document, save it, and share it with a teammate who can find and edit it*. The home screen distinguishes owned and shared work, and the editor emphasizes obvious save state and formatting.

## Stack

```text
Browser (HTML/CSS/JS + contenteditable)
       │ Fetch/JSON, X-Demo-User
       ▼
Python standard-library HTTP API (app.py)
       │ parameterized SQL
       ▼
SQLite (docs and shares tables)
```

No package installation or service credentials are required. Document `content` is a restricted HTML fragment, preserving headings, lists, inline emphasis and paragraphs after refresh. The Python HTML sanitizer allows only basic formatting elements, stripping attributes and active content.

Endpoints: `GET/POST /api/documents`, `GET/PATCH/DELETE /api/documents/:id`, `POST /api/import`, `POST /api/documents/:id/share`, `DELETE /api/documents/:id/share/:user`, `GET /api/users`.

Database: `docs(id, title, content, owner_id, version, created_at, updated_at)` and `shares(doc_id, user_id)`. Every document read/update is filtered by owner or explicit share. Share and delete operations require ownership.

## Deliberate priorities

1. **End-to-end vertical slice:** CRUD, formatting, file import, and owner/shared experience work together rather than existing as disconnected mock UI.
2. **Durability:** SQLite persistence, autosave, and a server-assigned version per edit. Stale saves receive 409 rather than silently overwriting another editor.
3. **Reviewability:** One command to start, preconfigured accounts, no registration, tests that exercise HTTP endpoints and permissions.
4. **Focused polish:** Responsive workspace, accessible labels, empty state, save indicators and simple onboarding.

## Tradeoffs / risks

- Demo user selection via `X-Demo-User` makes sharing behavior demonstrable but **is not authentication or secure authorization**. Production would require a session/token validated server-side, an identity provider, CSRF defenses where applicable, and a full permissions audit.
- The editor uses deprecated-but-available browser `execCommand`; a production editor should use Tiptap/ProseMirror or Lexical with a structured document schema and stronger paste/selection behavior.
- No collaborative CRDT / websocket transport. Concurrent updates use optimistic locking only, and the UI does not offer a merge flow.
- SQLite single-instance persistence is ideal for local assessment. For multi-instance cloud scale, migrate to Postgres and shared storage.
- Minimal Markdown parser intentionally covers only common block syntax, not the complete Markdown standard.

## Next 2–4 hours

1. Add actual sign-in / trusted user identity, replacing header-based demo switching.
2. Upgrade the editor to Tiptap/ProseMirror and add reliable semantic clipboard handling.
3. Add a conflict-resolution UI showing your draft versus the current server version.
4. Deploy with managed Postgres or persistent disk, conduct a multi-browser review, and record the walkthrough.
