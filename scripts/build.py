#!/usr/bin/env python3
"""
Regenerates every animated SVG in ../assets  (python3 scripts/build.py).
Edit the text / numbers below, run it, commit the new SVGs. Needs: Pillow (only for measuring text widths).
"""
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import Scene, measure, esc, FONT_STACK, MONO_STACK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets')
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(HERE, 'portrait.webp'), 'rb') as f:
    PORTRAIT = base64.b64encode(f.read()).decode()


def write(name, scene):
    svg = scene.render()
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'{name:22s} {len(svg) / 1024:6.1f} KB   loop {scene.loop:5.1f}s   build {scene.build_end:4.1f}s   speed x{scene.speed:.1f}')


def chip(s, x, y, label, dep=None, fill='soft', color='ink', size=12.5, weight=600, h=30, stroke=None, padx=14, bg=None):
    """pill with typed label; returns width"""
    tw = measure(label, size, weight)
    w = tw + padx * 2
    b = s.box(x, y, w, h, r=h / 2, fill=fill, stroke=stroke, dep=dep)
    s.text(x + padx, y + h / 2 + size * 0.35, label, size, weight, color, bg or fill, dep=b)
    return w


# ============================================================================== section headers
SECTIONS = [
    ('sec-01', '01', 'About', '// who am I'),
    ('sec-02', '02', 'Tech Stack', '// what I build with'),
    ('sec-03', '03', 'Experience', "// where I've worked"),
    ('sec-04', '04', 'Impact', '// what it moved'),
    ('sec-05', '05', 'Projects', "// things I've shipped"),
    ('sec-06', '06', 'Angular Utilities', '// @serotask on npm'),
    ('sec-07', '07', 'Education', '// where I learn'),
    ('sec-08', '08', 'Activity', "// what I'm up to"),
    ('sec-09', '09', 'Connect', "// let's talk"),
]


def section(num, title, tag):
    s = Scene(f'sec-{num}', 900, 64, cursors=2, target=1.7, hold=12, panel=True, panel_r=22, label=title)
    c = s.box(20, 14, 36, 36, r=18, fill='ink')
    s.text(38, 37.2, num, 13, 700, 'bg', 'ink', dep=c, anchor='middle')
    t = s.text(72, 41.5, title, 27, 800, 'ink', 'bg')
    s.text(72 + t.w + 16, 40, tag, 13.5, 500, 'muted', 'bg', mono=True)
    return s


