# Legacy Entrypoints

This audit records the old Writer Studio launch/import files that remain after the web architecture cleanup. It is intentionally conservative: no files are deleted in this pass.

## Current Primary Entrypoints

Use these for normal operation:

```text
Start_Web.command
web.py
scripts/start_web_server.sh
scripts/install_autostart.sh
scripts/uninstall_autostart.sh
```

- `Start_Web.command` starts the local Flask server and opens `http://localhost:5001`.
- `web.py` is the thin Flask process entrypoint used by manual runs and launchd.
- `scripts/start_web_server.sh` is a safer script entrypoint for launchd/manual server startup.
- `scripts/install_autostart.sh` and `scripts/uninstall_autostart.sh` manage login autostart.

## Keep

These still have clear compatibility value.

| File | Current role | Notes |
| --- | --- | --- |
| `app.py` | Generation compatibility API/CLI | `run.command` and `scripts/Auto_All.command` still call it. Existing imports may use `app.main(...)` or `run_generator(...)`. |
| `publisher.py` | WeChat publisher compatibility facade | Older scripts/imports can still use `publisher.WeChatPublisher`. `scripts/Auto_All.command` still calls it interactively. |
| `blog_publisher.py` | Blog publisher compatibility facade | Root-level import wrapper around `scripts.plugins.blog_publisher`. Keep while external callers may import from root. |
| `Start_Web.command` | Main manual web launcher | Current user-facing launcher, not legacy. |

## Deprecated But Kept

These are old desktop/script entrypoints. They now either delegate to the web app or print a retirement message. They are safe to keep for old shortcuts.

| File | Current behavior | Recommendation |
| --- | --- | --- |
| `Start_App.command` | Prints a web-app message and delegates to `Start_Web.command`. | Keep for old desktop shortcut compatibility. |
| `WriterStudio_GUI.py` | Prints that the desktop GUI was replaced, then starts the Flask app on port `5001`. | Keep for now; consider changing it to delegate to `web.py` only if duplication becomes annoying. |
| `build_app.command` | Prints that the legacy desktop build is retired. | Keep until old build shortcuts are confirmed unused. |
| `test_editor.py` | Prints that the old tkinter editor test is retired. | Candidate for deletion after one more cleanup pass. |
| `Auto_All.command` | Delegates to `scripts/Auto_All.command`. | Keep only if the old all-in-one terminal workflow is still useful. |
| `run.command` | Runs `app.py` directly. | Keep only if direct generation from `input/` to `output/` is still useful outside the web UI. |
| `scripts/Auto_All.command` | Runs `app.py`, then interactive `publisher.py`. | Deprecated all-in-one CLI flow; keep until confirmed unused. |

## Candidate Deletions Later

Do not delete these automatically. They are only candidates once old shortcuts/imports are confirmed unused:

```text
test_editor.py
build_app.command
Auto_All.command
scripts/Auto_All.command
run.command
```

Before deleting any candidate:

1. Search references with `rg`.
2. Check local macOS shortcuts/Automator/launchd references if applicable.
3. Keep one compatibility release/checkpoint with a clear retirement message before removal.

## Reference Search

Last audit found no runtime references to the retired desktop GUI/editor files outside documentation and their own messages. The meaningful current references are:

- `run.command` -> `app.py`
- `scripts/Auto_All.command` -> `app.py` and `publisher.py`
- `Auto_All.command` -> `scripts/Auto_All.command`
- `Start_App.command` -> `Start_Web.command`
- `writer_studio/web_services.py` -> `scripts.plugins.blog_publisher`

New code should import from `writer_studio/` modules or `scripts.plugins.blog_publisher` directly instead of root compatibility wrappers.
