"""Compatibility wrapper for the blog publisher plugin."""

from scripts.plugins.blog_publisher import deploy_to_github, publish_to_blog, safe_filename


__all__ = ["deploy_to_github", "publish_to_blog", "safe_filename"]
