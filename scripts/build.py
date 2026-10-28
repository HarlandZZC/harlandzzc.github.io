#!/usr/bin/env python3
"""Build the personal website with Python's standard library."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "content/profile.json").read_text(encoding="utf-8"))
BUILD_MARKER = ".haolin-site-build"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_url(url: str) -> str:
    if urlsplit(url).scheme not in ("", "https", "http", "mailto", "tel"):
        raise ValueError(f"Unsupported link scheme: {url}")
    return esc(url)


def external(url: str, label: str, css: str = "") -> str:
    attrs = ' target="_blank" rel="noopener noreferrer"' if url.startswith(("http:", "https:")) else ""
    return (
        f'<a class="{esc(css)}" href="{safe_url(url)}"{attrs}>'
        f"{label}</a>"
    )


INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def inline(text: str) -> str:
    """A small, escaped Markdown subset for author-maintained content."""
    result = []
    for token in INLINE.split(text):
        if token.startswith("**") and token.endswith("**"):
            result.append(f"<strong>{inline(token[2:-2])}</strong>")
        elif token.startswith("`") and token.endswith("`"):
            result.append(f"<code>{esc(token[1:-1])}</code>")
        elif (match := re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)):
            label, url = match.groups()
            result.append(external(url, esc(label)))
        else:
            result.append(esc(token))
    return "".join(result)


def bullets(items: list[str], css: str = "") -> str:
    if not items:
        return ""
    return f'<ul class="{css}">' + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>"


def markdown(text: str) -> str:
    """Headings, paragraphs, lists, quotes, images, and fenced code blocks."""
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    fence: str | None = None
    code: list[str] = []

    def flush() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            close_list()
            if fence is None:
                fence = stripped[3:].strip()
            else:
                language = f' class="language-{esc(fence)}"' if fence else ""
                output.append(f"<pre><code{language}>{esc(chr(10).join(code))}</code></pre>")
                code.clear()
                fence = None
            continue
        if fence is not None:
            code.append(line)
            continue
        if not stripped:
            flush()
            close_list()
            continue
        if (match := re.match(r"^(#{1,6})\s+(.+)$", stripped)):
            flush()
            close_list()
            level = max(2, len(match[1]))
            output.append(f"<h{level}>{inline(match[2])}</h{level}>")
        elif (match := re.match(r"^([-*]|\d+\.)\s+(.+)$", stripped)):
            flush()
            kind = "ul" if match[1] in ("-", "*") else "ol"
            if list_type != kind:
                close_list()
                output.append(f"<{kind}>")
                list_type = kind
            output.append(f"<li>{inline(match[2])}</li>")
        elif stripped.startswith("> "):
            flush()
            close_list()
            output.append(f"<blockquote><p>{inline(stripped[2:])}</p></blockquote>")
        elif (match := re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)):
            flush()
            close_list()
            output.append(
                f'<figure><img src="{safe_url(match[2])}" alt="{esc(match[1])}" loading="lazy">'
                f"<figcaption>{esc(match[1])}</figcaption></figure>"
            )
        elif stripped in ("---", "***"):
            flush()
            close_list()
            output.append("<hr>")
        else:
            close_list()
            paragraph.append(stripped)
    if fence is not None:
        raise ValueError("Unclosed code fence in blog post")
    flush()
    close_list()
    return "\n".join(output)


def bilingual_list(text: str) -> str:
    """Render numbered English/Chinese pairs while preserving each original."""
    items = []
    for number, block in enumerate(re.split(r"\n\s*\n", text.strip()), 1):
        lines = block.splitlines()
        match = re.fullmatch(r"(\d+)\.\s+(.+)", lines[0])
        if not match or int(match[1]) != number or len(lines) < 2:
            raise ValueError("Bilingual posts need numbered English/Chinese pairs")
        english = match[2].strip()
        chinese = " ".join(line.strip() for line in lines[1:])
        items.append(
            f'<li><p lang="en">{inline(english)}</p>'
            f'<p lang="zh-Hans">{inline(chinese)}</p></li>'
        )
    return '<ol class="bilingual-list">\n' + "\n".join(items) + "\n</ol>"


def load_posts() -> list[dict]:
    posts = []
    for path in sorted((ROOT / "content/posts").glob("*.md"), reverse=True):
        raw = path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
        if not match:
            raise ValueError(f"{path.name}: expected Markdown front matter")
        metadata = {}
        for line in match[1].splitlines():
            key, separator, value = line.partition(":")
            if separator:
                metadata[key.strip()] = value.strip().strip('"')
        if metadata.get("draft", "").lower() == "true":
            continue
        date = datetime.strptime(metadata["date"][:10], "%Y-%m-%d")
        slug = metadata.get("slug", path.stem[11:])
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"{path.name}: use a lowercase hyphenated slug")
        body = match[2].strip()
        posts.append({
            **metadata,
            "date": date.strftime("%Y-%m-%d"),
            "display_date": f"{date:%B} {date.day}, {date.year}",
            "short_date": f"{date:%b} {date.day}, {date.year}",
            "year": date.year,
            "path": f"blog/{date.year}/{slug}/index.html",
            "body": bilingual_list(body) if metadata.get("bilingual", "").lower() == "true" else markdown(body),
        })
    paths = [post["path"] for post in posts]
    if len(paths) != len(set(paths)):
        raise ValueError("Blog posts must have unique date/slug combinations")
    return sorted(posts, key=lambda post: post["date"], reverse=True)


def header(prefix: str, active: str) -> str:
    links = []
    for key, name, path in (
        ("about", "About", "index.html"),
        ("pub", "Publications", "pub.html"),
        ("blog", "Blog", "blog/index.html"),
    ):
        state = ' aria-current="page"' if active == key else ""
        links.append(
            f'<a href="{prefix}{path}" class="nav-link"{state}>{name}</a>'
        )
    nav = "".join(links)
    return f"""
    <a class="skip-link" href="#main">Skip to content</a>
    <header class="site-header" id="top">
      <nav class="main-nav" aria-label="Main navigation">{nav}</nav>
    </header>"""


def footer(prefix: str, contact: bool = False) -> str:
    return f"""
    <footer class="site-footer">
      <p>Haolin He <span aria-hidden="true">·</span> Updated {esc(DATA["updated"])}</p>
    </footer>"""


def page(title: str, body: str, active: str, prefix: str = "", description: str = "", contact: bool = False, page_class: str = "") -> str:
    full_title = f"{title} — Haolin He" if title else "Haolin He — Multimodal Learning & Interaction"
    description = description or "Haolin He is a Ph.D. student at CUHK and a research intern at Alibaba's Qwen team, working on multimodal understanding, interaction, and post-training."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="author" content="Haolin He">
  <meta name="theme-color" content="#ffffff">
  <meta name="color-scheme" content="light">
  <meta property="og:type" content="{"article" if page_class == "article-page" else "website"}">
  <meta property="og:title" content="{esc(full_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:site_name" content="Haolin He">
  <title>{esc(full_title)}</title>
  <link rel="icon" href="{prefix}assets/images/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="{prefix}assets/fonts/source-sans-3-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{prefix}assets/fonts/source-serif-4-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{prefix}assets/css/academic.css">
</head>
<body class="{esc(page_class)}">
  <div class="page">
    {header(prefix, active)}
    {body}
    {footer(prefix, contact)}
  </div>
</body>
</html>
"""


