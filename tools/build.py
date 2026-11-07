#!/usr/bin/env python3
"""Build the Neon Glass theme files and check them the way Orca does.

Run from the plugin root:  python3 -I tools/build.py

Writes themes/*.json and terminal/*.json from the palettes below, then replays
Orca's paint-time checks (opaque surfaces, contrast pairs, focus rings, border
alpha, Monaco editor colors). Orca silently drops a token that fails, so any
failure here is an error and the build exits non-zero.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PINK = "#ff2d95"  # the neon accent, shared by both modes

# --------------------------------------------------------------------------- palettes

DARK = {
    "base": "dark",
    "tokens": {
        # Surfaces: deep ink with a violet cast, stepped like stacked glass panes.
        "--background": "#0d0b16",
        "--editor-surface": "#100d1b",
        "--foreground": "#f3eefe",
        "--card": "#171327",
        "--card-foreground": "#f3eefe",
        "--popover": "#1a1530",
        "--popover-foreground": "#f3eefe",
        "--primary": PINK,
        "--primary-foreground": "#1a0010",
        "--secondary": "#221c38",
        "--secondary-foreground": "#f3eefe",
        "--muted": "#1d1830",
        "--muted-foreground": "#a9a0c8",
        "--accent": "#2a1a3e",
        "--accent-foreground": "#fff0f8",
        # Glass edges: thin, translucent light rather than solid lines.
        "--border": "rgb(214 196 255 / 0.11)",
        "--input": "rgb(214 196 255 / 0.17)",
        "--ring": "#ff4fa8",
        "--chart-1": PINK,
        "--chart-2": "#b06bff",
        "--chart-3": "#3de0ff",
        "--chart-4": "#5ee8a6",
        "--chart-5": "#ffd36b",
        "--sidebar": "#13101f",
        "--sidebar-foreground": "#ece6fb",
        "--sidebar-primary": PINK,
        "--sidebar-primary-foreground": "#1a0010",
        "--sidebar-accent": "#251a38",
        "--sidebar-accent-foreground": "#fff0f8",
        "--sidebar-border": "rgb(214 196 255 / 0.09)",
        "--sidebar-ring": "#ff4fa8",
        "--worktree-sidebar": "#13101f",
        "--worktree-sidebar-foreground": "#ece6fb",
        "--worktree-sidebar-accent": "#221a33",
        "--worktree-sidebar-accent-foreground": "#fff0f8",
        "--worktree-sidebar-border": "rgb(214 196 255 / 0.09)",
        "--worktree-sidebar-ring": "#ff4fa8",
        # Translucent neon washes: Orca composites these over the sidebar / chat.
        "--worktree-sidebar-active": "rgb(255 45 149 / 0.17)",
        "--worktree-sidebar-active-border": "rgb(255 79 168 / 0.55)",
        "--host-badge": "rgb(255 45 149 / 0.16)",
        "--host-badge-foreground": "#ffb8dc",
        "--tab-bar": "#0f0c1a",
        "--tab-active": "#1c1630",
        "--tab-active-foreground": "#ffffff",
        "--tab-active-indicator": PINK,
        "--tab-inactive": "#0f0c1a",
        "--tab-inactive-foreground": "#9088b0",
        "--split-divider": "rgb(214 196 255 / 0.08)",
        "--split-divider-hover": PINK,
        "--chat-user-message": "rgb(255 45 149 / 0.15)",
        "--text-link": "#ff6bb5",
        "--diff-added": "#3ddc97",
        "--diff-removed": "#ff5c7a",
        "--git-decoration-added": "#5ee8a6",
        "--git-decoration-modified": "#ffcf5c",
        "--git-decoration-deleted": "#ff5c7a",
        "--git-decoration-renamed": "#c08bff",
        "--git-decoration-untracked": "#4fe3ff",
        "--git-decoration-copied": "#8fb8ff",
        "--git-decoration-ignored": "#6e6690",
    },
    "syntax": {
        "comment": ("#716a96", "italic"),
        "keyword": ("#ff4fa8", None),
        "storage": ("#ff4fa8", None),
        "operator": ("#ff8fca", None),
        "language_var": ("#ff8fca", "italic"),
        "string": ("#8af5c8", None),
        "escape": ("#ffd36b", None),
        "number": ("#ffb37a", None),
        "constant": ("#ffb37a", None),
        "constant_lang": ("#c79bff", None),
        "function": ("#5ee6ff", None),
        "type": ("#c79bff", None),
        "variable": ("#f3eefe", None),
        "parameter": ("#ffc4e1", "italic"),
        "property": ("#9ecbff", None),
        "punctuation": ("#a49cc4", None),
        "tag": ("#ff4fa8", None),
        "attribute": ("#c79bff", "italic"),
        "decorator": ("#ffd36b", None),
        "heading": ("#ff4fa8", "bold"),
        "link": ("#5ee6ff", "underline"),
        "quote": ("#a49cc4", "italic"),
        "inline_code": ("#8af5c8", None),
        "inserted": ("#5ee8a6", None),
        "deleted": ("#ff5c7a", None),
        "invalid": ("#ff5c7a", None),
    },
    "terminal": {
        "background": "#0d0b16",
        "foreground": "#f3eefe",
        "cursor": PINK,
        "cursorAccent": "#0d0b16",
        "selectionBackground": "#4a1840",
        "selectionForeground": "#ffffff",
        "black": "#1b1628",
        "red": "#ff5c7a",
        "green": "#5ee8a6",
        "yellow": "#ffd36b",
        "blue": "#7aa2ff",
        "magenta": "#ff4fa8",
        "cyan": "#5ee6ff",
        "white": "#e6e0f5",
        "brightBlack": "#716a96",
        "brightRed": "#ff8fa3",
        "brightGreen": "#8af5c8",
        "brightYellow": "#ffe39a",
        "brightBlue": "#a8c2ff",
        "brightMagenta": "#ff8fca",
        "brightCyan": "#9ef0ff",
        "brightWhite": "#ffffff",
    },
    "background": {"path": "images/neon-glass-dark.webp", "opacity": 1, "size": "cover", "position": "center"},
}

LIGHT = {
    "base": "light",
    "tokens": {
        # Surfaces: frosted white with a lavender cast.
        "--background": "#f5f2fb",
        "--editor-surface": "#fbf9fe",
        "--foreground": "#1f1530",
        "--card": "#ffffff",
        "--card-foreground": "#1f1530",
        "--popover": "#ffffff",
        "--popover-foreground": "#1f1530",
        # A deeper neon pink so white button text stays readable.
        "--primary": "#db0077",
        "--primary-foreground": "#ffffff",
        "--secondary": "#eee8f7",
        "--secondary-foreground": "#1f1530",
        "--muted": "#efeaf7",
        "--muted-foreground": "#6b5f85",
        "--accent": "#fbe2f0",
        "--accent-foreground": "#2a1236",
        "--border": "rgb(76 36 128 / 0.13)",
        "--input": "rgb(76 36 128 / 0.20)",
        "--ring": PINK,
        "--chart-1": PINK,
        "--chart-2": "#8b4dff",
        "--chart-3": "#0096c7",
        "--chart-4": "#12a46d",
        "--chart-5": "#d48a00",
        "--sidebar": "#eee9f7",
        "--sidebar-foreground": "#231936",
        "--sidebar-primary": "#db0077",
        "--sidebar-primary-foreground": "#ffffff",
        "--sidebar-accent": "#f6dfee",
        "--sidebar-accent-foreground": "#2a1236",
        "--sidebar-border": "rgb(76 36 128 / 0.11)",
        "--sidebar-ring": PINK,
        "--worktree-sidebar": "#eee9f7",
        "--worktree-sidebar-foreground": "#231936",
        "--worktree-sidebar-accent": "#e9e0f4",
        "--worktree-sidebar-accent-foreground": "#2a1236",
        "--worktree-sidebar-border": "rgb(76 36 128 / 0.11)",
        "--worktree-sidebar-ring": PINK,
        "--worktree-sidebar-active": "rgb(255 45 149 / 0.14)",
        "--worktree-sidebar-active-border": "rgb(219 0 119 / 0.40)",
        "--host-badge": "rgb(255 45 149 / 0.12)",
        "--host-badge-foreground": "#a3005a",
        "--tab-bar": "#eee9f7",
        "--tab-active": "#fbf9fe",
        "--tab-active-foreground": "#1f1530",
        "--tab-active-indicator": PINK,
        "--tab-inactive": "#eee9f7",
        "--tab-inactive-foreground": "#665a80",
        "--split-divider": "rgb(76 36 128 / 0.10)",
        "--split-divider-hover": PINK,
        "--chat-user-message": "rgb(255 45 149 / 0.10)",
        "--text-link": "#c4006b",
        "--diff-added": "#0c9462",
        "--diff-removed": "#e0245e",
        "--git-decoration-added": "#0f8a5f",
        "--git-decoration-modified": "#a86a00",
        "--git-decoration-deleted": "#d0284f",
        "--git-decoration-renamed": "#7a3fd0",
        "--git-decoration-untracked": "#0079a8",
        "--git-decoration-copied": "#2f5fd0",
        "--git-decoration-ignored": "#847a9e",
    },
    "syntax": {
        "comment": ("#8a7fa6", "italic"),
        "keyword": ("#d6006f", None),
        "storage": ("#d6006f", None),
        "operator": ("#b0306f", None),
        "language_var": ("#b0306f", "italic"),
        "string": ("#078a5b", None),
        "escape": ("#b86e00", None),
        "number": ("#c2410c", None),
        "constant": ("#c2410c", None),
        "constant_lang": ("#7c3aed", None),
        "function": ("#0077b6", None),
        "type": ("#7c3aed", None),
        "variable": ("#1f1530", None),
        "parameter": ("#a3005a", "italic"),
        "property": ("#2f5fd0", None),
        "punctuation": ("#6b5f85", None),
        "tag": ("#d6006f", None),
        "attribute": ("#7c3aed", "italic"),
        "decorator": ("#b86e00", None),
        "heading": ("#d6006f", "bold"),
        "link": ("#0077b6", "underline"),
        "quote": ("#6b5f85", "italic"),
        "inline_code": ("#078a5b", None),
        "inserted": ("#0f8a5f", None),
        "deleted": ("#d0284f", None),
        "invalid": ("#e0245e", None),
    },
    "terminal": {
        "background": "#fbf9fe",
        "foreground": "#1f1530",
        "cursor": "#e6007e",
        "cursorAccent": "#ffffff",
        "selectionBackground": "#f8cde4",
        "selectionForeground": "#1f1530",
        "black": "#1f1530",
        "red": "#d0284f",
        "green": "#078a5b",
        "yellow": "#a86a00",
        "blue": "#2f5fd0",
        "magenta": "#d6006f",
        "cyan": "#0079a8",
        "white": "#6b5f85",
        "brightBlack": "#847a9e",
        "brightRed": "#e0245e",
        "brightGreen": "#12a46d",
        "brightYellow": "#c27c00",
        "brightBlue": "#4a74e0",
        "brightMagenta": PINK,
        "brightCyan": "#0096c7",
        "brightWhite": "#8a7fa6",
    },
    "background": {"path": "images/neon-glass-light.webp", "opacity": 1, "size": "cover", "position": "center"},
}

# TextMate scopes for each syntax role, in VS Code's tokenColors shape.
SCOPES = {
    "comment": ("Comments", ["comment", "punctuation.definition.comment"]),
    "keyword": ("Keywords", ["keyword", "keyword.control"]),
    "storage": ("Storage", ["storage.type", "storage.modifier"]),
    "operator": ("Operators", ["keyword.operator"]),
    "language_var": ("Language variables", ["variable.language"]),
    "string": ("Strings", ["string", "punctuation.definition.string"]),
    "escape": ("Escapes and regular expressions", ["constant.character.escape", "string.regexp"]),
    "number": ("Numbers", ["constant.numeric"]),
    "constant": ("Constants", ["constant", "support.constant", "variable.other.constant"]),
    "constant_lang": ("Language constants", ["constant.language"]),
    "function": ("Functions", ["entity.name.function", "support.function", "meta.function-call"]),
    "type": (
        "Types",
        [
            "entity.name.type",
            "entity.name.class",
            "entity.name.namespace",
            "entity.other.inherited-class",
            "support.type",
            "support.class",
        ],
    ),
    "variable": ("Variables", ["variable", "support.variable"]),
    "parameter": ("Parameters", ["variable.parameter"]),
    "property": ("Properties and keys", ["support.type.property-name", "variable.other.property", "meta.object-literal.key"]),
    "punctuation": ("Punctuation", ["punctuation", "meta.brace"]),
    "tag": ("Tags", ["entity.name.tag"]),
    "attribute": ("Attributes", ["entity.other.attribute-name"]),
    "decorator": ("Decorators", ["meta.decorator", "entity.name.function.decorator"]),
    "heading": ("Headings", ["markup.heading", "entity.name.section"]),
    "link": ("Links", ["markup.underline.link", "string.other.link"]),
    "quote": ("Quotes", ["markup.quote"]),
    "inline_code": ("Inline code", ["markup.inline.raw", "markup.raw"]),
    "inserted": ("Inserted", ["markup.inserted"]),
    "deleted": ("Deleted", ["markup.deleted"]),
    "invalid": ("Invalid", ["invalid"]),
}

THEMES = [
    # (id, title, palette, with background image)
    ("neon-glass-dark", "Neon Glass Dark", DARK, True),
    ("neon-glass-light", "Neon Glass Light", LIGHT, True),
    ("neon-glass-clear-dark", "Neon Glass Clear Dark", DARK, False),
    ("neon-glass-clear-light", "Neon Glass Clear Light", LIGHT, False),
]

TERMINALS = [
    ("neon-glass-dark", "Neon Glass Dark", DARK),
    ("neon-glass-light", "Neon Glass Light", LIGHT),
]

# --------------------------------------------------------------------------- color math (mirrors Orca)

RGBA = tuple[float, float, float, float]


def parse(value: str) -> RGBA:
    v = value.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{6})([0-9a-f]{2})?", v)
    if m:
        h = m.group(1)
        a = int(m.group(2), 16) / 255 if m.group(2) else 1.0
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    m = re.fullmatch(r"rgb\((\d+) (\d+) (\d+)(?: / ([0-9.]+))?\)", v)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4) or 1))
    raise ValueError(f"unsupported color in this build script: {value}")


def luminance(c: RGBA) -> float:
    def ch(x: float) -> float:
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a: RGBA, b: RGBA) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def over(top: RGBA, under: RGBA) -> RGBA:
    a = top[3]
    return (top[0] * a + under[0] * (1 - a), top[1] * a + under[1] * (1 - a), top[2] * a + under[2] * (1 - a), 1.0)


def mix(fg: RGBA, into: RGBA, percent: float) -> RGBA:
    r = percent / 100
    return tuple(fg[i] * r + into[i] * (1 - r) for i in range(4))  # type: ignore[return-value]


def tint(c: RGBA, percent: float) -> RGBA:
    return (c[0], c[1], c[2], c[3] * percent / 100)


class Resolver:
    """Resolves tokens the way Orca's renderer does for the contrast check."""

    def __init__(self, tokens: dict[str, str], base: str):
        self.t = {k: parse(v) for k, v in tokens.items()}
        self.base = base

    def __call__(self, name: str) -> RGBA:
        if name in self.t:
            return self.t[name]
        dark = self.base == "dark"
        fg = lambda: self("--foreground")  # noqa: E731
        rules = {
            "--chat-canvas": (lambda: mix(fg(), self("--background"), 5)) if dark else (lambda: self("--background")),
            "--chat-foreground-strong": lambda: mix(fg(), self("--chat-canvas"), 90 if dark else 92),
            "--chat-diff-added": lambda: mix(fg(), self("--diff-added"), 30),
            "--chat-diff-removed": lambda: mix(fg(), self("--diff-removed"), 30),
            "--diff-added-background": lambda: tint(self("--diff-added"), 16 if dark else 13),
            "--diff-added-emphasis": lambda: tint(self("--diff-added"), 20 if dark else 15),
            "--diff-removed-background": lambda: tint(self("--diff-removed"), 18 if dark else 11),
            "--diff-removed-emphasis": lambda: tint(self("--diff-removed"), 20 if dark else 15),
        }
        if name not in rules:
            raise KeyError(f"{name} is not set and has no fallback in this script")
        return rules[name]()


