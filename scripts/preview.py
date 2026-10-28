#!/usr/bin/env python3
"""Build and serve this folder. Usage: python scripts/preview.py [port]."""

from __future__ import annotations

import argparse
import functools
import http.server
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview Haolin He's personal website.")
    parser.add_argument("port", nargs="?", type=int, default=8766)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
    handler = functools.partial(PreviewHandler, directory=str(ROOT))
    try:
        server = http.server.ThreadingHTTPServer((args.bind, args.port), handler)
    except OSError as error:
        parser.exit(1, f"Cannot listen on port {args.port}: {error}\nTry a different port.\n")
    print(f"\nPreview: http://localhost:{args.port}\nFolder: {ROOT}\nPress Ctrl+C to stop.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPreview stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
