# AI-native workflow note

## AI tools used

**ChatGPT (GPT-6)** was used to scope the assignment, generate an initial implementation across the Python API, SQLite schema, frontend, tests, and documentation, and to identify security and deployment tradeoffs.

## Where AI accelerated delivery

AI accelerated decomposition of a broad product brief into an end-to-end vertical slice, routine API/SQL plumbing, design styling, initial test coverage, and documentation. The scope was deliberately constrained to a small editor and two seeded users to preserve time for functional verification.

## Output evaluated or changed

The generated backend initially used SQLite context managers without closing the underlying connections. This was corrected by adding a context manager that explicitly commits/rolls back and closes connections. A polished interface was prioritized over adding unsupported extras such as real-time cursors or DOCX import. The backend also strips untrusted HTML instead of storing pasted markup unchanged.

## Verification performed

Automated integration tests (`python -m unittest -v`) exercise document creation, server-side formatting sanitization, inaccessible documents, owner-only sharing/deletion, shared-user editing, version conflict responses, import and file-type validation. See test output by re-running the command. No claim is made here about an external deployment or a recorded walkthrough; those require real host credentials and a real recording.

## Human judgment and responsibility

The developer should review and understand the generated code and limitations before submission, retest the deployed version and video demo with both seeded accounts, and avoid describing this demo as production-secure. Additional manual browser checks are strongly recommended before final submission.