# ============================================================================== hero
def hero():
    s = Scene('hero', 900, 450, cursors=6, target=4.6, hold=11,
              label='Satendra Rajput: Senior Software Engineer, Angular and Java Spring Boot')
    # tag pill
    label = 'Senior Software Engineer · Angular + Java'
    tw = measure(label, 13, 600)
    tag = s.box(40, 40, tw + 62, 36, r=18, fill='card', stroke='line')
    s.pop('<circle cx="58" cy="58" r="5" fill="var(--green)"/><circle cx="58" cy="58" r="9" fill="var(--green)" opacity=".18"/>', 49, 49, 18, 18, dep=tag)
    s.text(76, 62.6, label, 13, 600, 'ink', 'card', dep=tag)

    # headline
    s.text(38, 150, 'I build', 66, 800, 'ink', 'bg')
    phrases = ['fintech UIs', 'REST APIs', 'web apps', 'products']
    slot_y = 226
    s.text(38, slot_y, phrases[0], 66, 800, 'accent', 'bg')
    s.text(40, 274, 'with Angular, Java & Spring Boot.', 28, 600, 'muted', 'bg')

    def slot(sc):
        css, svg = [], []
        t0 = sc.build_end + 2.2
        step = 2.0
        tD = t0 + step * 3
        for i, ph in enumerate(phrases[1:], start=1):
            on = t0 + step * (i - 1)
            k = f'slot{i}'
            a, b, c, d = sc.pct(on), sc.pct(on + 0.25), sc.pct(tD), sc.pct(tD + 0.25)
            css.append(f'@keyframes {k}{{0%,{a}{{opacity:0}}{b},{c}{{opacity:1}}{d},100%{{opacity:0}}}}.{k}{{opacity:0;animation:{k} {sc.loop}s linear infinite}}')
            svg.append(
                f'<g class="{k}"><rect x="30" y="{slot_y - 66}" width="450" height="84" fill="var(--bg)"/>'
                f'<text x="38" y="{slot_y}" font-family="{FONT_STACK}" font-size="66" font-weight="800" fill="var(--accent)" '
                f'textLength="{measure(ph, 66, 800):.1f}" lengthAdjust="spacingAndGlyphs">{esc(ph)}</text></g>'
            )
        return ''.join(css), ''.join(svg)

    s.custom.append(slot)

    items, ny = s.rich(40, 316, [('Software engineer with ', 400, 'muted'), ('4.5+ years', 700, 'ink'),
                                  (' building banking & fintech applications. Engineer. Builder. Creator of ', 400, 'muted'),
                                  ('Serotask', 700, 'ink'), ('.', 400, 'muted')], size=15.5, maxw=430, line_h=24, bg='bg')

    # facts
    fx = 40
    for i, (big, small) in enumerate([('4.5+', 'Years experience'), ('Fintech', 'Banking apps'), ('Sero', 'task creator')]):
        if i:
            s.box(fx - 18, 384, 1.6, 44, r=0, fill='line')
        b = s.text(fx, 408, big, 24, 800, 'ink', 'bg')
        sm = s.text(fx, 428, small, 12.5, 500, 'muted', 'bg')
        fx += max(b.w, sm.w) + 40

    # portrait card
    s.defs.append('<clipPath id="pc"><rect x="500" y="36" width="364" height="384" rx="30"/></clipPath>')
    card = s.box(500, 36, 364, 384, r=30, fill='hi')
    rings = ''.join(f'<circle cx="690" cy="330" r="{r}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.5"/>' for r in (150, 112, 74))
    s.shape(f'<g clip-path="url(#pc)">{rings}</g>', 540, 180, 300, 240, dep=card)
    s.media(f'<image href="data:image/webp;base64,{PORTRAIT}" x="500" y="50" width="364" height="370" preserveAspectRatio="xMidYMax slice" clip-path="url(#pc)"/>',
            500, 50, 364, 370, bg='hi', dep=card, axis='y', cover_clip='url(#pc)')

    def badge(x, y, letter, lc, label, w):
        return (f'<g><rect x="{x}" y="{y}" width="{w}" height="42" rx="21" fill="var(--card)" stroke="var(--line)"/>'
                f'<circle cx="{x + 21}" cy="{y + 21}" r="13" fill="{lc}"/>'
                f'<text x="{x + 21}" y="{y + 25.2}" text-anchor="middle" font-family="{FONT_STACK}" font-size="12" font-weight="800" fill="#fff">{letter}</text>'
                f'<text x="{x + 42}" y="{y + 25.5}" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="var(--ink)">{esc(label)}</text></g>')

    bw1 = measure('Angular', 13, 700) + 58
    bw2 = measure('Spring Boot', 13, 700) + 58
    bw3 = measure('years experience', 13, 700) + 68
    s.pop(badge(470, 150, 'A', '#dd0031', 'Angular', bw1), 470, 150, bw1, 42, dep=card)
    s.pop(badge(704, 62, 'S', '#4f9a2a', 'Spring Boot', bw2), 704, 62, bw2, 42, dep=card)
    s.pop(badge(462, 350, '4.5', '#2b59ff', 'years experience', bw3), 462, 350, bw3, 42, dep=card)

    cx, cy = 810, 366
    seal = (f'<g><circle cx="{cx}" cy="{cy}" r="46" fill="var(--black)"/>'
            f'<g class="spin"><path id="sealp" d="M{cx - 33},{cy} a33,33 0 1,1 66,0 a33,33 0 1,1 -66,0" fill="none"/>'
            f'<text font-family="{FONT_STACK}" font-size="8.6" font-weight="700" letter-spacing="1.2" fill="#fff"><textPath href="#sealp" textLength="203" lengthAdjust="spacing">SOFTWARE ENGINEER • FULL STACK •</textPath></text></g>'
            f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-size="22" font-weight="800" fill="var(--hi)" font-family="{FONT_STACK}">↗</text></g>')
    s.pop(seal, cx - 46, cy - 46, 92, 92, dep=card)
    s.extra_css.append('.spin{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}')
    return s


# ============================================================================== about
def about():
    s = Scene('about-card', 900, 330, cursors=5, target=4.0, hold=12, label='About Satendra: Senior Software Engineer, 4.5+ years in banking and fintech')
    left = s.box(24, 24, 560, 282, r=28, fill='card', stroke='line', shadow=True)
    s.text(52, 78, "Hi, I'm Satendra", 34, 800, 'ink', 'card', dep=left)
    s.text(52, 104, 'Senior Software Engineer · Angular + Java Spring Boot', 14, 700, 'accent', 'card', dep=left)
    body = ("I build Axis Bank's Loan Origination System, a business-critical platform for end-to-end loan journeys: "
            "scalable full-stack features, configuration-driven workflows and dealer dashboards. Earlier I shipped "
            "AEPS, Micro-ATM and bill-payment platforms with JWT-based RBAC and biometric device SDKs.")
    items, y = s.rich(52, 134, [(body, 400, 'muted')], size=14.5, maxw=500, line_h=23, bg='card', dep=left)
    cx = 52
    cy = 252
    for lab in ['Axis Bank LOS', 'ADCB LOS', 'AEPS', 'Micro-ATM', 'RBAC']:
        w = chip(s, cx, cy, lab, dep=left, size=12, h=30)
        cx += w + 8

    right = s.box(604, 24, 272, 282, r=28, fill='blue')
    s.text(632, 124, '4.5+', 78, 800, 'white', '#2b59ff', dep=right)
    s.text(632, 158, 'years building banking', 16, 600, '#dfe6ff', '#2b59ff', dep=right)
    s.text(632, 180, '& fintech applications', 16, 600, '#dfe6ff', '#2b59ff', dep=right)
    cx, cy = 632, 206
    for lab in ['Angular 21', 'Spring Boot']:
        tw = measure(lab, 12, 700) + 24
        b = s.box(cx, cy, tw, 28, r=14, fill='#ffffff', dep=right)
        s.text(cx + 12, cy + 18.2, lab, 12, 700, '#0e0e10', '#ffffff', dep=b)
        cx += tw + 8
    cx, cy = 632, 242
    for lab in ['TypeScript', 'RxJS', 'Signals']:
        tw = measure(lab, 12, 700) + 24
        b = s.box(cx, cy, tw, 28, r=14, fill='hi', dep=right)
        s.text(cx + 12, cy + 18.2, lab, 12, 700, '#0e0e10', '#ffd23f', dep=b)
        cx += tw + 8
    return s


# ============================================================================== skills marquee
ROW1 = ['Angular 14-21', 'TypeScript', 'RxJS', 'Signals', 'Zone-less', 'Reactive Forms', 'Angular Material', 'Lazy Loading', 'SCSS', 'Tailwind', 'Bootstrap', 'PWA']
ROW2 = ['Java', 'Spring Boot', 'Spring Security', 'Microservices', 'REST APIs', 'JWT', 'RBAC', 'PostgreSQL', 'MySQL', 'Docker', 'Git', 'GitHub Actions', 'Postman']


def skills():
    s = Scene('skills', 900, 176, cursors=3, target=2.6, hold=12, label='Tech stack: Angular, TypeScript, RxJS, Signals, Java, Spring Boot, PostgreSQL, Docker and more')

    def row(words, y, accent_every=None):
        x, parts = 0.0, []
        for i, wd in enumerate(words):
            tw = measure(wd, 14, 700)
            w = tw + 36
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="44" rx="22" fill="var(--card)" stroke="var(--line)"/>'
                         f'<text x="{x + 18:.1f}" y="{y + 27.5}" font-family="{FONT_STACK}" font-size="14" font-weight="700" fill="var(--ink)" textLength="{tw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(wd)}</text>')
            x += w + 10
            parts.append(f'<path transform="translate({x + 3:.1f},{y + 22})" d="M0-7 2 -2 7 0 2 2 0 7-2 2-7 0-2 -2z" fill="{"var(--accent)" if i % 2 else "var(--hi)"}"/>')
            x += 22
        return ''.join(parts), x

    r1, w1 = row(ROW1, 22)
    r2, w2 = row(ROW2, 96)
    s.defs.append('<clipPath id="mqc"><rect x="0" y="0" width="900" height="176" rx="32"/></clipPath>')
    inner1 = f'<g class="mq1">{r1}<g transform="translate({w1:.1f},0)">{r1}</g></g>'
    inner2 = f'<g class="mq2">{r2}<g transform="translate({w2:.1f},0)">{r2}</g></g>'
    s.media(f'<g clip-path="url(#mqc)">{inner1}{inner2}</g>', 0, 0, 900, 176, bg='bg', axis='x', cover_r=32)
    s.extra_css.append(
        f'.mq1{{animation:mq1 {w1 / 38:.1f}s linear infinite}}@keyframes mq1{{to{{transform:translateX(-{w1:.1f}px)}}}}'
        f'.mq2{{animation:mq2 {w2 / 38:.1f}s linear infinite}}@keyframes mq2{{from{{transform:translateX(-{w2:.1f}px)}}to{{transform:translateX(0)}}}}'
    )
    # soft edge fades so chips glide in/out
    s.static('<defs><linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="var(--bg)"/><stop offset="1" stop-color="var(--bg)" stop-opacity="0"/></linearGradient>'
             '<linearGradient id="fr" x1="1" x2="0"><stop offset="0" stop-color="var(--bg)"/><stop offset="1" stop-color="var(--bg)" stop-opacity="0"/></linearGradient></defs>')
    return s


