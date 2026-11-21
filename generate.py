"""
Generates every animated SVG card used by the profile README.
Run:  python generate.py      ->  writes into ./assets/

All animation is pure SVG (SMIL + CSS) so it plays inside GitHub's <img> sandbox.
No JavaScript, no external fonts. Edit the DATA section to change content.
"""
import math
import os
import random
from xml.sax.saxutils import escape as esc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)
random.seed(27)

# ───────────────────────────── DATA ─────────────────────────────
NAME = "Mehtab Singh"
GH = "MEHTABSINGH1"
ROLES = ["AI Engineer", "ML Developer", "Full-Stack Developer", "LLM + RAG Builder"]
TAGLINE = "B.Tech CSE '26  ·  Minor in AI @ IIT Ropar  ·  Amritsar, India"

# ───────────────────────────── THEME ────────────────────────────
BG0, BG1 = "#060914", "#0d1326"
CYAN, VIOLET, PINK, LIME, AMBER = "#22d3ee", "#a78bfa", "#f472b6", "#a3e635", "#fbbf24"
TXT, DIM, FAINT = "#e2e8f0", "#8b95b0", "#2a3354"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace"
CW = 0.6  # monospace char width as a fraction of font-size

BASE_CSS = f"""
.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}
"""


def svg(w, h, body, css="", title=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        f"<style>{BASE_CSS}{css}</style>{body}</svg>"
    )


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote assets/{name}  ({len(content)/1024:.1f} KB)")


def frame(w, h, rx=22, uid="f"):
    """Dark card background with subtle grid + moving scanline. Returns (defs, body_start)."""
    defs = f"""
    <linearGradient id="{uid}bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
    <pattern id="{uid}grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="{FAINT}" stroke-width="0.6" opacity="0.55"/></pattern>
    <linearGradient id="{uid}scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0.10"/></linearGradient>
    <linearGradient id="{uid}edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{VIOLET}"/>
      <stop offset="1" stop-color="{PINK}"/></linearGradient>
    <clipPath id="{uid}clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
    <filter id="{uid}glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    """
    body = f"""
    <g clip-path="url(#{uid}clip)">
    <rect width="{w}" height="{h}" fill="url(#{uid}bg)"/>
    <rect width="{w}" height="{h}" fill="url(#{uid}grid)"/>
    <rect x="0" y="-120" width="{w}" height="120" fill="url(#{uid}scan)">
      <animate attributeName="y" values="-120;{h}" dur="6s" repeatCount="indefinite"/></rect>
    """
    end = f"""</g>
    <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="{rx}" fill="none"
      stroke="url(#{uid}edge)" stroke-opacity="0.55" stroke-width="1.5"/>"""
    return defs, body, end


def kt(xs):
    return ";".join(f"{x:.4f}".rstrip("0").rstrip(".") if x not in (0, 1) else str(int(x)) for x in xs)


def typing(n, char_px, dur, t0, t_type, t_hold=None, t_erase=None, end_hold=True):
    """Discrete per-character width steps for a clip rect. Times in seconds within `dur`."""
    vals, keys = [0], [0]
    if t0 > 0:
        vals.append(0); keys.append(t0 / dur)
    step = t_type / max(n, 1)
    for i in range(1, n + 1):
        vals.append(i * char_px + 2); keys.append((t0 + i * step) / dur)
    if t_hold is not None and t_erase is not None:
        te = t0 + t_type + t_hold
        vals.append(n * char_px + 2); keys.append(te / dur)
        estep = t_erase / max(n, 1)
        for i in range(n - 1, -1, -1):
            vals.append(i * char_px + (2 if i else 0)); keys.append((te + (n - i) * estep) / dur)
    if keys[-1] < 1:
        vals.append(vals[-1]); keys.append(1)
    # dedupe equal key times (keep last)
    out_v, out_k = [], []
    for v, k in zip(vals, keys):
        if out_k and abs(out_k[-1] - k) < 1e-6:
            out_v[-1] = v
        else:
            out_v.append(v); out_k.append(min(k, 1))
    out_k[-1] = 1
    return out_v, out_k


def appear(dur, t, t_out=None):
    """opacity 0 -> 1 at time t (and optionally back to 0 at t_out), looping every dur."""
    if t_out is None:
        return f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;{t/dur:.4f};{min((t+0.25)/dur,0.999):.4f};1" dur="{dur}s" repeatCount="indefinite"/>'
    return (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{t/dur:.4f};{(t+0.25)/dur:.4f};'
            f'{t_out/dur:.4f};{min((t_out+0.3)/dur,0.999):.4f};1" dur="{dur}s" repeatCount="indefinite"/>')


