# SVG generator

`python3 scripts/build.py` rewrites every file in `../assets/`.

* Text, numbers and links live in `build.py` (EXP, PROJECTS, SECTIONS, ROW1/ROW2 …).
* `svgkit.py` is the small engine: it schedules several named cursors (Satendra, Angular, Spring Boot …) that drag out boxes, type text and scan in images, and writes it all as CSS keyframes — no JavaScript, so GitHub renders it.
* Needs `pip install pillow` (only to measure text widths). For identical measuring on every machine, drop `Inter-Regular/Medium/SemiBold/Bold/ExtraBold.otf` into `scripts/fonts/`.
* `portrait.webp` is the photo embedded in the hero.

Animation loops: build (2–7 s) → hold (~11 s) → fade → rebuild. Reduced-motion and viewers without CSS animation see the finished picture. Light / dark follow `prefers-color-scheme`.
