# Haolin He · Personal website

Three standalone pages: **About / Publications / Blog**. The site uses a light gray background, a white content area, and purple headings and links. Body text and headings use Source Serif 4 at different weights. Fonts and photos are stored locally. No npm, Jekyll, or network connection is required to browse the site locally.

## GitHub Pages deployment

The repository includes a GitHub Actions workflow that builds and deploys the site with **Python 3.12**, without third-party Python dependencies.

1. Place this directory's contents at the root of `HarlandZZC/harlandzzc.github.io`, including the hidden `.github/` directory and `.nojekyll` file. Replace the previous website files and remove any old Jekyll workflows.
2. In the repository's **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**. This is a one-time GitHub setting; repository files cannot configure it.
3. Push to `master` or `main`. The **Build and deploy GitHub Pages** workflow automatically builds, checks, and deploys the site. Pull requests only build and check the site; they do not deploy it.

The site is available at `https://harlandzzc.github.io/`. You can also trigger a deployment manually under **Actions → Build and deploy GitHub Pages → Run workflow**. The workflow uses GitHub's automatically provided token; no additional personal access token or API key is required.

Each build reads the latest files in `content/`, so you do not need to regenerate HTML manually before pushing. The HTML files at the repository root are included for local previews. Deployments upload only the static pages, images, and fonts in `_site/`.

## Build and check

Run the same commands used by GitHub Actions from the project root:

```bash
python scripts/build.py --output _site
python scripts/check_site.py _site
```

`_site/` is a generated directory and is refreshed on subsequent builds. The checker validates page entry points, internal links, anchors, image and font paths, and ensures that source files and Git metadata are not included in the deployment.

## Preview

Open `index.html` directly, or run:

```bash
python scripts/preview.py
```

Open `http://localhost:8766`. After editing content, run `python scripts/build.py` and refresh the page.

If the port is already in use:

```bash
python scripts/preview.py 8767
```

In a remote development environment, forward the port to your local machine or use the environment's web preview. You can also download the entire folder and open it locally.

## Files

| Content | File |
| --- | --- |
| About homepage | `index.html` |
| Publications page | `pub.html` |
| Blog index | `blog/index.html` |
| Blog post | `blog/2024/suggestions/index.html` |
| Profile, experience, publications, and awards | `content/profile.json` |
| Blog Markdown sources | `content/posts/` |
| Portrait | `assets/images/haolin-he.jpg`, `.webp` |
| Chinese calligraphic signature | `assets/images/haolin-he-chinese.png` |
| Local fonts and licenses | `assets/fonts/` |
| Colors, typography, and layout | `assets/css/academic.css` |
| Page generator | `scripts/build.py` |
| Pre-deployment checker | `scripts/check_site.py` |
| Automated build and deployment | `.github/workflows/pages.yml` |
| Deployment output (not committed) | `_site/` |

Colors and fonts can be adjusted in the CSS `:root`. The primary color is `--purple: #612968`; body text is 20px on desktop and 19px on small screens, with a line height of 1.4. English blog text uses a line height of 1.45, and Chinese text uses 1.5. Headings are distinguished by typography, size, and horizontal rules. All pages work without JavaScript.

The portrait is cropped at the top and bottom to retain the face and shoulders while removing the shirt logo. Both JPG and WebP versions are 1000 × 1150 pixels. On desktop, the image is 230px wide, aligned with the visible edges of the name and the final profile-link line, with 8px rounded corners. The Chinese signature is a transparent PNG rendered with Ma Shan Zheng calligraphy; its font license is in `assets/fonts/ma-shan-zheng-LICENSE.txt`. The site does not offer a separate CV or PDF download.

## Update profile information

Edit `content/profile.json`, then run:

```bash
python scripts/build.py
```

The profile was originally based on `../cv/cv_haolin_he.tex`. Website data is maintained separately from the original CV, which is not modified by the site generator. Experience, education, publications, and awards appear directly on the About and Publications pages.

Publications are grouped into Technical reports, First- and co-first-author work, and Selected co-authored work, corresponding to the `publications` categories `report`, `first`, and `collaboration`.

## Write a blog post

Add `YYYY-MM-DD-slug.md` to `content/posts/`:

```markdown
---
title: Your post title
date: 2026-10-28
description: A short introduction to this post.
tags: Research
slug: your-post-title
---

## A section

Your text, with **bold**, [links](https://example.com), and `inline code`.

- A point
- Another point
```

Dates must use `YYYY-MM-DD`. Slugs must contain lowercase letters, digits, and hyphens. Supported Markdown includes paragraphs, headings, links, bold text, inline code, code blocks, lists, blockquotes, and images. Add `draft: true` to keep a draft without generating a page. Running `python scripts/build.py` updates the blog index, post pages, and post paths.

“17 Suggestions from My Supervisor” retains its English title, original publication date, and English introduction. Each of its 17 suggestions presents the complete English original followed by its Chinese translation.

For bilingual list posts, set `bilingual: true` in the metadata and format the body as follows, replacing each translation placeholder with Chinese text:

```markdown
1. English content.
   Chinese translation.

2. The next English item.
   The next Chinese translation.
```

## Project scope

The site can be previewed locally or built and deployed through GitHub Actions. Source files, pages, fonts, images, and the `.github/` workflow are included; generated output and local tooling are not committed. The site does not load remote fonts or analytics scripts.
