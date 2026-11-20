#!/usr/bin/env python3
"""Pull the last year of contributions into data/profile.json for render_cards.py.

Token, first one found: $GH_TOKEN, $GITHUB_TOKEN, then `gh auth token` (local runs).
A token from the profile owner (or a PAT with read:user) also counts private
contributions; the Actions job token only sees what the public profile shows.

If the request fails, the previous data/profile.json is kept so the render still runs.

    python scripts/fetch_data.py
"""
import datetime
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "profile.json")
LOGIN = os.environ.get("PROFILE_LOGIN", "Yolooo332")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def token():
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    tok = token()
    if not tok:
        print("fetch_data: no token, keeping the old data/profile.json", file=sys.stderr)
        return
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json",
                 "User-Agent": "profile-cards"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
        cal = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as e:  # network, auth or schema trouble: render from the last good data
        print(f"fetch_data: request failed ({e}), keeping the old data/profile.json", file=sys.stderr)
        return

    days = [[d["date"], d["contributionCount"], LEVELS.get(d["contributionLevel"], 0)]
            for w in cal["weeks"] for d in w["contributionDays"]]
    out = {
        "login": LOGIN,
        "fetched": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "total": cal["totalContributions"],
        "days": days,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
        f.write("\n")
    print(f"fetch_data: {out['total']} contributions over {len(days)} days")


if __name__ == "__main__":
    main()
