# Course slides

366 slides for AI5049, Network Management and Monitoring at Hochschule Fulda.

- [PDF](exports/ai5049-reefnet.pdf)
- [HTML](exports/ai5049-reefnet.html) — download and open in a browser
- [Course outline](docs/course-outline.md)
- [References](REFERENCES.md)
- [Exercise templates](resources/templates/)

## Edit

Edit [ai5049-reefnet.md](ai5049-reefnet.md). The theme is embedded in the Markdown, so the Marp extension for VS Code needs no custom theme registration. Enable HTML in the extension settings.

Theme changes go in [theme/ai5049.css](theme/ai5049.css). The build copies them into the Markdown. Diagrams are local SVGs in `assets/diagrams/`. Their sources and measurement assumptions are documented in [assets/README.md](assets/README.md).

## Build

Requirements:

- Node.js 18+ and npm
- Chromium at `/usr/bin/chromium`, or set `CHROME_PATH`
- Python 3 with PyMuPDF and Pillow for PDF checks and contact sheets

From the repository root:

```bash
cd slides
npm ci
npm run build
```

The HTML and PDF are written to `exports/`. HTML includes the diagrams and can be used offline. The renderer runs Chromium without its browser sandbox, so only build trusted course material.

## Check changes

```bash
npm run qa
npm run check
```

These commands render the deck, check layout, navigation and assets, and create contact sheets in `build/qa/`. Inspect changed slides in the PDF as well. An automated check cannot judge a good line break.

`docs/slide-manifest.json` tracks slide order and section metadata. Update it when moving or replacing slides.

To regenerate diagrams:

```bash
npm run diagrams
npm run qa
npm run check
```

## Style

- Hochschule Fulda green (`#72bf44`) for headings. Neutral gray for diagram boxes and arrows.
- Center text inside diagram nodes and leave space around connectors.
- Short headings, one main point per slide. Shorten content before shrinking type.
- Put essential references in the footer and additional sources in the slide notes.
- Keep navigation off title and day-opening slides.

`node_modules/`, `build/` and internal review notes are local files and are excluded from Git.