# --------------------------------------------------------------------------- checks

def check_theme(title: str, palette: dict) -> list[str]:
    tokens = palette["tokens"]
    get = Resolver(tokens, palette["base"])
    errors: list[str] = []

    def pair(surface: str, text: str, minimum: float = 4.5, on: str | None = None) -> None:
        s, t = get(surface), get(text)
        if on is not None:
            s = over(s, get(on))
        if s[3] < 1:
            errors.append(f"{surface} must be opaque (alpha {s[3]:.2f}); Orca drops translucent surfaces")
            return
        if t[3] < 1:
            errors.append(f"{text} must be opaque")
            return
        ratio = contrast(s, t)
        if ratio < minimum:
            errors.append(f"{text} on {surface}: {ratio:.2f} < {minimum}")

    for s, t in [
        ("--background", "--foreground"),
        ("--background", "--muted-foreground"),
        ("--editor-surface", "--foreground"),
        ("--editor-surface", "--muted-foreground"),
        ("--card", "--card-foreground"),
        ("--popover", "--popover-foreground"),
        ("--primary", "--primary-foreground"),
        ("--secondary", "--secondary-foreground"),
        ("--muted", "--muted-foreground"),
        ("--accent", "--accent-foreground"),
        ("--sidebar", "--sidebar-foreground"),
        ("--sidebar-primary", "--sidebar-primary-foreground"),
        ("--sidebar-accent", "--sidebar-accent-foreground"),
        ("--worktree-sidebar", "--worktree-sidebar-foreground"),
        ("--worktree-sidebar-accent", "--worktree-sidebar-accent-foreground"),
        ("--tab-active", "--tab-active-foreground"),
        ("--tab-inactive", "--tab-inactive-foreground"),
        ("--tab-inactive", "--tab-active-foreground"),
        ("--editor-surface", "--text-link"),
    ]:
        pair(s, t)
    pair("--worktree-sidebar-active", "--worktree-sidebar-foreground", on="--worktree-sidebar")
    pair("--host-badge", "--host-badge-foreground", on="--worktree-sidebar")
    pair("--chat-user-message", "--chat-foreground-strong", on="--chat-canvas")
    for kind in ("added", "removed"):
        pair(f"--diff-{kind}-background", "--foreground", on="--editor-surface")
        pair(f"--diff-{kind}-emphasis", "--foreground", on="--editor-surface")
        pair(f"--diff-{kind}-background", f"--chat-diff-{kind}", on="--chat-canvas")
    for kind in ("added", "modified", "deleted", "renamed", "untracked", "copied", "ignored"):
        pair("--sidebar", f"--git-decoration-{kind}", minimum=3)

    for ring, surface in [
        ("--ring", "--background"),
        ("--sidebar-ring", "--sidebar"),
        ("--worktree-sidebar-ring", "--worktree-sidebar"),
        ("--tab-active-indicator", "--tab-active"),
    ]:
        ratio = contrast(over(get(ring), get(surface)), get(surface))
        if ratio < 2:
            errors.append(f"{ring} on {surface}: {ratio:.2f} < 2")

    for border in (
        "--border",
        "--input",
        "--sidebar-border",
        "--worktree-sidebar-border",
        "--worktree-sidebar-active-border",
        "--split-divider",
        "--split-divider-hover",
    ):
        if get(border)[3] < 0.05:
            errors.append(f"{border} alpha below 0.05 is dropped")

    # Monaco: Orca only builds an editor theme when these hold.
    editor = get("--editor-surface")
    vs_defaults = {
        "dark": ["#608b4e", "#ce9178", "#569cd6", "#3dc9b0", "#b5cea8"],
        "light": ["#008000", "#a31515", "#0000ff", "#008080", "#098658"],
    }[palette["base"]]
    if contrast(get("--foreground"), editor) < 4.5:
        errors.append("--foreground on --editor-surface below 4.5 disables the editor theme")
    for c in vs_defaults:
        if contrast(parse(c), editor) < 3:
            errors.append(f"VS default {c} below 3:1 on --editor-surface disables the editor theme")
    for role, (color, _) in palette["syntax"].items():
        ratio = contrast(parse(color), editor)
        if ratio < 3:
            errors.append(f"syntax {role} {color}: {ratio:.2f} < 3 (Monaco drops it)")

    return [f"{title}: {e}" for e in errors]


