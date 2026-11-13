# Ajaia AI-Native Full Stack Developer submission

## Included

- [x] Full source code: `app.py`, `index.html`, `script.js`, `styles.css`
- [x] Automated HTTP integration tests: `test_app.py`
- [x] Local setup/run instructions: `README.md`
- [x] Architecture and prioritization: `ARCHITECTURE.md`
- [x] AI workflow note: `AI_WORKFLOW.md`
- [x] Docker build file: `Dockerfile`
- [x] Walkthrough video URL file: `walkthrough_video_url.txt` (currently placeholder)
- [ ] **Live product URL:** REPLACE_WITH_REAL_DEPLOYED_URL
- [ ] **Public 3–5 minute walkthrough video:** REPLACE_WITH_REAL_VIDEO_URL
- [ ] **Google Drive folder link:** REPLACE_WITH_GOOGLE_DRIVE_FOLDER_URL

## Demo accounts

- Alex Morgan — select `Alex` in the left sidebar, demo user 1
- Sam Rivera — select `Sam` in the left sidebar, demo user 2

No password is required because this is simulated identity, not production authentication. All accounts may edit documents shared with them; only the owner can grant/revoke access or delete.

## Working

Creating, renaming, formatting, autosaving, reopening, deleting (owner only), `.txt`/`.md` imports, owner versus shared document views, sharing and revoking shared access, SQLite persistence, and server-side validation/version conflicts. Automated tests cover these flows.

## Partial / incomplete

Public deployment and recorded walkthrough need to be completed by the submitter; no hosting or video account was connected when this package was generated. Demo identity is not genuine authentication, and simultaneous editing is conflict-detected rather than merged. The rich-text toolbar uses browser formatting commands and is optimized for Chrome/Edge.

## Next 2–4 hours

Replace mock authentication, add a conflict-resolution UI, upgrade the editor to a structured-document library, and run end-to-end checks on the final public deployment.

## Quick start

```bash
python app.py
# Open http://localhost:8000
python -m unittest -v
```

## Final submission links

**Drive folder:** [ADD LINK]

**Live product:** [ADD LINK]

**Video:** [ADD LINK]
