"""Legacy GUI compatibility entrypoint.

The old tkinter/customtkinter desktop GUI has been retired in favor of the
Flask web app. Keep this file so older shortcuts fail gracefully instead of
raising an import/file-not-found error.
"""

from web import app_server


if __name__ == "__main__":
    print("Writer Studio desktop GUI has been replaced by the web app.")
    print("Open http://localhost:5001 after the server starts.")
    app_server.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
