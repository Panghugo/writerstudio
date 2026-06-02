from urllib.parse import quote

from .file_safety import sanitize_session_id


def output_url(session_id, filename, filepath):
    return "/output/{}/{}/{}".format(
        quote(sanitize_session_id(session_id), safe=''),
        quote(filename, safe=''),
        quote(filepath, safe='/'),
    )


def html_artifact(url, filename):
    return {
        "type": "html",
        "url": url,
        "filename": filename,
    }


def image_artifact(url, filename, index=None, total=None):
    artifact = {
        "type": "image",
        "url": url,
        "filename": filename,
    }
    if index is not None:
        artifact["index"] = index
    if total is not None:
        artifact["total"] = total
    return artifact


def zip_artifact(url, filename, count=None):
    artifact = {
        "type": "zip",
        "url": url,
        "filename": filename,
    }
    if count is not None:
        artifact["count"] = count
    return artifact
