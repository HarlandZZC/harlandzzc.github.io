#!/usr/bin/env python3
"""Check a built site before publishing; requires only Python's standard library."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.references: list[str] = []
        self.headings = 0
        self.title = False
        self.language = False
        self.current_page = 0

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        attrs = dict(attributes)
        if element_id := attrs.get("id"):
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "html":
            self.language = bool(attrs.get("lang"))
        if tag == "title":
            self.title = True
        if tag == "h1":
            self.headings += 1
        if tag == "a" and attrs.get("aria-current") == "page":
            self.current_page += 1
        for attribute in ("href", "src"):
            if value := attrs.get(attribute):
                self.references.append(value)
        if srcset := attrs.get("srcset"):
            self.references.extend(candidate.strip().split()[0] for candidate in srcset.split(",") if candidate.strip())


def check(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    required = ("index.html", "pub.html", "blog/index.html", "404.html", ".nojekyll")
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")

    for name in ("content", "scripts", ".github", ".git", "README.md"):
        if (root / name).exists():
            errors.append(f"Source file or directory included in the deployment: {name}")
    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"Symbolic link in deployment: {path.relative_to(root)}")

    documents: dict[Path, Document] = {}
    for path in sorted(root.rglob("*.html")):
        document = Document()
        document.feed(path.read_text(encoding="utf-8"))
        documents[path] = document
        relative = path.relative_to(root)
        if not document.title or not document.language:
            errors.append(f"{relative}: missing title or document language")
        if document.headings != 1:
            errors.append(f"{relative}: expected one h1, found {document.headings}")
        if path.name != "404.html" and document.current_page != 1:
            errors.append(f"{relative}: expected one active navigation link")
        if document.duplicate_ids:
            errors.append(f"{relative}: duplicate IDs: {', '.join(sorted(document.duplicate_ids))}")

    references = [(path, ref) for path, document in documents.items() for ref in document.references]
    for css in root.rglob("*.css"):
        references.extend(
            (css, match.group(1).strip().strip("\"'"))
            for match in re.finditer(r"url\(([^)]+)\)", css.read_text(encoding="utf-8"))
        )
    for source, reference in references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        if url.path.startswith("/"):
            target = (root / unquote(url.path).lstrip("/")).resolve()
        else:
            target = (source.parent / unquote(url.path)).resolve() if url.path else source
        if not target.is_relative_to(root):
            errors.append(f"{source.relative_to(root)}: reference escapes the site: {reference}")
            continue
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            errors.append(f"{source.relative_to(root)}: missing local target: {reference}")
        elif url.fragment and target in documents and unquote(url.fragment) not in documents[target].ids:
            errors.append(f"{source.relative_to(root)}: missing anchor: {reference}")
    return errors, len(documents), len(references)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("_site"))
    args = parser.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        parser.error(f"Build directory not found: {root}")
    errors, pages, references = check(root)
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    print(f"Passed: {pages} HTML pages, {references} references, local assets and publish directory.")


if __name__ == "__main__":
    main()