# ══════════════════════════ 1. HEADER ══════════════════════════
def header():
    W, H = 1200, 420
    d, b, e = frame(W, H, uid="h")
    css = f"""
    .tag{{font:500 18px {MONO};fill:{CYAN};letter-spacing:1px}}
    .name{{font:800 84px {SANS};letter-spacing:-2px}}
    .role{{font:600 30px {MONO};fill:{TXT}}}
    .sub{{font:500 17px {SANS};fill:{DIM}}}
    .chip{{font:600 14px {MONO};fill:{TXT}}}
    .chipk{{font:500 12px {MONO};fill:{DIM}}}
    .lbl{{font:600 11px {MONO};fill:{DIM};letter-spacing:2px}}
    """
    defs = d + f"""
    <filter id="blur80" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="70"/></filter>
    <linearGradient id="nameGrad" gradientUnits="userSpaceOnUse" x1="60" y1="0" x2="620" y2="0" spreadMethod="repeat">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="0.33" stop-color="{VIOLET}"/>
      <stop offset="0.66" stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;560 0" dur="5s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="nodeGrad"><stop offset="0" stop-color="#fff"/><stop offset="0.4" stop-color="{CYAN}"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
    """
    # aurora blobs
    aur = f"""
    <g filter="url(#blur80)" opacity="0.55">
      <ellipse cx="300" cy="80" rx="260" ry="120" fill="{VIOLET}" opacity="0.45">
        <animate attributeName="cx" values="260;420;260" dur="14s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="60;120;60" dur="11s" repeatCount="indefinite"/></ellipse>
      <ellipse cx="900" cy="360" rx="300" ry="120" fill="{CYAN}" opacity="0.35">
        <animate attributeName="cx" values="980;800;980" dur="16s" repeatCount="indefinite"/></ellipse>
      <ellipse cx="700" cy="60" rx="180" ry="90" fill="{PINK}" opacity="0.30">
        <animate attributeName="cy" values="40;140;40" dur="13s" repeatCount="indefinite"/></ellipse>
    </g>"""

    # neural network
    layers = [4, 6, 6, 3]
    xs = [760, 880, 1000, 1120]
    cy, gap = 205, 52
    nodes = []
    for L, (n, x) in enumerate(zip(layers, xs)):
        col = []
        for i in range(n):
            col.append((x, cy + (i - (n - 1) / 2) * gap))
        nodes.append(col)
    edges = []
    for L in range(len(nodes) - 1):
        for a in nodes[L]:
            for c in nodes[L + 1]:
                edges.append(f'<line x1="{a[0]}" y1="{a[1]:.1f}" x2="{c[0]}" y2="{c[1]:.1f}"/>')
    net = f'<g stroke="{VIOLET}" stroke-opacity="0.18" stroke-width="1">{"".join(edges)}</g>'
    # signal particles
    parts = []
    colors = [CYAN, VIOLET, PINK, LIME]
    for k in range(16):
        pts = [random.choice(col) for col in nodes]
        path = "M" + " L".join(f"{p[0]},{p[1]:.1f}" for p in pts)
        c = colors[k % 4]
        dur = random.uniform(2.4, 3.6)
        beg = -random.uniform(0, 4)
        parts.append(
            f'<path d="{path}" fill="none" stroke="{c}" stroke-width="1.6" stroke-opacity="0" >'
            f'<animate attributeName="stroke-opacity" values="0;0.5;0" dur="{dur:.2f}s" begin="{beg:.2f}s" repeatCount="indefinite"/></path>'
            f'<circle r="3.4" fill="{c}" filter="url(#hglow)"><animateMotion dur="{dur:.2f}s" begin="{beg:.2f}s" repeatCount="indefinite" path="{path}"/></circle>'
        )
    node_svg = []
    for L, col in enumerate(nodes):
        for i, (x, y) in enumerate(col):
            beg = (L * 0.35 + i * 0.12)
            node_svg.append(
                f'<circle cx="{x}" cy="{y:.1f}" r="14" fill="url(#nodeGrad)" opacity="0.25">'
                f'<animate attributeName="opacity" values="0.1;0.6;0.1" dur="2.4s" begin="{beg:.2f}s" repeatCount="indefinite"/></circle>'
                f'<circle cx="{x}" cy="{y:.1f}" r="6" fill="{BG0}" stroke="{CYAN}" stroke-width="2"/>'
                f'<circle cx="{x}" cy="{y:.1f}" r="2.5" fill="{TXT}"><animate attributeName="r" values="1.5;3;1.5" dur="2.4s" begin="{beg:.2f}s" repeatCount="indefinite"/></circle>'
            )
    labels = "".join(
        f'<text x="{x}" y="372" text-anchor="middle" class="lbl">{t}</text>'
        for x, t in zip(xs, ["INPUT", "HIDDEN", "HIDDEN", "OUTPUT"])
    )
    out_lbl = "".join(
        f'<text x="{1120+16}" y="{y+4:.1f}" class="lbl" fill="{c}" style="fill:{c}">{t}</text>'
        for (x, y), t, c in zip(nodes[3], ["", "", ""], [CYAN, VIOLET, PINK])
    )

    # name with glitch
    nx, ny = 60, 190
    name = f"""
    <text x="{nx}" y="{ny}" class="name" fill="{PINK}" opacity="0">{NAME}
      <animate attributeName="opacity" values="0;0;0.8;0;0.7;0;0" keyTimes="0;0.86;0.87;0.89;0.9;0.92;1" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="x" values="{nx};{nx};{nx+5};{nx-4};{nx+3};{nx};{nx}" keyTimes="0;0.86;0.87;0.89;0.9;0.92;1" dur="5s" repeatCount="indefinite"/></text>
    <text x="{nx}" y="{ny}" class="name" fill="{CYAN}" opacity="0">{NAME}
      <animate attributeName="opacity" values="0;0;0.8;0;0.7;0;0" keyTimes="0;0.86;0.875;0.885;0.905;0.92;1" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="x" values="{nx};{nx};{nx-5};{nx+4};{nx-3};{nx};{nx}" keyTimes="0;0.86;0.875;0.885;0.905;0.92;1" dur="5s" repeatCount="indefinite"/></text>
    <text x="{nx}" y="{ny}" class="name" fill="url(#nameGrad)">{NAME}</text>
    """

    # role carousel with typing
    rx0, ry0, fs = 100, 254, 30
    cpx = fs * CW
    cyc = 3.6
    DUR = cyc * len(ROLES)
    roles = [f'<text x="62" y="{ry0}" class="role" style="fill:{CYAN}">&gt;</text>']
    for i, r in enumerate(ROLES):
        v, k = typing(len(r), cpx, DUR, 0, 1.1, t_hold=1.7, t_erase=0.5)
        vs, ks = ";".join(f"{x:.1f}" for x in v), kt(k)
        xv = ";".join(f"{rx0 + x:.1f}" for x in v)
        off_t = (1.1 + 1.7 + 0.5 + 0.05) / DUR
        roles.append(f"""
        <clipPath id="rc{i}"><rect x="{rx0}" y="{ry0-30}" height="40" width="0">
          <animate attributeName="width" values="{vs}" keyTimes="{ks}" calcMode="discrete" dur="{DUR}s" begin="{i*cyc}s" repeatCount="indefinite"/></rect></clipPath>
        <g opacity="0">
          <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{off_t:.4f};{off_t+0.001:.4f};1" calcMode="discrete" dur="{DUR}s" begin="{i*cyc}s" repeatCount="indefinite"/>
          <text x="{rx0}" y="{ry0}" class="role" clip-path="url(#rc{i})" textLength="{len(r)*cpx:.1f}" lengthAdjust="spacingAndGlyphs">{esc(r)}</text>
          <rect x="{rx0}" y="{ry0-25}" width="14" height="30" fill="{PINK}">
            <animate attributeName="x" values="{xv}" keyTimes="{ks}" calcMode="discrete" dur="{DUR}s" begin="{i*cyc}s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="1;0.15;1" dur="0.8s" repeatCount="indefinite"/></rect>
        </g>""")

    # chips
    chips_data = [("15+", "projects shipped"), ("3x", "AI/ML internships"), ("10+", "technologies")]
    chips = []
    cx = 60
    for i, (k_, v_) in enumerate(chips_data):
        w = 34 + len(k_) * 9 + len(v_) * 7.4
        chips.append(f"""
        <g transform="translate({cx},318)" opacity="0">
          <animate attributeName="opacity" values="0;1" dur="0.6s" begin="{0.4+i*0.25}s" fill="freeze"/>
          <rect width="{w:.0f}" height="34" rx="17" fill="#ffffff" fill-opacity="0.04" stroke="{[CYAN,VIOLET,PINK][i]}" stroke-opacity="0.5"/>
          <text x="16" y="22" class="chip" style="fill:{[CYAN,VIOLET,PINK][i]}">{k_}</text>
          <text x="{22+len(k_)*9}" y="22" class="chipk">{v_}</text>
        </g>""")
        cx += w + 12

    status = f"""
    <g transform="translate(60,70)">
      <circle cx="6" cy="-6" r="6" fill="{LIME}"><animate attributeName="r" values="5;9;5" dur="1.8s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.8s" repeatCount="indefinite"/></circle>
      <circle cx="6" cy="-6" r="4" fill="{LIME}"/>
      <text x="22" y="0" class="tag" style="fill:{LIME}">available_for_work = True</text>
    </g>
    <text x="60" y="104" class="tag">&lt;hello world, I'm/&gt;</text>
    <text x="60" y="296" class="sub">{esc(TAGLINE)}</text>
    """
    body = b + aur + net + "".join(parts) + "".join(node_svg) + labels + out_lbl + status + name + "".join(roles) + "".join(chips) + e
    write("header.svg", svg(W, H, f"<defs>{defs}</defs>{body}", css, f"{NAME} — {', '.join(ROLES)}"))


