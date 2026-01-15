# Writer Studio (Web Edition)

A powerful, aesthetic article layout generator and editor for WeChat Official Accounts.
Now available as a Cloud-Ready Web Application.

![Preview](https://via.placeholder.com/800x400?text=Writer+Studio+Preview)

## Features
- **Markdown Editor**: Write comfortably with instant preview.
- **Auto Layout**: Automatically generates "Black Gold" style images for headers, quotes, and covers.
- **WeChat Publishing**: Publish drafts directly to WeChat Official Account.
- **Zero-Knowledge**: Your AppID/Secret are stored in *your* browser, not on the server.
- **Session Isolation**: Supports multiple users simultaneously.

## How to Run

### 1. Cloud Deployment (Recommended)
This project is Docker-ready.
1.  Fork this repo.
2.  Deploy to **Railway**, **Zeabur**, or **Render**.
3.  The platform will auto-detect the `Dockerfile` and build it.

### 2. Local Run (Docker)
```bash
docker-compose up
# Access at http://localhost:5000
```

### 3. Local Run (Python)
```bash
# Install dependencies
pip install -r requirements.txt

# Start Server
./Start_Web.command
# Access at http://localhost:5001
```

## Security
This application is designed with a "Zero-Knowledge" architecture for credentials.
-   **AppID/AppSecret**: Never stored on disk or server database.
-   **Storage**: Persisted only in your browser's `localStorage`.
-   **Transmission**: Sent securely via HTTPS (when deployed) to the server only for the duration of the request.

## License
MIT