def resource_links(pub: dict) -> str:
    return '<div class="resource-links">' + "".join(
        f'[{external(link["url"], esc(link["label"]))}]' for link in pub["links"]
    ) + "</div>"


def home(posts: list[dict]) -> str:
    experience = "".join(
        f'<article class="experience-entry"><div class="entry-heading">'
        f'<h3>{external(item["url"], esc(item["organization"] + " — " + item["team"]))}</h3>'
        f'<span class="entry-date">{esc(item["period"])}</span></div>'
        f'<p class="entry-role">{esc(item["role"])} · {esc(item["focus"])}</p></article>'
        for item in DATA["experience"]
    )
    education = "".join(
        f'<article class="education-entry"><div class="entry-heading">'
        f'<h3>{external(item["url"], esc(item["institution"]))}</h3>'
        f'<span class="entry-date">{esc(item["short_period"])}</span></div>'
        f'<p class="entry-role">{esc(item["degree"])}</p>'
        f'{bullets(item["highlights"])}</article>'
        for item in DATA["education"]
    )
    intro = "".join(f"<p>{inline(text)}</p>" for text in DATA["intro"])
    awards = "".join(
        f'<li><strong>{esc(item["title"])}</strong>, {esc(item["detail"])} ({esc(item["year"])}).</li>'
        for item in DATA["awards"]
    )
    skills = "".join(
        f'<div><dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}</dd></div>' for item in DATA["skills"]
    )
    service = "".join(
        f'<article class="service-entry"><div class="entry-heading">'
        f'<h3>{external(item["url"], esc(item["title"]))}</h3>'
        f'<span class="entry-date">{esc(item["period"])}</span></div>'
        f'<p class="entry-role">{esc(item["role"])}</p></article>'
        for item in DATA["service"]
    )
    body = f"""
    <main id="main">
      <section class="profile-header" aria-labelledby="profile-name">
        <div class="profile-info">
          <h1 id="profile-name"><span>{esc(DATA["name"])}</span><img class="name-calligraphy" src="assets/images/haolin-he-chinese.png" alt="{esc(DATA["name_zh"])}" lang="zh-Hans" width="657" height="206"></h1>
          <p class="profile-role">Ph.D. Student</p>
          <p>Department of Electronic Engineering<br>
            The Chinese University of Hong Kong<br>
            Hong Kong SAR</p>
          <p class="profile-email">Email: {esc(DATA["email"])}</p>
          <div class="social-links" aria-label="Contact and profiles">
            {external(DATA["scholar"], "Google Scholar")}<span aria-hidden="true">/</span>
            {external(DATA["github"], "GitHub")}
          </div>
        </div>
        <figure class="portrait">
          <picture>
            <source srcset="assets/images/haolin-he.webp" type="image/webp">
            <img src="assets/images/haolin-he.jpg" alt="Portrait of Haolin He" width="1000" height="1150" fetchpriority="high">
          </picture>
        </figure>
      </section>
      <section class="section" aria-labelledby="biography-heading">
        <h2 id="biography-heading">Biography</h2>
        <div class="biography">{intro}
          <p>Previously, I was a research intern with the Venus team at Ant Group. I received my B.Eng. in Communication Engineering from the University of Electronic Science and Technology of China in 2024.</p>
        </div>
      </section>
      <section class="section" aria-labelledby="education-heading">
        <h2 id="education-heading">Education</h2>
        {education}
      </section>
      <section class="section" aria-labelledby="experience-heading">
        <h2 id="experience-heading">Internship Experience</h2>
        <div class="experience-list">{experience}</div>
      </section>
      <section class="section" aria-labelledby="service-heading">
        <h2 id="service-heading">Challenges and Academic Service</h2>
        {service}
      </section>
      <section class="section" aria-labelledby="honors-heading">
        <h2 id="honors-heading">Honors and Awards</h2>
        <ul class="award-list">{awards}</ul>
      </section>
      <section class="section" aria-labelledby="skills-heading">
        <h2 id="skills-heading">Skills</h2>
        <dl class="skills-list">{skills}</dl>
      </section>
    </main>"""
    return page("", body, "about", contact=True, page_class="home-page")