# ══════════════════════════ 2. TERMINAL ABOUT ══════════════════════════
def terminal():
    W = 1200
    fs, lh = 17, 29
    cpx = fs * CW
    P = "mehtab@neural-core"
    script = [
        ("cmd", "whoami"),
        ("out", [("Mehtab Singh", TXT), ("  //  AI Engineer · Full-Stack Developer", DIM)]),
        ("cmd", "cat about.json"),
        ("out", [("{", DIM)]),
        ("kv", "location", '"Amritsar, Punjab, India"'),
        ("kv", "education", '["B.Tech CSE (2022-26)", "Minor in AI @ IIT Ropar"]'),
        ("kv", "experience", '["Bharti Airtel", "Croma Campus", "Solitaire Infosys"]'),
        ("kv", "focus", '["Deep Learning", "NLP / LLMs / RAG", "Computer Vision", "MERN"]'),
        ("kv", "mission", '"turn ML research into production-grade apps"'),
        ("kv", "fuel", '"chai, curiosity and late-night debugging"'),
        ("out", [("}", DIM)]),
        ("cmd", "./hire_me --role=ai-engineer"),
        ("out", [("[ OK ] ", LIME), ("handshake accepted  ->  open to full-time roles & internships", TXT)]),
    ]
    H = 66 + lh * len(script) + 40
    d, b, e = frame(W, H, uid="t")
    css = f"""
    .t{{font:500 {fs}px {MONO};fill:{TXT}}}
    .p{{fill:{LIME}}} .pa{{fill:{CYAN}}} .k{{fill:{VIOLET}}} .s{{fill:{AMBER}}}
    .title{{font:600 13px {MONO};fill:{DIM}}}
    """
    DUR = 18.0
    rows, t = [], 0.6
    y = 66 + 24
    for idx, item in enumerate(script):
        if item[0] == "cmd":
            txt = item[1]
            prompt_w = (len(P) + 4) * cpx
            x0 = 40 + prompt_w
            v, k = typing(len(txt), cpx, DUR, t, 0.06 * len(txt))
            rows.append(f"""
            <g opacity="0">{appear(DUR, t)}
              <text x="40" y="{y}" class="t" textLength="{(len(P)+3)*cpx:.1f}" lengthAdjust="spacingAndGlyphs"><tspan class="p">{P}</tspan><tspan fill="{DIM}">:</tspan><tspan class="pa">~</tspan><tspan fill="{DIM}">$</tspan></text>
              <clipPath id="tc{idx}"><rect x="{x0}" y="{y-20}" height="28" width="0">
                <animate attributeName="width" values="{';'.join(f'{q:.1f}' for q in v)}" keyTimes="{kt(k)}" calcMode="discrete" dur="{DUR}s" repeatCount="indefinite"/></rect></clipPath>
              <text x="{x0}" y="{y}" class="t" clip-path="url(#tc{idx})" textLength="{len(txt)*cpx:.1f}" lengthAdjust="spacingAndGlyphs">{esc(txt)}</text>
            </g>""")
            t += 0.06 * len(txt) + 0.45
        elif item[0] == "out":
            spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in item[1])
            rows.append(f'<g opacity="0">{appear(DUR, t)}<text x="40" y="{y}" class="t">{spans}</text></g>')
            t += 0.25
        else:
            _, key, val = item
            pad = " " * (12 - len(key))
            rows.append(
                f'<g opacity="0">{appear(DUR, t)}<text x="40" y="{y}" class="t" xml:space="preserve">'
                f'  <tspan class="k">"{key}"</tspan><tspan fill="{DIM}">:{pad}</tspan><tspan class="s">{esc(val)}</tspan></text></g>'
            )
            t += 0.22
        y += lh
    # final blinking cursor
    rows.append(f"""<g opacity="0">{appear(DUR, t)}
      <text x="40" y="{y}" class="t" textLength="{(len(P)+3)*cpx:.1f}" lengthAdjust="spacingAndGlyphs"><tspan class="p">{P}</tspan><tspan fill="{DIM}">:</tspan><tspan class="pa">~</tspan><tspan fill="{DIM}">$</tspan></text>
      <rect x="{40+(len(P)+4)*cpx}" y="{y-16}" width="10" height="20" fill="{PINK}">
        <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>""")
    chrome = f"""
    <rect width="{W}" height="46" fill="#ffffff" fill-opacity="0.03"/>
    <line x1="0" y1="46" x2="{W}" y2="46" stroke="{FAINT}"/>
    <circle cx="30" cy="23" r="7" fill="#ff5f57"/><circle cx="54" cy="23" r="7" fill="#febc2e"/><circle cx="78" cy="23" r="7" fill="#28c840"/>
    <text x="{W/2}" y="28" text-anchor="middle" class="title">{P}: ~/about  —  zsh  —  120x{len(script)+1}</text>
    <text x="{W-30}" y="28" text-anchor="end" class="title" fill="{CYAN}" style="fill:{CYAN}">● LIVE</text>
    """
    write("about-terminal.svg", svg(W, H + 10, f"<defs>{d}</defs>{b}{chrome}{''.join(rows)}{e}", css, "About Mehtab — terminal"))


