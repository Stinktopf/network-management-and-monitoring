# Visual assets and provenance

The active deck uses **108 local SVGs on 108 slides**. The presentation keeps the supplied course palette: green headings (`#72bf44`), dark text, white/light-gray surfaces and gray connectors. Green distinguishes a second series only in the paired-run and forecast figures. Single-series measurements use the same dark ink throughout. Process arrows, node outlines and decorative accents are neutral.

## Sources

- `tools/diagrams.py` produces the restructured deck's original vector diagrams with the revised neutral treatment.
- `tools/visual-assets.py` builds the additional protocol, forwarding, incident, measurement and review visuals.
- BGP stages, gNMI subscription modes and the citation chain were adapted from supplied diagrams. Five former gray meme panels now use native Marp text. Their original SVGs remain in the historical archive.
- `forecast-comparison.svg` preserves the supplied forecast plot's actual paths and enlarges its labels. Its synthetic data, predictions and summary are in `data/`. Shaded intervals remain excluded; no missing points were interpolated.

The supplied reference deck contains SVG illustrations, not a collection of incident photographs. No fabricated product screenshot or invented measurement is presented as real evidence. `stale-panel.svg` is explicitly an illustrative panel.

Old reference diagrams with unrelated topology/AS numbers were not copied into ReefNet teaching slides. New network diagrams use the current BOB1 roles, documentation addresses and observation conditions.

- `b4-traffic-engineering.svg` is an original conceptual illustration based on [Google’s B4 paper (SIGCOMM 2013)](https://research.google/pubs/b4-experience-with-a-globally-deployed-software-defined-wan/). It shows control decisions, not a packet path.
- `capacity-hidden-demand.svg` shows a synthetic 200 ms burst at 75 Mbit/s on the 50 Mbit/s Lagoon egress. The 10 s output average stays approximately 90%. A finite queue can overflow during the burst. Assumptions and arithmetic are in the slide notes. It is not measured lab data.

## Visual checks

`tools/svg-qa.mjs` checks every active SVG's text bounds, pairwise text collisions and box-edge crossings and strokes through labels in Chromium. This complements whole-slide checks and manual PDF inspection. Source SVGs remain editable and are embedded into the standalone HTML.

Text groups are centered within nodes. Standard process rows use 56 px gaps, with 12 px clearance at both arrow ends. Arrowheads use a fixed 10 px viewport, independent of stroke width. Diagram images are centered by the Marp theme.

The forecast source needed for regeneration is in `resources/source-graphics/`. The active build has no dependency on the historical archive.

Palette roles: main labels and primary data `#303030`, secondary text `#666666`, connectors `#888888`, borders `#cccccc`, grids `#dddddd`, panels `#f6f6f6`, white canvas. The diagram build applies these roles consistently.
