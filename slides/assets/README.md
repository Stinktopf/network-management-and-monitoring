# Diagram sources

The deck uses 108 SVG diagrams. Their generators are `../tools/diagrams.py` and `../tools/visual-assets.py`. `../tools/normalize-palette.py` applies the shared colors. Run `npm run diagrams` from `slides/` to rebuild them.

Edit the generators for changes that should survive regeneration. Direct SVG edits also work, but the next generator run overwrites them.

## Data and interpretation

- Protocol and incident diagrams explain relationships. They are not product screenshots or measured traces.
- `b4-traffic-engineering.svg` is a conceptual illustration based on [Google’s B4 paper](https://research.google/pubs/b4-experience-with-a-globally-deployed-software-defined-wan/).
- `capacity-hidden-demand.svg` uses a synthetic 200 ms burst at 75 Mbit/s on the 50 Mbit/s Lagoon egress. Its assumptions are in the slide notes.
- `forecast-comparison.svg` is generated from `../resources/source-graphics/forecast.svg`. Data, predictions and evaluation settings are in `data/`.
- `stale-panel.svg` is an illustration, not a Grafana screenshot.

Headings use Fulda green (`#72bf44`). Diagram labels, connectors and boxes use neutral grays. Green distinguishes the second series in the paired comparison and forecast plots.