# ============================================================================== experience
EXP = [
    dict(logo='S', color='#2b59ff', company=None, role='Independent Software Engineer', sub='Serotask · Self-employed',
         meta='Jul 2026 - Present · 4 mos', loc='Noida, Uttar Pradesh, India · Remote',
         bullets=['Building Serotask: 300+ PDF, image, SEO and developer tools with online editors',
                  'Published @serotask/angular-loader and @serotask/angular-toaster',
                  'Own deployment, API infrastructure, domain, SSL and production configuration']),
    dict(logo='V', color='#0e0e10', company='Vastika Technologies', sub='Full-time · 11 mos', loc='Noida, Uttar Pradesh, India · On-site',
         roles=[dict(role='Senior Software Engineer', meta='Oct 2026 - Present · 1 mo',
                     bullets=["Building and enhancing Axis Bank's Loan Origination System (LOS) end to end",
                              'Dynamic, configuration-driven loan workflows and backend-driven UI components',
                              'Dealer-focused apps and dashboards with real-time visibility for business teams']),
                dict(role='Software Engineer', meta='Dec 2025 - Sep 2026 · 10 mos',
                     bullets=['Built Axis Bank LOS modules: application, document upload, eligibility, tracking',
                              'Dynamic UI workflows and dealer-focused loan application features',
                              'Integrated REST APIs; delivered user stories, fixed bugs, improved UI performance'])]),
    dict(logo='R', color='#dd0031', company='Redmil Business Mall', sub='Full-time · 3 yrs 8 mos', loc='Sector 142 Noida, Uttar Pradesh, India · On-site',
         roles=[dict(role='Software Engineer', meta='May 2024 - Nov 2025 · 1 yr 7 mos',
                     bullets=['AEPS, Micro-ATM, Recharge, Bill Payment, Cash-Out modules with end-to-end APIs',
                              'JWT role-based access (Admin, Agent, Retailer) on Spring Boot and Angular 18',
                              'Mantra, Morpho, Micro-ATM SDKs: 90% success rate, transaction errors down 40%']),
                dict(role='Angular Developer', meta='Apr 2022 - Apr 2024 · 2 yrs 1 mo',
                     bullets=['Expanded and optimized Angular applications for financial services',
                              'Reusable dashboard components cut development time for new modules by 40%',
                              'Zone-less patterns and manual change detection cut UI latency by 35%'])]),
]


