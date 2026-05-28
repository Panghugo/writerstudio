# Cleanup Summary

This is the working cleanup inventory after the Writer Studio refactor pass.

## Current Status

The application is running at:

```text
http://localhost:5001
```

The major refactor is functionally verified:

- local page loads
- generation API works
- smoke tests pass
- offline publisher check passes
- real WeChat draft publish was tested successfully by the user

## Main Refactor Areas

### Frontend

The previous large template/script structure has been split into:

```text
templates/index.html
static/css/app.css
static/js/api.js
static/js/settings.js
static/js/publishing.js
static/js/obsidian.js
static/js/uploads.js
static/js/app.js
```

The UI is intended to look the same. The change is mostly internal structure:

- `index.html` is now structural HTML.
- `app.css` owns UI styling.
- `api.js` owns all frontend `fetch(...)` calls.
- `settings.js` owns browser settings/localStorage.
- `publishing.js` owns frontend publish actions.
- `obsidian.js` owns the Obsidian browser modal.
- `uploads.js` owns image upload flows.
- `app.js` coordinates DOM, session/theme state, events, and preview generation.

### Backend

The old `web.py` was split into:

```text
web.py
writer_studio/web_app.py
writer_studio/web_services.py
writer_studio/logging_setup.py
writer_studio/file_safety.py
writer_studio/config.py
```

Current intent:

- `web.py`: launch entrypoint only.
- `web_app.py`: Flask app factory and route registration.
- `web_services.py`: route-facing business actions.
- `logging_setup.py`: logging setup.
- `file_safety.py`: path/name/session safety helpers.
- `config.py`: shared paths and constants.

### Generation Pipeline

The old monolithic generator was split behind `app.py`:

```text
app.py
writer_studio/pipeline.py
writer_studio/renderer.py
writer_studio/preview.py
writer_studio/themes.py
```

`app.py` remains as a compatibility wrapper for older callers.

### Publishing

The WeChat publishing flow is now split into:

```text
publisher.py
writer_studio/wechat_publisher.py
writer_studio/wechat_client.py
writer_studio/wechat_draft.py
writer_studio/wechat_format.py
scripts/check_publisher_offline.py
```

Current intent:

- `publisher.py`: compatibility facade for older imports and CLI usage.
- `wechat_publisher.py`: publish orchestration.
- `wechat_client.py`: WeChat API calls.
- `wechat_draft.py`: generated asset scanning and article data assembly.
- `wechat_format.py`: Markdown-to-WeChat HTML formatting.
- `check_publisher_offline.py`: fake-client check that validates publish assembly without touching WeChat.

## Working Tree Notes

`git status --short` currently includes two kinds of changes:

### Effective Refactor Changes

These are expected parts of the cleanup:

```text
.gitignore
app.py
publisher.py
templates/index.html
web.py
config.template.json
docker-compose.yml
docs/ARCHITECTURE.md
docs/CLEANUP_SUMMARY.md
scripts/
static/
writer_studio/
```

### Legacy Compatibility Entrypoints

These tracked files were old desktop/script entrypoints. They have been kept as lightweight compatibility wrappers instead of being deleted:

```text
Auto_All.command
Start_App.command
WriterStudio_GUI.py
blog_publisher.py
run.command
```

They now either delegate to the new Web/script entrypoints or print a clear retirement message for the old desktop GUI/editor flow.

The retired `build_app.command` and `test_editor.py` wrappers were removed after the legacy entrypoint audit found no runtime references.

See `docs/LEGACY_ENTRYPOINTS.md` for the current keep/deprecate/delete-later audit.

## Ignored Runtime Data

These are runtime/generated data and are ignored:

```text
input/
output/
temp_sessions/
*.log
qtest.png
__pycache__/
config.json
.DS_Store
```

## Verification Commands

Use these before continuing larger refactors:

```bash
./venv/bin/python3 scripts/check_all.py
```

`check_all.py` runs compile checks, smoke tests, text formatting checks, the offline publisher check, and frontend JavaScript syntax checks when Node.js is available.

Optional live API check:

```bash
curl -sS --max-time 20 -H 'Content-Type: application/json' \
  -d '{"filename":"smoke","session_id":"manual","theme":"black_gold","author_name":"Smoke","content":"# Smoke\n\nBody"}' \
  http://127.0.0.1:5001/api/save_and_generate
```

Restart local launchd service:

```bash
launchctl kickstart -k gui/$(id -u)/com.writerstudio.webserver
```

## Suggested Next Step

Before making a commit, review the compatibility entrypoints and confirm this behavior is desired.

Recommended commit grouping:

1. Frontend split and static assets.
2. Backend app/service/logging split.
3. Publisher split and publisher checks.
4. Docs and launch/autostart scripts.

If committing as one checkpoint instead, make sure the deleted legacy files are intentional.
