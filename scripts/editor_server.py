#!/usr/bin/env python3
"""Manga Studio editor server — stdlib only.

Serves the manga_studio directory statically (editor UI + episode renders) and a tiny
JSON API the editor uses to load/save episode state (variant selection, approvals,
flags, notes, dialogue-for-second-pass).

  GET  /api/episodes            -> {"episodes": [{id, title, panels, approved, rendered}]}
  GET  /api/episode/<id>        -> episode.json
  POST /api/episode/<id>        -> saves body as episode.json (archives a .bak first)

Usage:  python3 editor_server.py [--port 2910] [--host 0.0.0.0]
"""

from __future__ import annotations

import argparse
import json
import shutil
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1]
EPISODES = STUDIO / "episodes"


class Handler(SimpleHTTPRequestHandler):
    # PWA needs these MIME types (stdlib doesn't map .webmanifest by default).
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webmanifest": "application/manifest+json",
        ".js": "text/javascript",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".json": "application/json",
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STUDIO), **kw)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/episodes":
            eps = []
            for d in sorted(EPISODES.iterdir()) if EPISODES.exists() else []:
                f = d / "episode.json"
                if f.exists():
                    ep = json.load(open(f, encoding="utf-8"))
                    eps.append(
                        {
                            "id": d.name,
                            "title": ep.get("title", d.name),
                            "panels": len(ep.get("panels", [])),
                            "approved": sum(
                                1 for p in ep["panels"] if p.get("approved")
                            ),
                            "flagged": sum(1 for p in ep["panels"] if p.get("flagged")),
                            "rendered": sum(
                                len(p.get("variants", [])) for p in ep["panels"]
                            ),
                        }
                    )
            return self._json({"episodes": eps})
        if self.path.startswith("/api/episode/"):
            eid = self.path.rsplit("/", 1)[1]
            f = EPISODES / eid / "episode.json"
            if f.exists():
                return self._json(json.load(open(f, encoding="utf-8")))
            return self._json({"error": "not found"}, 404)
        if self.path in ("/phone", "/phone/"):
            # phone PWA reviewer (installable; one-thumb review)
            self.send_response(302)
            self.send_header("Location", "/editor/phone/index.html")
            self.end_headers()
            return None
        if self.path in ("/", "/editor", "/editor/"):
            # real redirect so the browser's base URL becomes /editor/ and the
            # page's relative asset links (editor.css / editor.js) resolve
            self.send_response(302)
            self.send_header("Location", "/editor/index.html")
            self.end_headers()
            return None
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        if self.path.startswith("/api/episode/"):
            eid = self.path.rsplit("/", 1)[1]
            f = EPISODES / eid / "episode.json"
            if not f.exists():
                return self._json({"error": "not found"}, 404)
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n))
            shutil.copy2(f, f.with_suffix(".json.bak"))  # archive before overwrite
            json.dump(
                data, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False
            )
            return self._json({"ok": True})
        return self._json({"error": "bad endpoint"}, 404)

    def log_message(self, *a):  # quiet
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=2910)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    print(
        f"Manga Studio editor on http://{args.host}:{args.port}/  (studio root: {STUDIO})"
    )
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
