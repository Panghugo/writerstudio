# Writer Studio Architecture

This document records the current structure after the cleanup pass. It is meant as a quick map for future changes, not a full product spec.

## Runtime Shape

Writer Studio is a local Flask web app served from:

```text
http://localhost:5001
```

The launchd service still starts `web.py`, but `web.py` is now only a small entrypoint. The app is created by `writer_studio.web_app.create_app()`.

## Backend

```text
web.py
```

Entry point for local execution and launchd. It creates `app_server` and runs Flask when executed directly.

```text
writer_studio/web_app.py
```

Flask app factory and route registration. It owns:

- Flask app creation
- CORS setup
- route declarations
- HTTP request/response mapping
- route-level error mapping

Routes should stay thin here. Business work belongs in `web_services.py` or smaller service modules.

```text
writer_studio/web_services.py
```

Backend service layer used by routes. It owns:

- generating previews
- publishing WeChat drafts
- saving uploaded images
- publishing to the local blog
- listing/loading Obsidian files
- theme normalization

This layer coordinates lower-level modules, filesystem paths, and external integrations.

```text
writer_studio/logging_setup.py
```

Central logging setup for Flask, rotating log files, and launchd console output.

```text
writer_studio/file_safety.py
```

Filename/session/path safety helpers. Anything touching user-provided names or session paths should use this module.

```text
writer_studio/config.py
```

Shared paths, allowed theme/image constants, and server config loading.

```text
writer_studio/obsidian.py
```

Obsidian vault integration and image conversion/copying.

```text
writer_studio/pipeline.py
writer_studio/renderer.py
writer_studio/preview.py
writer_studio/themes.py
```

Article generation pipeline:

- `themes.py`: style definitions
- `renderer.py`: image rendering primitives
- `pipeline.py`: Markdown-to-assets orchestration
- `preview.py`: HTML preview/export

```text
app.py
```

Compatibility wrapper around the generation pipeline. Older callers can still call `app.main(...)`.

```text
publisher.py
```

Compatibility facade for older imports and CLI usage. New code should use `writer_studio/wechat_publisher.py`.

```text
writer_studio/wechat_publisher.py
```

WeChat publishing orchestration. It coordinates generated output folders, client calls, draft assembly, and result handling.

```text
writer_studio/wechat_draft.py
```

Generated draft assembly helpers. It owns:

- scanning generated `assets/`
- uploading cover/body assets through an injected upload function
- building WeChat `article_data`

```text
writer_studio/wechat_client.py
```

Low-level WeChat API client. It owns:

- access token retrieval
- cover/body image upload
- draft submission
- request timeout/proxy/header handling

```text
writer_studio/wechat_format.py
```

Markdown-to-WeChat-HTML formatting. It owns inline styles, image tag rendering, quote/lead paragraph formatting, and theme-specific WeChat colors.

## Frontend

```text
templates/index.html
```

Structural HTML only. It loads CSS and the frontend modules.

```text
static/css/app.css
```

Main UI styling extracted from the old template.

```text
static/js/api.js
```

Backend API wrapper. All direct `fetch(...)` calls should stay here.

```text
static/js/dom.js
```

Central DOM lookup map for the main page. Shared page element references should stay here instead of being re-declared in `app.js`.

```text
static/js/editor.js
```

Editor text helpers, including toolbar-driven Markdown insertion.

```text
static/js/generation.js
```

Save-and-generate preview flow. It gathers editor state, calls the backend generation API, updates preview visibility, and reports generation errors through the injected notifier.

```text
static/js/notifications.js
```

Toast/notification rendering helpers.

```text
static/js/settings.js
```

Settings modal and browser `localStorage` config.

```text
static/js/publishing.js
```

Frontend publishing flows for WeChat and blog sync.

```text
static/js/obsidian.js
```

Obsidian file browser modal, file list rendering, search, and file loading.

```text
static/js/session.js
```

Browser session ID creation and persistence.

```text
static/js/theme.js
```

Theme selection initialization and persistence.

```text
static/js/uploads.js
```

Image and feature-image upload flows.

```text
static/js/app.js
```

Frontend entrypoint and UI coordinator. It owns:

- initial editor content
- module configuration
- event binding
- generate-preview event dispatch

## Dynamic Data

These paths are runtime data and should not be committed:

```text
input/
output/
temp_sessions/
*.log
config.json
qtest.png
```

They are ignored in `.gitignore`.

## Verification Commands

Run these after structural changes:

```bash
./venv/bin/python3 scripts/check_all.py
```

For live API verification:

```bash
curl -sS --max-time 20 -H 'Content-Type: application/json' \
  -d '{"filename":"smoke","session_id":"manual","theme":"black_gold","author_name":"Smoke","content":"# Smoke\n\nBody"}' \
  http://127.0.0.1:5001/api/save_and_generate
```

Restart the local launchd service when needed:

```bash
launchctl kickstart -k gui/$(id -u)/com.writerstudio.webserver
```

## Cleanup Notes

Current cleanup status:

- Frontend has been split into focused CSS/JS modules.
- Backend has been split into app factory, route layer, service layer, logging setup, and generation modules.
- Import-time publisher output has been removed.
- WeChat API requests, draft assembly, and WeChat HTML formatting have been extracted from `publisher.py`.

Suggested next refactor:

1. Consider replacing publisher `print(...)` calls with structured logging.
2. Add focused unit tests around `wechat_draft.py` and `wechat_format.py`.
3. Keep `WeChatPublisher.publish_draft(...)` as a compatibility facade until behavior is verified.