def experience():
    s = Scene('experience-v2', 900, 960, cursors=6, target=7.0, hold=13, label='Experience: Serotask, Vastika Technologies, Redmil Business Mall')
    X, W = 76, 800
    y = 28
    rail_top = y + 20
    cards = []

    def bullets(card, bx, by, items, dy=23):
        for t in items:
            s.text(bx, by, '▸', 12, 800, 'accent', 'card', dep=card)
            s.text(bx + 18, by, t, 13.2, 500, 'ink', 'card', dep=card)
            by += dy
        return by

    for e in EXP:
        top = y
        if 'bullets' in e:
            h = 24 + 64 + 3 * 23 + 8
        else:
            h = 24 + 64 + 6 + len(e['roles']) * (24 + 3 * 23 + 22) - 4
        card = s.box(X, top, W, h, r=26, fill='card', stroke='line', shadow=True)
        cards.append((card, top, h))
        # rail dot
        s.pop(f'<circle cx="40" cy="{top + 34}" r="9" fill="var(--bg)" stroke="var(--accent)" stroke-width="3"/>', 31, top + 25, 18, 18, dep=card)
        # logo
        s.pop(f'<g><circle cx="{X + 44}" cy="{top + 44}" r="20" fill="{e["color"]}"/><text x="{X + 44}" y="{top + 50.5}" text-anchor="middle" font-family="{FONT_STACK}" font-size="17" font-weight="800" fill="#fff">{e["logo"]}</text></g>',
              X + 24, top + 24, 40, 40, dep=card)
        tx = X + 76
        if 'bullets' in e:
            s.text(tx, top + 40, e['role'], 18, 800, 'ink', 'card', dep=card)
            s.text(tx, top + 60, e['sub'], 13, 500, 'muted', 'card', dep=card)
            s.text(X + W - 28, top + 40, e['meta'], 12.5, 700, 'accent', 'card', dep=card, anchor='end')
            s.text(X + W - 28, top + 60, e['loc'], 12, 500, 'muted', 'card', dep=card, anchor='end')
            bullets(card, tx, top + 96, e['bullets'])
        else:
            s.text(tx, top + 40, e['company'], 18, 800, 'ink', 'card', dep=card)
            s.text(tx, top + 60, e['sub'], 13, 500, 'muted', 'card', dep=card)
            s.text(X + W - 28, top + 60, e['loc'], 12, 500, 'muted', 'card', dep=card, anchor='end')
            ry = top + 100
            for r in e['roles']:
                s.text(tx, ry, r['role'], 15, 700, 'ink', 'card', dep=card)
                s.text(X + W - 28, ry, r['meta'], 12.5, 700, 'accent', 'card', dep=card, anchor='end')
                ry = bullets(card, tx, ry + 24, r['bullets']) + 20
        y += h + 20
    s.h = y + 8
    # rail
    s.shape(f'<rect x="38" y="{rail_top}" width="4" height="{y - rail_top - 24}" rx="2" fill="var(--accent)" opacity=".85"/>', 38, rail_top, 4, y - rail_top - 24)
    return s