# ══════════════════════════ 3. TECH-STACK ORBIT ══════════════════════════
def orbit():
    W, H = 1200, 560
    d, b, e = frame(W, H, uid="o")
    cx, cy = 600, 300
    css = f"""
    .pill{{font:600 14px {MONO};fill:{TXT}}}
    .h{{font:700 22px {MONO};fill:{TXT}}} .hd{{font:500 14px {MONO};fill:{DIM}}}
    .core{{font:800 30px {SANS};fill:{BG0}}}
    .leg{{font:600 12px {MONO};fill:{DIM}}}
    """
    rings = [
        (210, 72, 22, CYAN, "ML CORE", ["Python", "PyTorch", "TensorFlow", "Scikit-learn"]),
        (360, 132, 34, VIOLET, "AI / DATA", ["LangChain", "Hugging Face", "OpenAI API", "RAG", "OpenCV", "Pandas", "NumPy"]),
        (530, 205, 52, PINK, "BUILD / SHIP", ["React", "Next.js", "TypeScript", "Node.js", "Express", "MongoDB", "SQL", "Docker", "AWS", "Git"]),
    ]
    defs = d + f"""
    <radialGradient id="coreG"><stop offset="0" stop-color="#ffffff"/><stop offset="0.35" stop-color="{CYAN}"/>
      <stop offset="0.75" stop-color="{VIOLET}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
    <filter id="obl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="40"/></filter>
    """
    g = [f'<ellipse cx="{cx}" cy="{cy}" rx="420" ry="160" fill="{VIOLET}" opacity="0.12" filter="url(#obl)"/>']
    for rx, ry, dur, col, lbl, items in rings:
        g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity="0.28" stroke-width="1.2" stroke-dasharray="4 7">'
                 f'<animate attributeName="stroke-dashoffset" values="0;-110" dur="6s" repeatCount="indefinite"/></ellipse>')
    # core
    g.append(f"""
    <circle cx="{cx}" cy="{cy}" r="70" fill="url(#coreG)" opacity="0.5">
      <animate attributeName="r" values="60;82;60" dur="3s" repeatCount="indefinite"/></circle>
    <circle cx="{cx}" cy="{cy}" r="44" fill="{CYAN}"/>
    <circle cx="{cx}" cy="{cy}" r="44" fill="none" stroke="#fff" stroke-opacity="0.6" stroke-width="2">
      <animate attributeName="r" values="44;90" dur="2.4s" repeatCount="indefinite"/>
      <animate attributeName="stroke-opacity" values="0.6;0" dur="2.4s" repeatCount="indefinite"/></circle>
    <text x="{cx}" y="{cy+10}" text-anchor="middle" class="core">AI</text>
    """)
    for rx, ry, dur, col, lbl, items in rings:
        path = f"M{cx-rx},{cy} a{rx},{ry} 0 1,0 {2*rx},0 a{rx},{ry} 0 1,0 {-2*rx},0"
        n = len(items)
        for i, it in enumerate(items):
            w = len(it) * 8.6 + 28
            beg = -dur * i / n
            g.append(f"""
            <g><animateMotion dur="{dur}s" begin="{beg:.2f}s" repeatCount="indefinite" path="{path}"/>
              <rect x="{-w/2:.1f}" y="-15" width="{w:.1f}" height="30" rx="15" fill="{BG0}" stroke="{col}" stroke-width="1.4"/>
              <circle cx="{-w/2+13:.1f}" cy="0" r="3.5" fill="{col}"/>
              <text x="{-w/2+22:.1f}" y="5" class="pill">{esc(it)}</text></g>""")
    head = f"""
    <text x="40" y="52" class="h"><tspan fill="{PINK}">const</tspan> stack <tspan fill="{DIM}">=</tspan> <tspan fill="{CYAN}">orbit</tspan>(<tspan fill="{AMBER}">'everything I build with'</tspan>)</text>
    """
    leg = []
    lx = 40
    for rx, ry, dur, col, lbl, items in rings:
        leg.append(f'<circle cx="{lx+5}" cy="{H-30}" r="5" fill="{col}"/><text x="{lx+16}" y="{H-26}" class="leg">{lbl}</text>')
        lx += 30 + len(lbl) * 8
    write("tech-orbit.svg", svg(W, H, f"<defs>{defs}</defs>{b}{''.join(g)}{head}{''.join(leg)}{e}", css, "Tech stack orbit"))