def research() -> str:
    groups = []
    for category, heading, anchor in (
        ("report", "Technical reports", "technical-reports"),
        ("first", "First- and co-first-author work", "first-author-work"),
        ("collaboration", "Selected co-authored work", "co-authored-work"),
    ):
        cards = []
        for pub in (p for p in DATA["publications"] if p["category"] == category):
            cards.append(f"""
            <article class="paper-entry" id="{pub['id']}">
              <h3>{external(pub['links'][0]['url'], esc(pub['title']))}</h3>
              <p class="paper-authors">{inline(pub['authors'])}</p>
              <p class="paper-venue"><em>{esc(pub['venue'])}{'' if str(pub['year']) in pub['venue'] else ', ' + str(pub['year'])}.</em> <span>{esc(pub['role'])}.</span></p>
              {resource_links(pub)}
            </article>""")
        groups.append(
            f'<section class="publication-group" aria-labelledby="{anchor}">'
            f'<h2 id="{anchor}">{heading}</h2>{"".join(cards)}</section>'
        )
    body = f"""
    <main id="main">
      <div class="page-heading">
        <h1>Publications</h1>
        <p>My name is shown in <strong>bold</strong>. See also [{external(DATA['scholar'], 'Google Scholar')}].</p>
      </div>
      <div class="publications">{"".join(groups)}</div>
    </main>"""
    return page("Publications", body, "pub", contact=True, page_class="research-page")