def check_terminal(title: str, palette: dict) -> list[str]:
    term = palette["terminal"]
    errors = []
    for key, value in term.items():
        if not re.fullmatch(r"#[0-9a-f]{6}", value):
            errors.append(f"{key} must be a 6-digit hex color")
    bg = parse(term["background"])
    if contrast(parse(term["foreground"]), bg) < 7:
        errors.append("foreground below 7:1")
    for key in ("red", "green", "yellow", "blue", "magenta", "cyan", "brightRed", "brightGreen", "brightBlue", "brightMagenta", "brightCyan"):
        ratio = contrast(parse(term[key]), bg)
        if ratio < 3:
            errors.append(f"{key} {term[key]}: {ratio:.2f} < 3")
    sel = parse(term["selectionBackground"])
    if contrast(parse(term["selectionForeground"]), sel) < 4.5:
        errors.append("selectionForeground on selectionBackground below 4.5")
    return [f"{title} terminal: {e}" for e in errors]


# --------------------------------------------------------------------------- emit

def token_colors(palette: dict) -> list[dict]:
    rules = []
    for role, (name, scopes) in SCOPES.items():
        color, style = palette["syntax"][role]
        settings = {"foreground": color}
        if style:
            settings["fontStyle"] = style
        rules.append({"name": name, "scope": scopes, "settings": settings})
    for name, scope, style in [("Bold", "markup.bold", "bold"), ("Italic", "markup.italic", "italic")]:
        rules.append({"name": name, "scope": [scope], "settings": {"fontStyle": style}})
    return rules


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if len(text.encode()) > 16 * 1024:
        raise SystemExit(f"{path.name} is over Orca's 16 KiB theme limit")
    path.write_text(text)


def main() -> int:
    errors: list[str] = []
    for _, title, palette in TERMINALS:
        errors += check_theme(title, palette)
        errors += check_terminal(title, palette)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    for theme_id, _, palette, with_image in THEMES:
        data = {"schemaVersion": 1, "base": palette["base"], "tokens": palette["tokens"], "tokenColors": token_colors(palette)}
        if with_image:
            data["background"] = palette["background"]
        write_json(ROOT / "themes" / f"{theme_id}.json", data)
    for theme_id, _, palette in TERMINALS:
        write_json(
            ROOT / "terminal" / f"{theme_id}.json",
            {"schemaVersion": 1, "mode": palette["base"], "terminal": palette["terminal"]},
        )
    print(f"ok: {len(THEMES)} app themes, {len(TERMINALS)} terminal themes, all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