# ══════════════════════════ 4. SKILLS TRAINING ══════════════════════════
def training():
    W, H = 1200, 470
    d, b, e = frame(W, H, uid="s")
    css = f"""
    .h{{font:700 22px {MONO};fill:{TXT}}} .m{{font:500 14px {MONO};fill:{DIM}}}
    .ax{{font:500 12px {MONO};fill:{DIM}}} .sk{{font:600 15px {MONO};fill:{TXT}}}
    .pc{{font:700 14px {MONO}}} .big{{font:800 26px {MONO}}}
    """
    DUR = 10
    # loss chart (left)
    X0, Y0, CWd, CH = 70, 110, 470, 270
    pts = []
    for i in range(61):
        x = i / 60
        yv = 0.92 * math.exp(-4.2 * x) + 0.05 + 0.035 * math.sin(i * 1.7) * (1 - x) + 0.01 * random.random()
        pts.append((X0 + x * CWd, Y0 + CH - yv * CH))
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{X0+CWd},{Y0+CH} L{X0},{Y0+CH} Z"
    vpts = []
    for i in range(61):
        x = i / 60
        yv = 0.98 * math.exp(-3.4 * x) + 0.11 + 0.05 * math.sin(i * 2.3 + 1) * (1 - x)
        vpts.append((X0 + x * CWd, Y0 + CH - yv * CH))
    vline = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in vpts)
    L = 1400
    draw = lambda: (f'<animate attributeName="stroke-dashoffset" values="{L};{L};0;0" keyTimes="0;0.05;0.55;1" dur="{DUR}s" repeatCount="indefinite"/>')
    defs = d + f"""
    <linearGradient id="areaG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
    <clipPath id="areaClip"><rect x="{X0}" y="{Y0-10}" height="{CH+20}" width="0">
      <animate attributeName="width" values="0;0;{CWd};{CWd}" keyTimes="0;0.05;0.55;1" dur="{DUR}s" repeatCount="indefinite"/></rect></clipPath>
    """
    grid = "".join(f'<line x1="{X0}" y1="{Y0+CH*i/4:.0f}" x2="{X0+CWd}" y2="{Y0+CH*i/4:.0f}" stroke="{FAINT}" stroke-dasharray="3 5"/>' for i in range(5))
    yl = "".join(f'<text x="{X0-10}" y="{Y0+CH*i/4+4:.0f}" text-anchor="end" class="ax">{1-i/4:.2f}</text>' for i in range(5))
    xl = "".join(f'<text x="{X0+CWd*i/4:.0f}" y="{Y0+CH+22}" text-anchor="middle" class="ax">{int(2022+i)}</text>' for i in range(5))
    # head dot riding the curve
    chart = f"""
    {grid}{yl}{xl}
    <text x="{X0}" y="{Y0-18}" class="m"><tspan fill="{CYAN}">━ train_loss</tspan>   <tspan fill="{PINK}">┅ val_loss</tspan>   (lower = smarter)</text>
    <path d="{area}" fill="url(#areaG)" clip-path="url(#areaClip)"/>
    <path d="{vline}" fill="none" stroke="{PINK}" stroke-width="2" stroke-dasharray="5 6" opacity="0.8" clip-path="url(#areaClip)"/>
    <path d="{line}" fill="none" stroke="{CYAN}" stroke-width="3" stroke-linecap="round" stroke-dasharray="{L}" stroke-dashoffset="{L}" filter="url(#sglow)">{draw()}</path>
    <circle r="6" fill="#fff" stroke="{CYAN}" stroke-width="3">
      <animateMotion dur="{DUR}s" repeatCount="indefinite" path="{line}" keyPoints="0;0;1;1" keyTimes="0;0.05;0.55;1" calcMode="linear"/></circle>
    """
    # epoch readout frames
    frames = [("epoch 001/100", "loss 0.9120", "acc 41.2%"), ("epoch 025/100", "loss 0.3274", "acc 78.6%"),
              ("epoch 060/100", "loss 0.1031", "acc 93.4%"), ("epoch 100/100", "loss 0.0213", "acc 99.1%")]
    ro = []
    for i, f_ in enumerate(frames):
        t0 = 0.05 + i * 0.125
        t1 = t0 + 0.125 if i < 3 else 0.97
        ro.append(f"""<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{t0:.3f};{t0+0.001:.3f};{t1:.3f};{t1+0.001:.3f};1" calcMode="discrete" dur="{DUR}s" repeatCount="indefinite"/>
          <text x="{X0}" y="{Y0+CH+58}" class="m"><tspan fill="{TXT}">{f_[0]}</tspan>   {f_[1]}   <tspan fill="{LIME}">{f_[2]}</tspan></text></g>""")
    done = f"""<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.56;0.58;0.97;1" dur="{DUR}s" repeatCount="indefinite"/>
      <rect x="{X0+CWd-180}" y="{Y0+8}" width="180" height="34" rx="8" fill="{LIME}" fill-opacity="0.12" stroke="{LIME}" stroke-opacity="0.6"/>
      <text x="{X0+CWd-90}" y="{Y0+30}" text-anchor="middle" class="pc" fill="{LIME}" style="fill:{LIME}">✓ model converged</text></g>"""

    # skill bars (right)
    skills = [("Python", 95, CYAN), ("Machine Learning", 90, CYAN), ("Deep Learning / PyTorch", 85, VIOLET),
              ("NLP · LLMs · RAG", 85, VIOLET), ("Computer Vision", 78, VIOLET), ("MERN Stack", 82, PINK),
              ("SQL · MongoDB · VectorDB", 80, PINK), ("AWS · Docker · MLOps", 72, AMBER)]
    BX, BY, BW = 660, 112, 480
    bars = [f'<text x="{BX}" y="{Y0-18}" class="m">layer weights <tspan fill="{DIM}">// skills.load_state_dict()</tspan></text>']
    for i, (s, p, c) in enumerate(skills):
        y = BY + i * 38
        t0 = 0.06 + i * 0.04
        w = BW * p / 100
        segs = "".join(f'<rect x="{BX + j*12}" y="{y+12}" width="9" height="10" rx="2" fill="{FAINT}"/>' for j in range(int(BW / 12)))
        bars.append(f"""
        <text x="{BX}" y="{y+6}" class="sk">{esc(s)}</text>
        {segs}
        <clipPath id="bc{i}"><rect x="{BX}" y="{y+10}" height="14" width="0">
          <animate attributeName="width" values="0;0;{w:.0f};{w:.0f}" keyTimes="0;{t0:.2f};{t0+0.3:.2f};1" dur="{DUR}s" repeatCount="indefinite"/></rect></clipPath>
        <g clip-path="url(#bc{i})">{''.join(f'<rect x="{BX + j*12}" y="{y+12}" width="9" height="10" rx="2" fill="{c}"/>' for j in range(int(BW / 12)))}</g>
        <text x="{BX+BW}" y="{y+6}" text-anchor="end" class="pc" style="fill:{c}" opacity="0">{p}%
          <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;{t0+0.3:.2f};{t0+0.32:.2f};1" dur="{DUR}s" repeatCount="indefinite"/></text>""")
    head = f'<text x="40" y="52" class="h"><tspan fill="{CYAN}">model</tspan>.fit(<tspan fill="{AMBER}">mehtab</tspan>, epochs=<tspan fill="{VIOLET}">∞</tspan>)  <tspan fill="{DIM}" font-size="14"># still training, never overfitting</tspan></text>'
    defs += f'<filter id="sglow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    write("skills-training.svg", svg(W, H, f"<defs>{defs}</defs>{b}{head}{chart}{''.join(ro)}{done}{''.join(bars)}{e}", css, "Skills as a training run"))


