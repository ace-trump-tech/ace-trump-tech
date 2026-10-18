"""Refresh repository-owned star badges from GitHub; preserve data on failure."""
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OWNER = "ace-trump-tech"
REPOSITORIES = (
    "MindPaw", "DeltaForce-OBS-Locker", "Paper-Harness", "html-lab",
    "template.github.io", "Wifi-killer", "Chatbot",
)
OUTPUT = ROOT / "assets" / "stars"


def count_stars(name):
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    for attempt in range(3):
        try:
            if token:
                request = Request(
                    f"https://api.github.com/repos/{OWNER}/{name}",
                    headers={"Authorization": f"Bearer {token}",
                             "Accept": "application/vnd.github+json",
                             "User-Agent": "profile-star-badges",
                             "X-GitHub-Api-Version": "2022-11-28"},
                )
                with urlopen(request, timeout=25) as response:
                    data = json.load(response)
            else:
                response = subprocess.run(
                    ["gh", "api", f"repos/{OWNER}/{name}"],
                    check=True, capture_output=True, text=True, encoding="utf-8", timeout=30,
                )
                data = json.loads(response.stdout)
            count = data.get("stargazers_count")
            if type(count) is not int or count < 0:
                raise ValueError(f"Invalid star count for {name}")
            return name, count
        except (HTTPError, URLError, TimeoutError, subprocess.SubprocessError):
            if attempt == 2:
                raise RuntimeError(f"Unable to fetch {name}; existing badges were kept") from None
            time.sleep(2 ** attempt)


def badge(name, count):
    right = max(28, len(str(count)) * 8 + 14)
    width = 58 + right
    label = escape(f"{name} stars: {count}", quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}">
  <title>{label}</title>
  <rect width="58" height="20" fill="#555"/>
  <rect x="58" width="{right}" height="20" fill="#ffd700"/>
  <g text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="29" y="14" fill="#fff">★ stars</text>
    <text x="{58 + right / 2:g}" y="14" fill="#332900">{count}</text>
  </g>
</svg>
'''


def main():
    # Finish and validate every request before touching the previous snapshot.
    with ThreadPoolExecutor(max_workers=4) as pool:
        counts = dict(pool.map(count_stars, REPOSITORIES))
    generated = {OUTPUT / f"{name}.svg": badge(name, counts[name]) for name in REPOSITORIES}
    changes = {p: text for p, text in generated.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text}
    if not changes and (OUTPUT / "stats.json").exists():
        print("Star counts are unchanged")
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    snapshot = {"updated_at": datetime.now(timezone.utc).isoformat(),
                "repositories": {f"{OWNER}/{name}": counts[name] for name in REPOSITORIES}}
    changes[OUTPUT / "stats.json"] = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    for path, text in changes.items():
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    print(json.dumps(snapshot["repositories"], ensure_ascii=False))


if __name__ == "__main__":
    main()