# ============================================================================== impact
def impact():
    s = Scene('impact', 900, 200, cursors=4, target=3.2, hold=12, label='Impact: 90% auth success rate, 40% fewer errors, 35% lower latency, 40% less dev effort')
    data = [('90%', 'Biometric auth', 'success rate (SDKs)', 'blue', '#ffffff', '#dfe6ff'),
            ('40%', 'Fewer transaction', 'errors (device SDKs)', 'card', 'ink', 'muted'),
            ('35%', 'Lower UI latency', '(zone-less patterns)', 'hi', '#0e0e10', '#3b3b40'),
            ('40%', 'Less effort for', 'new dashboard modules', 'black', '#ffffff', '#b9b9c0')]
    x = 24
    for big, l1, l2, fill, c1, c2 in data:
        bgc = {'blue': '#2b59ff', 'hi': '#ffd23f', 'black': '#0e0e10'}.get(fill, fill)
        card = s.box(x, 24, 202, 152, r=26, fill=fill, stroke='line' if fill in ('card', 'black') else None, shadow=(fill == 'card'))
        s.text(x + 22, 92, big, 56, 800, c1, bgc, dep=card)
        s.text(x + 22, 124, l1, 14, 700, c1, bgc, dep=card)
        s.text(x + 22, 144, l2, 13, 500, c2, bgc, dep=card)
        x += 202 + 17
    return s


# ============================================================================== projects
PROJECTS = [
    ('Jul 2026 - Present', 'Serotask · Founder Project', 'Building 300+ useful online tools and editors', 'PDF · Image · SEO · Developer tools'),
    ('Feb 2026 - Present', 'Serotask Online Editors', 'PDF and image editing tools with a simple workflow', 'PDF Editor · Image Editor'),
    ('Feb 2026 - Present', 'Axis Bank · Dealer Onboarding', 'Dealer registration, verification, group/entity mapping', 'Angular · Spring Boot · Steppers'),
    ('Dec 2025 - Present', 'ADCB LOS · Borrower Journey', 'Stepper loan flow, document upload, status tracking', 'Angular · Spring Boot · HTML/CSS'),
    ('Sep 2024 - Aug 2025', 'Fintech Platform (AePS, DMT)', 'AEPS, DMT, bill payments, recharges, loans, insurance', 'Java · Angular Material · Spring Boot'),
    ('Apr 2022 - Apr 2024', 'HDFC Loan Applications', 'Loan applications referred to HDFC Bank via Jan Samarth', 'TypeScript · Angular Material'),
]