# ══════════════════════════ 5. GIT-GRAPH EXPERIENCE ══════════════════════════
def gitgraph():
    W, H = 1200, 470
    d, b, e = frame(W, H, uid="g")
    css = f"""
    .h{{font:700 22px {MONO};fill:{TXT}}} .hash{{font:600 12px {MONO};fill:{AMBER}}}
    .c1{{font:700 15px {MONO};fill:{TXT}}} .c2{{font:500 13px {MONO};fill:{DIM}}}
    .tagt{{font:700 12px {MONO};fill:{BG0}}}
    """
    MY, BYb = 250, 350
    DUR = 12
    commits = [
        (100, "a1f0c3e", "init", ["B.Tech CSE", "Global Group of Inst."], CYAN, "up"),
        (300, "4be91d2", "feat", ["Python & ML Intern", "Solitaire Infosys"], CYAN, "up"),
        (500, "9c3aa07", "feat", ["AI/ML Intern", "Croma Campus"], CYAN, "up"),
        (800, "e7d5b18", "feat", ["AI/ML Intern", "Bharti Airtel · geo-ML"], CYAN, "up"),
        (1090, "HEAD", "release", ["v2026.0", "open to roles"], LIME, "up"),
    ]
    branch_c = (660, "0d2f9b4", "minor", ["Minor in AI", "IIT Ropar (2024-26)"], VIOLET)
    L = 1100
    main = f"M60,{MY} L1140,{MY}"
    bpath = f"M560,{MY} C600,{MY} 600,{BYb} 650,{BYb} L900,{BYb} C950,{BYb} 950,{MY} 990,{MY}"
    g = [f"""
    <path d="{main}" stroke="{FAINT}" stroke-width="4" fill="none"/>
    <path d="{main}" stroke="{CYAN}" stroke-width="4" fill="none" stroke-dasharray="{L}" stroke-dashoffset="{L}" stroke-linecap="round">
      <animate attributeName="stroke-dashoffset" values="{L};0;0" keyTimes="0;0.5;1" dur="{DUR}s" repeatCount="indefinite"/></path>
    <path d="{bpath}" stroke="{FAINT}" stroke-width="4" fill="none"/>
    <path d="{bpath}" stroke="{VIOLET}" stroke-width="4" fill="none" stroke-dasharray="600" stroke-dashoffset="600" stroke-linecap="round">
      <animate attributeName="stroke-dashoffset" values="600;600;0;0" keyTimes="0;0.24;0.46;1" dur="{DUR}s" repeatCount="indefinite"/></path>
    <circle r="7" fill="#fff" filter="url(#gglow)"><animateMotion dur="{DUR/2}s" repeatCount="indefinite" path="{main}"/></circle>
    <circle r="5" fill="{VIOLET}" filter="url(#gglow)"><animateMotion dur="{DUR/2}s" begin="1.5s" repeatCount="indefinite" path="{bpath}"/></circle>
    """]

    def node(x, y, h, kind, lines, col, t, up=True):
        ty = y - 70 if up else y + 48
        tag = ""
        if h == "HEAD":
            tag = f"""<rect x="{x-58}" y="{y+22}" width="116" height="24" rx="6" fill="{LIME}"/>
            <text x="{x}" y="{y+39}" text-anchor="middle" class="tagt">HEAD -&gt; main</text>"""
        return f"""
        <g opacity="0">{appear(DUR, t)}
          <circle cx="{x}" cy="{y}" r="20" fill="{col}" opacity="0.25"><animate attributeName="r" values="14;24;14" dur="2s" repeatCount="indefinite"/></circle>
          <circle cx="{x}" cy="{y}" r="11" fill="{BG0}" stroke="{col}" stroke-width="4"/>
          <line x1="{x}" y1="{y-(16 if up else -16)}" x2="{x}" y2="{ty+(36 if up else -18)}" stroke="{col}" stroke-opacity="0.35" stroke-dasharray="2 4"/>
          <text x="{x}" y="{ty-22 if up else ty}" text-anchor="middle" class="hash">{h} <tspan fill="{col}">{kind}:</tspan></text>
          <text x="{x}" y="{ty-2 if up else ty+20}" text-anchor="middle" class="c1">{esc(lines[0])}</text>
          <text x="{x}" y="{ty+16 if up else ty+38}" text-anchor="middle" class="c2">{esc(lines[1])}</text>
          {tag}
        </g>"""

    for x, h, kind, lines, col, _ in commits:
        t = (x - 60) / 1080 * DUR * 0.5
        g.append(node(x, MY, h, kind, lines, col, t))
    x, h, kind, lines, col = branch_c
    g.append(node(x, BYb, h, kind, lines, col, DUR * 0.34, up=False))
    g.append(f'<g opacity="0">{appear(DUR, DUR*0.47)}<circle cx="990" cy="{MY}" r="8" fill="{VIOLET}"/>'
             f'<text x="990" y="{MY+34}" text-anchor="middle" class="hash" fill="{VIOLET}" style="fill:{VIOLET}">merge</text></g>')
    head = f'<text x="40" y="52" class="h"><tspan fill="{DIM}">$</tspan> git log <tspan fill="{CYAN}">--graph</tspan> <tspan fill="{PINK}">--oneline</tspan> career</text>'
    d += f'<filter id="gglow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    write("experience-gitgraph.svg", svg(W, H, f"<defs>{d}</defs>{b}{head}{''.join(g)}{e}", css, "Career as a git graph"))