def blog(posts: list[dict]) -> str:
    years = []
    for year in sorted({post["year"] for post in posts}, reverse=True):
        entries = "".join(
            f'<article class="blog-entry"><h3><a href="../{post["path"]}">{esc(post["title"])}</a></h3>'
            f'<p class="post-meta"><time datetime="{post["date"]}">{esc(post["display_date"])}</time> · {esc(post.get("tags", "Notes"))}</p>'
            f'<p>{esc(post.get("description", ""))}</p></article>'
            for post in posts if post["year"] == year
        )
        years.append(f'<section class="section"><h2>{year}</h2>{entries}</section>')
    body = f"""
    <main id="main" class="blog-main">
      <div class="page-heading">
        <h1>Blog</h1>
      </div>
      {"".join(years) if years else "<p>No posts yet.</p>"}
    </main>"""
    return page("Blog", body, "blog", "../", "Notes by Haolin He on research, learning, and the Ph.D. journey.", True, "blog-page")


def post_page(post: dict) -> str:
    prefix = "../../../"
    body = f"""
    <main id="main" class="article-main">
      <article>
        <header class="article-heading">
          <h1>{esc(post['title'])}</h1>
          <p class="post-meta">Haolin He · <time datetime="{post['date']}">{esc(post['display_date'])}</time> · {esc(post.get('tags', 'Notes'))}</p>
          <p class="article-deck">{esc(post.get('description', ''))}</p>
        </header>
        <div class="prose post-body">{post['body']}</div>
        <p class="article-back"><a href="../../index.html">← Back to Blog</a></p>
      </article>
    </main>"""
    return page(post["title"], body, "blog", prefix, post.get("description", ""), False, "article-page")


def write(path: str, content: str, output: Path) -> None:
    destination = output / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"Built {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the personal website without third-party dependencies.")
    parser.add_argument(
        "--output", type=Path, default=ROOT,
        help="Output directory; defaults to updating the HTML files beside the source.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    posts = load_posts()
    pages = {
        "index.html": home(posts),
        "pub.html": research(),
        "blog/index.html": blog(posts),
        **{post["path"]: post_page(post) for post in posts},
        "404.html": page(
            "Page not found",
            '<main id="main" class="not-found"><h1>Page not found</h1>'
            '<p>This page may have moved. <a href="index.html">Back to About</a>.</p></main>',
            "", page_class="not-found-page",
        ),
    }
    if output != ROOT:
        protected = [ROOT / name for name in ("assets", "content", "scripts", ".github", ".git")]
        if output in ROOT.parents or any(output == path or path in output.parents for path in protected):
            parser.error("Use a separate build directory, such as --output _site.")
        if output.exists() and not output.is_dir():
            parser.error(f"Output is not a directory: {output}")
        if output.exists() and any(output.iterdir()):
            if not (output / BUILD_MARKER).is_file():
                parser.error(f"Output directory is not empty: {output}. Choose an empty directory.")
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)
        (output / BUILD_MARKER).write_text("Generated by scripts/build.py\n", encoding="utf-8")
        shutil.copytree(ROOT / "assets", output / "assets")

    generated_posts = {post["path"] for post in posts}
    for old in (output / "blog").glob("*/*/index.html"):
        if old.relative_to(output).as_posix() not in generated_posts:
            old.unlink()
    for path, content in pages.items():
        write(path, content, output)
    (output / ".nojekyll").touch()
    print(f"Ready: {output}")


if __name__ == "__main__":
    main()