def projects():
    s = Scene('projects', 900, 480, cursors=6, target=5.0, hold=12, label='Key projects: Serotask, Axis Bank Dealer Onboarding, ADCB LOS, Fintech Platform, HDFC Loan Applications')
    cw, ch, gap = 272, 204, 18
    fills = ['blue', 'card', 'card', 'hi', 'card', 'black']
    for i, (date, title, desc, tech) in enumerate(PROJECTS):
        cx = 24 + (i % 3) * (cw + gap)
        cy = 24 + (i // 3) * (ch + gap)
        fill = fills[i]
        bgc = {'blue': '#2b59ff', 'hi': '#ffd23f', 'black': '#0e0e10'}.get(fill, fill)
        t_main = '#ffffff' if fill in ('blue', 'black') else ('#0e0e10' if fill == 'hi' else 'ink')
        t_mut = '#dfe6ff' if fill == 'blue' else ('#b9b9c0' if fill == 'black' else ('#3b3b40' if fill == 'hi' else 'muted'))
        t_acc = '#ffd23f' if fill in ('blue', 'black') else ('#0e0e10' if fill == 'hi' else 'accent')
        card = s.box(cx, cy, cw, ch, r=26, fill=fill, stroke='line' if fill in ('card', 'black') else None, shadow=(fill == 'card'))
        s.text(cx + 22, cy + 38, date.upper(), 10.5, 800, t_acc, bgc, dep=card)
        s.text(cx + 22, cy + 70, title, 16.5, 800, t_main, bgc, dep=card)
        items, _ = s.rich(cx + 22, cy + 100, [(desc, 400, t_mut)], size=13, maxw=cw - 44, line_h=19, bg=bgc, dep=card)
        s.text(cx + 22, cy + ch - 24, tech, 11.5, 700, t_acc, bgc, dep=card)
    return s


# ============================================================================== npm packages
def tools():
    s = Scene('tools', 900, 268, cursors=4, target=3.6, hold=12, label='Serotask Angular NPM packages: angular-loader and angular-toaster')
    pk = [('@serotask/angular-loader', 'Modern, lightweight Angular loader', '20 animations · HTTP interceptor · Manual control · Global config · Flicker-free · Accessible · SSR-safe', 'npm · v1.0.0'),
          ('@serotask/angular-toaster', 'Modern toast notifications for Angular', '4 types · 6 positions · Queue · Hover-to-pause · Themes · Animations · Actions · Signals · SSR-safe', 'npm · Published')]
    for i, (name, tag, feats, badge) in enumerate(pk):
        x = 24 + i * 438
        card = s.box(x, 24, 426, 220, r=28, fill='card', stroke='line', shadow=True)
        # npm square
        s.pop('<g><rect x="%d" y="46" width="34" height="34" rx="9" fill="#cb3837"/><path d="M%d 54h18v18h-6v-12h-6v12h-6z" fill="#fff"/></g>' % (x + 24, x + 32), x + 24, 46, 34, 34, dep=card)
        s.text(x + 70, 68, name, 13.5, 700, 'accent', 'card', dep=card, mono=True)
        bw = measure(badge, 11, 700) + 22
        b = s.box(x + 426 - bw - 22, 52, bw, 26, r=13, fill='soft', dep=card)
        s.text(x + 426 - bw - 22 + 11, 69, badge, 11, 700, 'ink', 'soft', dep=b)
        s.text(x + 24, 118, tag, 18, 800, 'ink', 'card', dep=card)
        items, _ = s.rich(x + 24, 150, [(feats, 400, 'muted')], size=13, maxw=378, line_h=20, bg='card', dep=card)
    return s


# ============================================================================== education
def education():
    s = Scene('education', 900, 164, cursors=3, target=2.8, hold=12, label='Education: MCA and BCA, Avviare Educational Hub')
    ed = [('Master of Computer Applications', 'Avviare Educational Hub', 'Computer Software Engineering · Jul 2026 - Present', 'blue'),
          ('Bachelor of Computer Applications', 'Avviare Educational Hub · Grade: 72%', 'Computer Software Engineering · Jul 2019 - Jun 2021', 'card')]
    for i, (deg, sch, yr, fill) in enumerate(ed):
        x = 24 + i * 438
        bgc = '#2b59ff' if fill == 'blue' else 'card'
        c1 = '#ffffff' if fill == 'blue' else 'ink'
        c2 = '#dfe6ff' if fill == 'blue' else 'muted'
        card = s.box(x, 24, 426, 116, r=26, fill=fill, stroke='line' if fill == 'card' else None, shadow=(fill == 'card'))
        s.pop(f'<g><circle cx="{x + 46}" cy="82" r="22" fill="{"#ffffff" if fill == "blue" else "var(--hi)"}"/><path d="M{x + 35} 79l11-6 11 6-11 6zM{x + 40} 84v6c3 3 9 3 12 0v-6" fill="none" stroke="#0e0e10" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></g>', x + 24, 60, 44, 44, dep=card)
        s.text(x + 84, 66, deg, 16.5, 800, c1, bgc, dep=card)
        s.text(x + 84, 88, sch, 13, 500, c2, bgc, dep=card)
        s.text(x + 84, 110, yr, 12, 800, '#ffd23f' if fill == 'blue' else 'accent', bgc, dep=card)
    return s


# ============================================================================== footer
def footer():
    s = Scene('footer', 900, 200, cursors=4, target=3.0, hold=12, label='Thanks for stopping by')
    card = s.box(24, 24, 852, 152, r=32, fill='blue')
    s.shape('<circle cx="800" cy="150" r="120" fill="#fff" fill-opacity=".10"/><circle cx="800" cy="150" r="80" fill="#fff" fill-opacity=".10"/>', 680, 30, 196, 146, dep=card)
    s.text(60, 92, 'Thanks for stopping by.', 40, 800, 'white', '#2b59ff', dep=card)
    s.text(62, 126, 'star the repos if you like the work', 16, 600, '#dfe6ff', '#2b59ff', dep=card)
    star = 'M0-11 3.2-3.6 11-3.4 4.9 1.5 7 9 0 4.6-7 9-4.9 1.5-11-3.4-3.2-3.6z'
    for i in range(5):
        s.pop(f'<path transform="translate({66 + i * 30},150)" d="{star}" fill="#ffd23f"/>', 55 + i * 30, 139, 22, 22, dep=card)
    return s


# ============================================================================== divider
def divider():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="22" viewBox="0 0 900 22" role="presentation" aria-hidden="true">'
            '<style>svg{--line:#d9d5ca;--accent:#2b59ff;--hi:#ffd23f}@media (prefers-color-scheme:dark){svg{--line:#2a2a30;--accent:#88a2ff}}'
            '@media (prefers-reduced-motion:no-preference){.tw{transform-box:fill-box;transform-origin:center;animation:tw 3.2s ease-in-out infinite}.tw2{animation-delay:-1.6s}'
            '@keyframes tw{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(1.35) rotate(45deg)}}}</style>'
            '<rect x="24" y="10.2" width="380" height="1.6" rx=".8" fill="var(--line)"/><rect x="496" y="10.2" width="380" height="1.6" rx=".8" fill="var(--line)"/>'
            '<path class="tw" transform="translate(450,11)" d="M0-8 2.2-2.2 8 0 2.2 2.2 0 8-2.2 2.2-8 0-2.2-2.2z" fill="var(--accent)"/>'
            '<path class="tw tw2" transform="translate(428,11) scale(.55)" d="M0-8 2.2-2.2 8 0 2.2 2.2 0 8-2.2 2.2-8 0-2.2-2.2z" fill="var(--hi)"/>'
            '<path class="tw tw2" transform="translate(472,11) scale(.55)" d="M0-8 2.2-2.2 8 0 2.2 2.2 0 8-2.2 2.2-8 0-2.2-2.2z" fill="var(--hi)"/></svg>')


if __name__ == '__main__':
    for fname, num, title, tag in SECTIONS:
        write(f'{fname}.svg', section(num, title, tag))
    write('hero.svg', hero())
    write('about-card.svg', about())
    write('skills.svg', skills())
    write('experience-v2.svg', experience())
    write('impact.svg', impact())
    write('projects.svg', projects())
    write('tools.svg', tools())
    write('education.svg', education())
    write('footer.svg', footer())
    with open(os.path.join(OUT, 'divider.svg'), 'w', encoding='utf-8') as f:
        f.write(divider())
    print('divider.svg')