# ══════════════════════════ 6. PROJECT CARDS ══════════════════════════
PROJECTS = [
    ("jarvis", "Voice-Assistant---JARVIS", "JARVIS · Voice Assistant",
     ["Speech recognition + NLP assistant that", "automates search, reminders & system tasks."],
     ["Python", "SpeechRecognition", "NLP"], CYAN, "wave"),
    ("invoice", "invoice-ai-parser", "Invoice AI Parser",
     ["AI pipeline that reads invoices and pulls", "structured fields out of messy documents."],
     ["TypeScript", "LLMs", "OCR"], VIOLET, "scan"),
    ("diabetes", "diabetes-prediction-ml", "Diabetes Prediction",
     ["LogReg / Random Forest / SVM classifier on", "glucose, BMI, insulin & age features."],
     ["Python", "Scikit-learn", "Pandas"], PINK, "ecg"),
    ("trading", "mlops-trading-signal-pipeline-task", "MLOps Trading Signals",
     ["End-to-end ML pipeline that turns market", "data into reproducible trading signals."],
     ["Python", "MLOps", "Pipelines"], LIME, "candles"),
]


def project_card(slug, repo, title, desc, tags, col, icon):
    W, H = 580, 230
    uid = "p" + slug
    css = f"""
    .pt{{font:800 24px {SANS};fill:{TXT}}} .pd{{font:500 15px {SANS};fill:{DIM}}}
    .tg{{font:600 12px {MONO};fill:{TXT}}} .rp{{font:600 12px {MONO};fill:{DIM}}}
    """
    defs = f"""
    <linearGradient id="{uid}bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
    <linearGradient id="{uid}bd" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
      <stop offset="0" stop-color="{col}"/><stop offset="0.5" stop-color="{col}" stop-opacity="0.05"/><stop offset="1" stop-color="{col}"/>
      <animateTransform attributeName="gradientTransform" type="rotate" values="0 {W/2} {H/2};360 {W/2} {H/2}" dur="6s" repeatCount="indefinite"/></linearGradient>
    <radialGradient id="{uid}gl" cx="0.85" cy="0.2" r="0.6"><stop offset="0" stop-color="{col}" stop-opacity="0.22"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>
    <clipPath id="{uid}cl"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    """
    ix, iy = 470, 70
    if icon == "wave":
        bars = []
        for i in range(13):
            hmax = 10 + 34 * abs(math.sin(i * 0.7 + 0.4))
            bars.append(f'<rect x="{ix-60+i*10}" y="{iy}" width="5" rx="2.5" height="6" fill="{col}">'
                        f'<animate attributeName="height" values="6;{hmax:.0f};6" dur="{0.7+0.05*(i%4):.2f}s" begin="{i*0.07:.2f}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="y" values="{iy};{iy-hmax/2+3:.0f};{iy}" dur="{0.7+0.05*(i%4):.2f}s" begin="{i*0.07:.2f}s" repeatCount="indefinite"/></rect>')
        ic = "".join(bars)
    elif icon == "scan":
        ic = f"""<rect x="{ix-34}" y="{iy-44}" width="68" height="88" rx="6" fill="none" stroke="{col}" stroke-width="2"/>
        {''.join(f'<rect x="{ix-24}" y="{iy-30+i*14}" width="{[48,36,44,28,40][i]}" height="5" rx="2" fill="{col}" opacity="0.45"/>' for i in range(5))}
        <rect x="{ix-44}" y="{iy-44}" width="88" height="3" fill="{col}" filter="url(#{uid}g)">
          <animate attributeName="y" values="{iy-44};{iy+42};{iy-44}" dur="2.6s" repeatCount="indefinite"/></rect>"""
    elif icon == "ecg":
        p = f"M{ix-80},{iy} l30,0 l8,-8 l8,8 l10,0 l6,-38 l8,64 l7,-26 l10,0 l8,-10 l8,10 l40,0"
        ic = f"""<path d="{p}" fill="none" stroke="{col}" stroke-opacity="0.2" stroke-width="2.5"/>
        <path d="{p}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round" stroke-dasharray="80 300" filter="url(#{uid}g)">
          <animate attributeName="stroke-dashoffset" values="80;-300" dur="1.8s" repeatCount="indefinite"/></path>"""
    else:
        cs = []
        vals = [(0, 18, 30, 8, 1), (1, 6, 26, -4, 0), (2, 0, 30, 10, 1), (3, -14, 20, 4, 1), (4, -20, 28, -6, 0), (5, -30, 20, 8, 1)]
        for i, (k, off, h, d_, up) in enumerate(vals):
            x = ix - 60 + k * 22
            c = col if up else PINK
            cs.append(f'<g opacity="0.2"><animate attributeName="opacity" values="0.15;1;1;0.15" keyTimes="0;{0.1+i*0.12:.2f};0.9;1" dur="4s" repeatCount="indefinite"/>'
                      f'<line x1="{x+5}" y1="{iy+off-h/2-8}" x2="{x+5}" y2="{iy+off+h/2+8}" stroke="{c}" stroke-width="1.5"/>'
                      f'<rect x="{x}" y="{iy+off-h/2}" width="10" height="{h}" rx="1.5" fill="{c}"/></g>')
        ic = "".join(cs)
    tg, tx = [], 30
    for t in tags:
        w = len(t) * 7.6 + 20
        tg.append(f'<rect x="{tx}" y="172" width="{w:.0f}" height="28" rx="14" fill="{col}" fill-opacity="0.10" stroke="{col}" stroke-opacity="0.45"/>'
                  f'<text x="{tx+10}" y="190" class="tg">{esc(t)}</text>')
        tx += w + 8
    body = f"""
    <g clip-path="url(#{uid}cl)">
      <rect width="{W}" height="{H}" fill="url(#{uid}bg)"/><rect width="{W}" height="{H}" fill="url(#{uid}gl)"/>
      <text x="30" y="40" class="rp"><tspan fill="{col}">◆</tspan> {GH}/{esc(repo[:34])}</text>
      <text x="30" y="80" class="pt">{esc(title)}</text>
      <text x="30" y="114" class="pd">{esc(desc[0])}</text>
      <text x="30" y="136" class="pd">{esc(desc[1])}</text>
      {''.join(tg)}
      <g>{ic}</g>
      <text x="{W-30}" y="192" text-anchor="end" class="rp" fill="{col}" style="fill:{col}">view repo →
        <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/></text>
    </g>
    <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="url(#{uid}bd)" stroke-width="2"/>
    """
    defs += f'<filter id="{uid}g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    write(f"project-{slug}.svg", svg(W, H, f"<defs>{defs}</defs>{body}", css, title))


