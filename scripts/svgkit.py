"""
svgkit — tiny engine that makes "page builds itself" SVGs for a GitHub profile README.

GitHub renders README images through <img>, so there is no JavaScript. Everything here is plain
CSS keyframes inside the SVG:

  * boxes are dragged out by a named cursor,
  * text is typed character by character (a cover rect shrinks in `steps()`, the caret follows),
  * images are scanned in, small icons pop in,
  * several cursors (Satendra, Angular, Spring Boot, …) work in parallel, like a multiplayer editor,
  * after a pause everything fades and rebuilds, so people who scroll down later still see it.

Without animation (reduced motion, e-mail previews, …) the SVG shows its finished state.
Light / dark follow `prefers-color-scheme`.
"""
from __future__ import annotations

import html
import math
import os
from dataclasses import dataclass, field

# ----------------------------------------------------------------------------- fonts (measuring only)
_FONT_DIRS = [
    os.path.join(os.path.dirname(__file__), 'fonts'),
    '/usr/share/fonts/opentype/inter',
    '/usr/share/fonts/truetype/inter',
    '/Library/Fonts',
    os.path.expanduser('~/Library/Fonts'),
]
_WEIGHTS = {400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold'}
_font_cache: dict = {}


def _font(weight: int, mono: bool):
    from PIL import ImageFont  # optional: falls back to an estimate when Pillow / fonts are missing

    key = (weight, mono)
    if key in _font_cache:
        return _font_cache[key]
    cands = []
    if mono:
        cands = ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']
    else:
        for d in _FONT_DIRS:
            cands.append(os.path.join(d, f'Inter-{_WEIGHTS.get(weight, "Medium")}.otf'))
        cands.append('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    f = None
    for p in cands:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, 200)
                break
            except Exception:
                pass
    _font_cache[key] = f
    return f


def measure(text: str, size: float, weight: int = 500, mono: bool = False) -> float:
    try:
        f = _font(weight, mono)
    except Exception:
        f = None
    if f is None:
        return len(text) * size * (0.6 if mono else 0.57)
    return f.getlength(text) * size / 200.0


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ----------------------------------------------------------------------------- palette
CSS_VARS_LIGHT = (
    '--bg:#f3f1ec;--card:#ffffff;--ink:#0e0e10;--muted:#5f5f66;--line:#e2ded3;--soft:#ece9e1;--accent:#2b59ff;'
    '--sh:.16;--bar:#0e0e10'
)
CSS_VARS_DARK = (
    '--bg:#0c0c0e;--card:#151518;--ink:#f4f1ea;--muted:#a3a3ab;--line:#26262b;--soft:#1e1e23;--accent:#88a2ff;'
    '--sh:0;--bar:#f4f1ea'
)
CONST_VARS = '--blue:#2b59ff;--hi:#ffd23f;--black:#0e0e10;--white:#ffffff;--green:#22c55e;--red:#dd0031;--onhi:#0e0e10'

CURSORS = [
    ('Satendra', '#2b59ff'),
    ('Angular', '#dd0031'),
    ('Spring Boot', '#4f9a2a'),
    ('RxJS', '#b7178c'),
    ('TypeScript', '#3178c6'),
    ('Java', '#e8830c'),
]
FONT_STACK = "Inter,'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO_STACK = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"


def col(name: str) -> str:
    """'ink' -> var(--ink); '#fff' stays."""
    if name.startswith('#') or name.startswith('rgb') or name == 'none':
        return name
    return f'var(--{name})'


# ----------------------------------------------------------------------------- items
@dataclass
class Item:
    kind: str  # box | text | media | pop
    x: float
    y: float
    w: float
    h: float
    dep: 'Item | None' = None
    svg: str = ''  # visual markup (box / media / pop)
    # text
    text: str = ''
    size: float = 14
    weight: int = 500
    fill: str = 'ink'
    bg: str = 'card'
    mono: bool = False
    opacity: float = 1.0
    # media
    axis: str = 'y'  # y: scan top->bottom   x: wipe left->right
    cover_r: float = 0
    cover_clip: str = ''
    # results
    t0: float = 0
    t1: float = 0
    cursor: int = -1
    uid: int = 0
    extra_class: str = ''

    @property
    def chars(self) -> int:
        return len(self.text.replace(' ', ''))

    @property
    def entry(self):
        if self.kind == 'text':
            return (self.x, self.y - self.size * 0.92)
        if self.kind == 'media':
            return (self.x, self.y) if self.axis == 'x' else (self.x + self.w / 2, self.y)
        return (self.x, self.y)

    @property
    def exit(self):
        if self.kind == 'text':
            return (self.x + self.w, self.y - self.size * 0.92)
        if self.kind == 'media':
            return (self.x + self.w, self.y + self.h / 2) if self.axis == 'x' else (self.x + self.w / 2, self.y + self.h)
        return (self.x + self.w, self.y + self.h)


@dataclass
class Seg:
    t0: float
    t1: float
    x0: float
    y0: float
    x1: float
    y1: float
    ease: str = 'cubic-bezier(.4,0,.2,1)'
    typing: bool = False
    bar_h: float = 18


class Scene:
    def __init__(self, name: str, w: int, h: int, cursors: int = 4, target: float = 4.2, hold: float = 10.0,
                 panel: bool = True, panel_r: int = 32, label: str = ''):
        self.name, self.w, self.h = name, w, h
        self.n_cursors = min(cursors, len(CURSORS))
        self.target, self.hold = target, hold
        self.items: list[Item] = []
        self.panel = panel
        self.panel_r = panel_r
        self.label = label or name
        self.defs: list[str] = []
        self.statics: list[str] = []  # always visible, drawn before items
        self.extra_css: list[str] = []  # extra css (marquee, rotations …) appended inside the motion media query
        self.extra_anim: list[tuple[str, str]] = []  # custom keyframes needing the loop length: (name, builder)
        self._uid = 0
        self.loop = 0.0
        self.build_end = 0.0
        self.custom: list = []  # callables(scene) -> (css, svg) executed after scheduling

    # ----------------------------------------------------------------- primitives
    def _add(self, it: Item) -> Item:
        self._uid += 1
        it.uid = self._uid
        self.items.append(it)
        return it

    def box(self, x, y, w, h, r=24, fill='card', stroke=None, dep=None, shadow=False, sw=1.2, opacity=1.0):
        parts = []
        if shadow:
            parts.append(f'<rect class="shd" x="{x + 2}" y="{y + 14}" width="{w - 4}" height="{h - 8}" rx="{r}" fill="#000" filter="url(#blur)"/>')
        st = f' stroke="{col(stroke)}" stroke-width="{sw}"' if stroke else ''
        op = f' opacity="{opacity}"' if opacity != 1 else ''
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{col(fill)}"{st}{op}/>')
        return self._add(Item('box', x, y, w, h, dep, svg=''.join(parts)))

    def shape(self, svg: str, x, y, w, h, dep=None):
        """arbitrary box-like markup that is 'dragged out' (rings, circles …)"""
        return self._add(Item('box', x, y, w, h, dep, svg=svg))

    def text(self, x, y, text, size=14, weight=500, fill='ink', bg='card', dep=None, anchor='start', mono=False,
             opacity=1.0):
        w = measure(text, size, weight, mono)
        if anchor == 'middle':
            x -= w / 2
        elif anchor == 'end':
            x -= w
        return self._add(Item('text', x, y, w, size * 1.2, dep, text=text, size=size, weight=weight, fill=fill, bg=bg,
                              mono=mono, opacity=opacity))

    def rich(self, x, y, parts, size=14, maxw=None, line_h=None, bg='card', dep=None):
        """parts: [(text, weight, fill)] — wraps on spaces (a part that starts without a space is glued to the
        previous word, so "Serotask" + "." never splits). Returns (items, y_after)."""
        line_h = line_h or size * 1.5
        words: list[list[tuple]] = []  # word = list of (text, weight, fill) fragments
        prev_space = True
        for t, wt, fl in parts:
            toks = t.split(' ')
            for i, tok in enumerate(toks):
                if tok == '':
                    prev_space = True
                    continue
                if i == 0 and not prev_space and words:
                    words[-1].append((tok, wt, fl))
                else:
                    words.append([(tok, wt, fl)])
                prev_space = False
            if t.endswith(' '):
                prev_space = True
        space = measure(' ', size, 500)
        lines, cur, cur_w = [], [], 0.0
        for wd in words:
            ww = sum(measure(f[0], size, f[1]) for f in wd)
            if maxw and cur and cur_w + space + ww > maxw:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur_w += (space if cur else 0) + ww
            cur.append(wd)
        if cur:
            lines.append(cur)
        items, cy = [], y
        for line in lines:
            px = x
            runs: list[list] = []  # [text, weight, fill, start_x]
            for wi, wd in enumerate(line):
                if wi:
                    px += space
                    if runs and runs[-1][1] == wd[0][1] and runs[-1][2] == wd[0][2]:
                        runs[-1][0] += ' '
                    # (different style: the gap is simply skipped, x offsets come from px)
                for tok, wt, fl in wd:
                    if runs and runs[-1][1] == wt and runs[-1][2] == fl and runs[-1][4] == 'open':
                        runs[-1][0] += tok
                    else:
                        if runs:
                            runs[-1][4] = 'closed'
                        runs.append([tok, wt, fl, px, 'open'])
                    px += measure(tok, size, wt)
                if runs:
                    runs[-1][4] = 'open'
            for text_, wt, fl, sx, _ in runs:
                items.append(self.text(sx, cy, text_.rstrip(), size, wt, fl, bg, dep))
            cy += line_h
        return items, cy

    def media(self, svg, x, y, w, h, bg='card', dep=None, axis='y', cover_r=0, cover_clip=''):
        return self._add(Item('media', x, y, w, h, dep, svg=svg, bg=bg, axis=axis, cover_r=cover_r, cover_clip=cover_clip))

    def pop(self, svg, x, y, w, h, dep=None):
        return self._add(Item('pop', x, y, w, h, dep, svg=svg))

    def static(self, svg):
        self.statics.append(svg)

    # ----------------------------------------------------------------- scheduling
    def _simulate(self, speed: float):
        cursors = []
        for i in range(self.n_cursors):
            side = i % 4
            sx, sy = [(self.w * (0.2 + 0.15 * i), -30), (self.w + 30, self.h * 0.2), (-30, self.h * 0.3), (self.w * 0.5, self.h + 30)][side]
            cursors.append({'free': 0.0, 'x': sx, 'y': sy, 'segs': [], 'sx': sx, 'sy': sy})
        end = 0.0
        for it in self.items:
            dep_end = it.dep.t1 if it.dep else 0.0
            if it.kind == 'pop':
                it.t0 = dep_end + 0.04
                it.t1 = it.t0 + 0.3 / math.sqrt(speed)
                it.cursor = -1
                end = max(end, it.t1)
                continue
            ex, ey = it.entry
            best = None
            for ci, c in enumerate(cursors):
                d = math.hypot(ex - c['x'], ey - c['y'])
                tt = min(0.5, max(0.12, 0.12 + d * 0.0009)) / speed ** 0.7
                st = max(c['free'] + tt, dep_end + 0.02)
                if best is None or st < best[0] - 1e-6:
                    best = (st, ci, tt)
            st, ci, tt = best
            c = cursors[ci]
            if it.kind == 'text':
                dur = 0.12 + max(1, it.chars) / (46.0 * speed)
            elif it.kind == 'box':
                dur = min(0.62, max(0.22, 0.2 + (it.w + it.h) / 2600)) / speed ** 0.6
            else:
                dur = min(0.9, max(0.4, 0.3 + max(it.w, it.h) / 1400)) / speed ** 0.6
            ts = st - tt
            if ts > c['free'] + 1e-6:  # waiting for the parent box: hold position
                c['segs'].append(Seg(c['free'], ts, c['x'], c['y'], c['x'], c['y']))
            c['segs'].append(Seg(ts, st, c['x'], c['y'], ex, ey))
            xx, xy = it.exit
            if it.kind == 'text':
                c['segs'].append(Seg(st, st + dur, ex, ey, xx, xy, ease=f'steps({max(1, it.chars)},end)', typing=True,
                                     bar_h=it.size * 1.15))
            elif it.kind == 'box':
                c['segs'].append(Seg(st, st + dur, ex, ey, xx, xy, ease='cubic-bezier(.22,1,.36,1)'))
            else:
                c['segs'].append(Seg(st, st + dur, ex, ey, xx, xy, ease='cubic-bezier(.4,0,.2,1)'))
            it.t0, it.t1, it.cursor = st, st + dur, ci
            c['free'], c['x'], c['y'] = it.t1, xx, xy
            end = max(end, it.t1)
        return cursors, end

    def schedule(self):
        speed = 1.0
        for _ in range(4):
            cursors, end = self._simulate(speed)
            if end <= self.target * 1.03 and speed <= 1.0:
                break
            speed = max(1.0, speed * end / self.target)
        cursors, end = self._simulate(speed)
        self.speed = speed
        self.build_end = end
        self.loop = round(end + self.hold + 1.4, 2)
        return cursors

    # ----------------------------------------------------------------- output
    def pct(self, t: float) -> str:
        v = max(0.0, min(100.0, t / self.loop * 100))
        return f'{v:.3f}'.rstrip('0').rstrip('.') + '%'

    def render(self) -> str:
        cursors = self.schedule()
        L = self.loop
        css, body = [], []
        pc = self.pct

        for it in self.items:
            k = f'k{it.uid}'
            a, b = pc(it.t0), pc(it.t1)
            if it.kind == 'box':
                body.append(f'<g class="g {k}">{it.svg}</g>')
                css.append(f'@keyframes {k}{{0%,{a}{{transform:scale(0);animation-timing-function:cubic-bezier(.22,1,.36,1)}}{b},100%{{transform:scale(1)}}}}')
                css.append(f'.{k}{{transform-box:fill-box;transform-origin:0 0;animation:{k} {L}s linear infinite}}')
            elif it.kind == 'pop':
                body.append(f'<g class="g {k}">{it.svg}</g>')
                css.append(f'@keyframes {k}{{0%,{a}{{transform:scale(0);opacity:0;animation-timing-function:cubic-bezier(.34,1.56,.64,1)}}{b},100%{{transform:scale(1);opacity:1}}}}')
                css.append(f'.{k}{{transform-box:fill-box;transform-origin:center;animation:{k} {L}s linear infinite}}')
            elif it.kind == 'text':
                fam = MONO_STACK if it.mono else FONT_STACK
                op = f' opacity="{it.opacity}"' if it.opacity != 1 else ''
                ty = it.y
                pad = it.size * 0.25
                n = max(1, it.chars)
                e = 0.02
                a0, b0 = it.t0 / L * 100, it.t1 / L * 100
                body.append(
                    f'<g class="tx t{k}"><text x="{it.x:.2f}" y="{ty:.2f}" font-family="{fam}" font-size="{it.size}" font-weight="{it.weight}" '
                    f'fill="{col(it.fill)}" textLength="{it.w:.2f}" lengthAdjust="spacingAndGlyphs"{op}>{esc(it.text)}</text>'
                    f'<rect class="cv {k}" x="{it.x - 1:.2f}" y="{ty - it.size * 1.05:.2f}" width="{it.w + pad + 1:.2f}" height="{it.size * 1.45:.2f}" fill="{col(it.bg)}"/></g>'
                )
                # the text only exists from t0 on; the cover only during the typing window
                css.append(f'@keyframes t{k}{{0%,{max(a0 - e, 0):.3f}%{{opacity:0}}{a0:.3f}%,100%{{opacity:1}}}}.t{k}{{opacity:0;animation:t{k} {L}s linear infinite}}')
                css.append(f'@keyframes {k}{{0%,{max(a0 - e, 0):.3f}%{{opacity:0;transform:scaleX(1)}}{a0:.3f}%{{opacity:1;transform:scaleX(1);animation-timing-function:steps({n},end)}}'
                           f'{b0:.3f}%{{opacity:1;transform:scaleX(0)}}{min(b0 + e, 100):.3f}%,100%{{opacity:0;transform:scaleX(0)}}}}')
                css.append(f'.{k}{{transform-box:fill-box;transform-origin:100% 0;animation:{k} {L}s linear infinite}}')
            elif it.kind == 'media':
                e = 0.02
                a0, b0 = it.t0 / L * 100, it.t1 / L * 100
                body.append(f'<g><g class="mc m{k}">{it.svg}</g><rect class="cv {k}" x="{it.x - 1}" y="{it.y - 1}" width="{it.w + 2}" height="{it.h + 2}" rx="{it.cover_r}" fill="{col(it.bg)}"{(' clip-path="' + it.cover_clip + '"') if it.cover_clip else ''}/></g>')
                css.append(f'@keyframes m{k}{{0%,{max(a0 - e, 0):.3f}%{{opacity:0}}{a0:.3f}%,100%{{opacity:1}}}}.m{k}{{opacity:0;animation:m{k} {L}s linear infinite}}')
                sc = 'scaleX' if it.axis == 'x' else 'scaleY'
                org = '100% 0' if it.axis == 'x' else '0 100%'
                css.append(f'@keyframes {k}{{0%,{max(a0 - e, 0):.3f}%{{opacity:0;transform:{sc}(1)}}{a0:.3f}%{{opacity:1;transform:{sc}(1);animation-timing-function:cubic-bezier(.4,0,.2,1)}}'
                           f'{b0:.3f}%{{opacity:1;transform:{sc}(0)}}{min(b0 + e, 100):.3f}%,100%{{opacity:0;transform:{sc}(0)}}}}')
                css.append(f'.{k}{{transform-box:fill-box;transform-origin:{org};animation:{k} {L}s linear infinite}}')

        # custom blocks (marquee, slot words, …) get the finished schedule
        for fn in self.custom:
            c_css, c_svg = fn(self)
            css.append(c_css)
            body.append(c_svg)

        # cursors
        cur_svg = []
        for ci, c in enumerate(cursors):
            name, color = CURSORS[ci]
            segs = c['segs']
            if not segs:
                continue
            fw = measure(name, 11, 600) + 14
            kf = []
            first = segs[0]
            kf.append((0.0, first.x0, first.y0, first.ease))
            prev_end = None
            for s in segs:
                if prev_end is None or abs(prev_end - s.t0) > 1e-6:
                    pass
                kf.append((s.t0, s.x0, s.y0, s.ease))
                kf.append((s.t1, s.x1, s.y1, 'linear'))
                prev_end = s.t1
            last = segs[-1]
            # after the build the cursor walks out of the picture
            ex = self.w + 70 if ci % 2 == 0 else -70
            segs.append(Seg(last.t1 + 0.5, last.t1 + 1.3, last.x1, last.y1, ex, min(max(last.y1, 20), self.h - 20)))
            kf.append((last.t1 + 0.5, last.x1, last.y1, 'cubic-bezier(.4,0,.2,1)'))
            kf.append((last.t1 + 1.3, ex, min(max(last.y1, 20), self.h - 20), 'linear'))
            last = segs[-1]
            kf.append((L, last.x1, last.y1, 'linear'))
            # collapse duplicates
            rows, seen = [], {}
            for t, x, y, e in kf:
                key = round(t, 4)
                if key in seen:
                    rows[seen[key]] = (t, x, y, e if e != 'linear' else rows[seen[key]][3])
                    continue
                seen[key] = len(rows)
                rows.append((t, x, y, e))
            frames = ''.join(f'{pc(t)}{{transform:translate({x:.1f}px,{y:.1f}px);animation-timing-function:{e}}}' for t, x, y, e in rows)
            css.append(f'@keyframes cu{ci}{{{frames}}}')
            css.append(f'.cu{ci}{{animation:cu{ci} {L}s linear infinite}}')

            # caret bar / arrow toggling
            typ = [s for s in segs if s.typing]
            bar_f, arr_f = ['0%{opacity:0;transform:scaleY(1)}'], ['0%{opacity:1}']
            eps = 0.02
            last_pct = 0.0
            for s in typ:
                p0 = max(last_pct + eps, s.t0 / L * 100)
                p1 = s.t1 / L * 100
                bar_f.append(f'{p0 - eps:.3f}%{{opacity:0}}{p0:.3f}%{{opacity:1;transform:scaleY({s.bar_h / 18:.3f})}}{p1:.3f}%{{opacity:1}}{p1 + eps:.3f}%{{opacity:0}}')
                arr_f.append(f'{p0 - eps:.3f}%{{opacity:1}}{p0:.3f}%{{opacity:0}}{p1:.3f}%{{opacity:0}}{p1 + eps:.3f}%{{opacity:1}}')
                last_pct = p1 + eps
            bar_f.append('100%{opacity:0}')
            arr_f.append('100%{opacity:1}')
            css.append(f'@keyframes cb{ci}{{{"".join(bar_f)}}}')
            css.append(f'@keyframes ca{ci}{{{"".join(arr_f)}}}')
            css.append(f'.cu{ci} .bar{{animation:cb{ci} {L}s linear infinite}}.cu{ci} .ar{{animation:ca{ci} {L}s linear infinite}}')

            cur_svg.append(
                f'<g class="cur cu{ci}"><rect class="bar" x="-1" y="0" width="2.2" height="18" rx="1" fill="{color}"/>'
                f'<path class="ar" d="M1 1 13 8.6 7.6 10 5.4 16z" fill="{color}" stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/>'
                f'<g class="fl"><rect x="11" y="13" width="{fw:.1f}" height="19" rx="6" fill="{color}"/>'
                f'<text x="18" y="26.2" font-family="{FONT_STACK}" font-size="11" font-weight="600" fill="#fff">{esc(name)}</text></g></g>'
            )

        # global fade-out / rebuild
        f0, f1 = self.build_end + self.hold, self.build_end + self.hold + 0.9
        css.append(f'@keyframes fade{{0%,{pc(f0)}{{opacity:1}}{pc(f1)},100%{{opacity:0}}}}')
        css.append(f'.scene{{animation:fade {L}s linear infinite}}')

        panel = (f'<rect width="{self.w}" height="{self.h}" rx="{self.panel_r}" fill="var(--bg)"/>' if self.panel else '')
        style = (
            f'svg{{{CONST_VARS};{CSS_VARS_LIGHT}}}'
            f'@media (prefers-color-scheme:dark){{svg{{{CSS_VARS_DARK}}}}}'
            '.shd{opacity:var(--sh)}'
            '.cv,.cur{display:none}.bar{transform-box:fill-box;transform-origin:0 0}'
            f'@media (prefers-reduced-motion:no-preference){{.cv,.cur{{display:block}}.cur{{will-change:transform}}'
            + ''.join(css) + ''.join(self.extra_css) + '}'
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.label)}">'
            f'<title>{esc(self.label)}</title>'
            f'<defs><filter id="blur" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur stdDeviation="14"/></filter>{"".join(self.defs)}</defs>'
            f'<style>{style}</style>{panel}{"".join(self.statics)}<g class="scene">{"".join(body)}{"".join(cur_svg)}</g></svg>'
        )
