import os
import re
import datetime
import json

# Target blog directory (Hardcoded for this user, could be config)
BLOG_POSTS_DIR = "/Users/hugo/personal-blog/posts"


def _yaml_scalar(value):
    """Render a value as a safe YAML scalar.

    A JSON string literal is also a valid YAML double-quoted scalar, so this
    escapes newlines/quotes and prevents user input (e.g. author) from
    injecting additional frontmatter fields.
    """
    return json.dumps(str(value), ensure_ascii=False)


def publish_to_blog(title, content, author="Hugo", custom_slug=None):
    """
    Publish content to the local Next.js blog.
    
    Args:
        title (str): Blog post title.
        content (str): Markdown content.
        author (str): Author name.
        custom_slug (str): Optional custom filename (slug).
    
    Returns:
        str: The full path of the created file.
    """
    if not os.path.exists(BLOG_POSTS_DIR):
        raise FileNotFoundError(f"Blog directory not found: {BLOG_POSTS_DIR}")

    # Generate slug/filename
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if custom_slug:
        slug = safe_filename(custom_slug)
    else:
        # Default: YYYYMMDD-{title_hash} or simplistic slug
        # Just use title if ASCII, else use timestamp
        slug = safe_filename(title)
        if not slug: 
             slug = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    filename = f"{slug}.md"
    file_path = os.path.join(BLOG_POSTS_DIR, filename)
    
    # Generate simple excerpt (first 100 chars of text content)
    clean_text = re.sub(r'[#*`\[\]]', '', content)[:150].replace('\n', ' ').strip() + "..."
    
    # Construct Frontmatter (values JSON-encoded -> safe YAML double-quoted
    # scalars, so newlines/quotes in user input can't inject extra fields)
    frontmatter = f"""---
title: {_yaml_scalar(title)}
excerpt: {_yaml_scalar(clean_text)}
date: {date_str}
author: {_yaml_scalar(author)}
published: true
---

"""
    
    # Write File
    full_content = frontmatter + content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)
        
    print(f"✅ Published to blog: {file_path}")
    return file_path

def deploy_to_github(commit_message="New post from Writer Studio"):
    """Sync to GitHub (which triggers Vercel)."""
    import subprocess
    try:
        print("🚀 Starting GitHub Sync...")
        # 1. Git Add
        subprocess.run(["git", "add", "."], cwd=BLOG_POSTS_DIR.replace("/posts", ""), check=True)
        
        # 2. Git Commit
        # Don't fail if nothing to commit
        subprocess.run(["git", "commit", "-m", commit_message], cwd=BLOG_POSTS_DIR.replace("/posts", ""), check=False)
        
        # 3. Git Push
        result = subprocess.run(
            ["git", "push"], 
            cwd=BLOG_POSTS_DIR.replace("/posts", ""), 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ GitHub Pushed: {result.stdout.strip()}")
            return True, "Synced to GitHub!"
        else:
            print(f"❌ Push Fail: {result.stderr}")
            return False, f"Push Failed: {result.stderr}"
            
    except Exception as e:
        print(f"❌ Git Error: {e}")
        return False, str(e)

def safe_filename(text):
    """Convert text to safe filename (pinyin or english). For now just simple replacement."""
    # Keep alphanumeric, hyphens, and underscores
    # If chinese, relying on caller or just keeping it (modern FS supports utf8)
    # But usually blogs prefer ascii slugs.
    # Let's simple keep safe chars.
    return re.sub(r'[^a-zA-Z0-9\-\u4e00-\u9fa5]', '_', text).strip('_')

if __name__ == "__main__":
    # Test
    publish_to_blog("Test Post", "# Hello World\nThis is a test.")