# ══════════════════════════ 7. SECTION DIVIDER + FOOTER ══════════════════════════
def divider(name, label, col):
    W, H = 1200, 70
    n = len(label)
    css = f".l{{font:700 18px {MONO};fill:{TXT};letter-spacing:3px}} .n{{font:600 14px {MONO}}}"
    lw = n * 18 * CW + n * 3 + 40
    x0 = 90
    body = f"""
    <defs><linearGradient id="dl" x1="0" x2="1"><stop offset="0" stop-color="{col}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>
    <text x="20" y="42" class="n" fill="{col}" style="fill:{col}">{name}</text>
    <text x="{x0}" y="42" class="l">{esc(label)}</text>
    <rect x="{x0+lw}" y="35" height="2" width="{W-x0-lw-20}" fill="url(#dl)"/>
    <circle cx="{x0+lw}" cy="36" r="4" fill="{col}">
      <animate attributeName="cx" values="{x0+lw};{W-40};{x0+lw}" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;0.2;1" dur="5s" repeatCount="indefinite"/></circle>
    """
    write(f"div-{name.strip('/ ').replace(' ', '')}.svg", svg(W, H, body, css, label))


def footer():
    W, H = 1200, 220
    css = f".f{{font:700 20px {MONO};fill:{TXT}}} .fs{{font:500 14px {MONO};fill:{DIM}}}"

    def wave(amp, y, col, op, dur, phase):
        pts = []
        for i in range(0, 2401, 40):
            pts.append(f"{i},{y + amp*math.sin(i/2400*4*math.pi + phase):.1f}")
        p = "M" + " L".join(pts) + f" L2400,{H} L0,{H} Z"
        return (f'<path d="{p}" fill="{col}" opacity="{op}"><animateTransform attributeName="transform" type="translate" '
                f'values="0 0;-1200 0" dur="{dur}s" repeatCount="indefinite"/></path>')
    body = f"""
    <defs><linearGradient id="fw" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient></defs>
    {wave(16, 150, "url(#fw)", 0.25, 9, 0)}
    {wave(12, 165, "url(#fw)", 0.35, 6, 1.4)}
    {wave(9, 180, "url(#fw)", 0.6, 4, 2.6)}
    <text x="600" y="60" text-anchor="middle" class="f"><tspan fill="{CYAN}">while</tspan>(<tspan fill="{VIOLET}">alive</tspan>) {{ learn(); build(); ship(); }}</text>
    <text x="600" y="92" text-anchor="middle" class="fs">// end of transmission — thanks for stopping by ✦</text>
    """
    write("footer.svg", svg(W, H, body, css, "Footer"))


if __name__ == "__main__":
    print("Generating cards ->", OUT)
    header()
    terminal()
    orbit()
    training()
    gitgraph()
    for p in PROJECTS:
        project_card(*p)
    divider("01", "WHOAMI", CYAN)
    divider("02", "TECH ORBIT", VIOLET)
    divider("03", "TRAINING LOG", PINK)
    divider("04", "COMMIT HISTORY", LIME)
    divider("05", "FEATURED BUILDS", AMBER)
    divider("06", "LIVE TELEMETRY", CYAN)
    divider("07", "CONNECT", PINK)
    footer()
    print("done.")
