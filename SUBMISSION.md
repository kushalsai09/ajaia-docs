# Ajaia Docs — AI-Native Full Stack Developer Assignment

## Project Links

- Live Application: https://ajaia-docs-6xgn.onrender.com
- Source Code: https://github.com/kushalsai09/ajaia-docs
- Walkthrough Video: https://drive.google.com/file/d/1Qc9weu562wWK7Sw0L8-_G999d1hUNFxF/view?usp=sharing
- Google Drive Submission Folder: To be added

## Project Overview

Ajaia Docs is a lightweight collaborative document editor inspired by Google Docs, built to demonstrate practical full-stack development within a limited timebox.

## Implemented Features

- Create, rename, edit, save, reopen, and delete documents
- Rich-text formatting: bold, italic, underline, headings, and lists
- Autosave with formatting preservation
- Import TXT and basic Markdown files
- Share documents between two demo users
- Owned and shared document views
- SQLite persistence
- Input validation, HTML sanitization, and edit-conflict detection

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python REST-style APIs
- Database: SQLite
- Deployment: Docker and Render
- Version Control: GitHub

## Demo Users

- Alex Morgan — document owner
- Sam Rivera — collaborator

Use the account selector to switch users. No passwords are required because authentication is simulated for this demonstration.

## Architecture and Engineering Decisions

The application uses a lightweight browser frontend communicating with a Python backend through HTTP APIs.

SQLite stores document content, metadata, and sharing permissions.

I prioritized a working document lifecycle and sharing workflow over advanced features such as real-time cursors and simultaneous editing.

Automated backend tests cover document operations, permissions, imports, validation, and version conflicts.

## AI-Native Workflow

ChatGPT was used to accelerate implementation, frontend development, backend scaffolding, automated testing, and documentation.

The implementation was verified using automated tests and manual browser testing of document creation, editing, formatting, file importing, persistence, and sharing.

## Known Limitations

- Authentication uses simulated demo accounts, not production authentication.
- Real-time simultaneous editing and automatic conflict merging are not implemented.
- Render Free uses temporary filesystem storage. Documents may disappear after a server restart or redeployment.
- DOCX import and advanced document formatting are not supported.

## Improvements With Another 2–4 Hours

1. Add durable PostgreSQL storage or a persistent disk.
2. Implement secure authentication.
3. Improve conflict resolution and add deployment-level tests.

## Local Setup

Clone the repository:

    git clone https://github.com/kushalsai09/ajaia-docs.git
    cd ajaia-docs
    python3 app.py

Open http://localhost:8000

Run automated tests:

    python3 -m unittest -v

## Included Files

- app.py
- index.html
- script.js
- styles.css
- test_app.py
- README.md
- ARCHITECTURE.md
- AI_WORKFLOW.md
- SUBMISSION.md
- walkthrough_video_url.txt
- Dockerfile
- .dockerignore
- .gitignore

