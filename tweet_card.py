"""Create and publish a readable source-post image when X has no image."""
import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CARD_DIR = Path("generated_cards")


def _font(size, bold=False):
    name = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def create_tweet_card(tweet_id, username, text):
    """Render the original X post as an image card and return its local path."""
    CARD_DIR.mkdir(exist_ok=True)
    path = CARD_DIR / f"{tweet_id}.png"
    if path.exists():
        return path

    width, padding = 1200, 80
    lines = []
    for paragraph in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(paragraph, width=52) or [""])
    lines = lines[:36]
    height = max(720, 250 + len(lines) * 48)
    image = Image.new("RGB", (width, height), "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, width - 32, height - 32), radius=32, fill="#ffffff")
    draw.text((padding, 90), f"@{username}  ·  X", font=_font(34, True), fill="#111827")
    y = 175
    for line in lines:
        draw.text((padding, y), line, font=_font(31), fill="#1f2937")
        y += 48
    draw.text((padding, height - 105), "Source post shared via X to Threads Bot", font=_font(22), fill="#64748b")
    image.save(path, "PNG", optimize=True)
    return path


def publish_card_to_github(tweet_id, path):
    """Make the generated image public through this repository's raw URL."""
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", str(path)], check=True)
        changed = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
        if changed:
            subprocess.run(["git", "commit", "-m", f"chore: add source card {tweet_id}"], check=True)
            subprocess.run(["git", "push"], check=True)
        repo = os.getenv("GITHUB_REPOSITORY")
        if not repo:
            return None
        return f"https://raw.githubusercontent.com/{repo}/main/{path.as_posix()}"
    except subprocess.CalledProcessError as error:
        print(f"來源貼文卡上傳失敗：{error}")
        return None
