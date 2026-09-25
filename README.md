# Prompt Constructor

A lightweight, zero-external-dependencies Python web application for assembling and editing modular LLM prompts.

## Overview

Prompt Constructor provides a visual workspace for building complex LLM prompts from modular components:
1. **Main Prompts (`data/prompts/`)**: Core system prompts, role definitions, and workflow directives stored as `*.md` files.
2. **Appendices & Snippets (`data/appendices/`)**: Smaller, reusable modifiers, constraints, and output specifications (e.g., chain-of-thought instructions, JSON schemas, concise formatting rules, security boundaries).
3. **Prompt Workbench**: A large interactive editing area with real-time word/character/token estimation, live markdown preview, cursor-aware insertion, and one-click copy to clipboard.

## Features

- **Zero External Dependencies**: Built entirely with Python's standard library (`http.server`, `urllib`, `json`, `dataclasses`, `pathlib`). No Flask, FastAPI, or third-party packages required.
- **Maintainable & Extendable Architecture**:
  - **Models Layer (`prompt_builder/models.py`)**: Strong typing and YAML-like frontmatter metadata parser (`title`, `description`, `tags`).
  - **Repository Layer (`prompt_builder/repository.py`)**: Abstractable storage layer with directory traversal sanitization and safe file access. Can be extended to support SQLite, Git, or S3.
  - **Service Layer (`prompt_builder/services.py`)**: Business logic for listing, searching, filtering, and assembling prompts.
  - **Server Layer (`prompt_builder/server.py`)**: Multi-threaded HTTP server with RESTful API endpoints and static asset delivery.
- **Frontend Workbench (`prompt_builder/static/`)**:
  - Library panel with instant search, category filtering (All, Prompts, Appendices), and live item counts.
  - "+ Append", "Insert at Cursor", and "Replace" actions for any item.
  - Built-in live Markdown preview toggle.
  - One-click "Copy Prompt" with fallback support and `Ctrl+Enter` / `Cmd+Enter` shortcut.
  - "Save As File..." modal to persist new prompts or appendices directly from the web interface.
  - File export (`.md` download).
  - Out-of-the-box template seeding for instant usability.

---

## Directory Structure

```text
/app
├── app.py                     # Application entry point with CLI argument parsing
├── data/
│   ├── prompts/               # Main *.md prompt files
│   └── appendices/            # Reusable appendix / modifier *.md files
├── prompt_builder/
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration dataclass and environment variable handling
│   ├── models.py              # PromptItem data model & markdown frontmatter parser
│   ├── repository.py          # File system repository & path traversal security
│   ├── services.py            # PromptService and default template definitions
│   ├── server.py              # Multi-threaded HTTP server & REST route handlers
│   └── static/
│       ├── index.html         # Responsive single-page workbench UI
│       ├── style.css          # Modern dark slate theme styling
│       └── app.js             # Vanilla JavaScript client application
├── tests/
│   └── test_app.py            # Automated tests using Python standard unittest
└── README.md                  # Documentation
```

---

## Quick Start

### 1. Launch Server

Run using any standard Python 3.8+ interpreter:

```bash
python3 app.py
```

By default, the server starts on `http://localhost:8000`.

### 2. Custom Port and Directories

You can customize the host, port, or markdown directories via command-line arguments:

```bash
python3 app.py --port 9000 --prompts-dir /path/to/my/prompts --appendices-dir /path/to/my/appendices
```

Or via environment variables:

```bash
PORT=9000 PROMPTS_DIR=./custom_prompts python3 app.py
```

---

## Running with Docker

### Option 1: Docker CLI

1. **Build the Docker image**:
   ```bash
   docker build -t prompt-constructor .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name prompt-constructor \
     -p 8000:8000 \
     -v $(pwd)/data/prompts:/app/data/prompts \
     -v $(pwd)/data/appendices:/app/data/appendices \
     prompt-constructor
   ```

3. Open your browser at `http://localhost:8000`.

> **Note on Volumes**: Mounting host directories to `/app/data/prompts` and `/app/data/appendices` ensures your markdown files persist across container restarts.

### Option 2: Docker Compose

Start the service in the background with a single command:

```bash
docker compose up -d
```

To stop:
```bash
docker compose down
```

---

## Format of Prompt & Appendix Files

Files are standard Markdown (`*.md`). They can optionally include YAML frontmatter for custom titles, descriptions, and tags:

```markdown
---
title: Senior Code Reviewer
description: Comprehensive security and architecture review
tags: code, engineering, quality
---

# Senior Code Reviewer

You are an expert software engineer...
```

If frontmatter is omitted, the app automatically extracts the first `# Heading` as the title, or falls back to the formatted filename.

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status check |
| `GET` | `/api/prompts?q=search` | List main prompts |
| `GET` | `/api/prompts/{filename}` | Get a specific prompt by filename |
| `POST` | `/api/prompts` | Create or update a prompt (`{"filename": "...", "content": "..."}`) |
| `DELETE` | `/api/prompts/{filename}` | Delete a prompt |
| `GET` | `/api/appendices?q=search` | List appendix snippets |
| `GET` | `/api/appendices/{filename}` | Get an appendix by filename |
| `POST` | `/api/appendices` | Create or update an appendix |
| `DELETE` | `/api/appendices/{filename}` | Delete an appendix |
| `POST` | `/api/compose` | Compose a prompt from base + appendices |

---

## Running Automated Tests

Run the test suite using Python's built-in `unittest` runner:

```bash
python3 -m unittest discover tests
```
