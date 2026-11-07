# Neon Glass

Frosted glass themes for [Orca](https://github.com/stablyai/orca), dark and light, lit by a neon pink accent.

| Theme | What it is |
| --- | --- |
| **Neon Glass Dark** | Deep violet ink. Translucent terminals and chats show a soft neon pink and violet glow behind them. |
| **Neon Glass Light** | Frosted lavender white. Translucent terminals and chats show a pastel pink and lilac glow. |
| **Neon Glass Clear Dark** | The same colors with no image, so macOS can blur your desktop behind translucent terminals. |
| **Neon Glass Clear Light** | The light colors with no image, for the same desktop blur. |

Both modes come with a matching terminal palette: **Neon Glass Dark** and **Neon Glass Light**.

## Install

In Orca, open **Settings → Plugins**, search for **Neon Glass** and install it. Or browse it at
[onorca.dev/plugins/unz47/neon-glass-theme](https://www.onorca.dev/plugins/unz47/neon-glass-theme).

## Getting the glass look

The glow only shows through surfaces that are see-through, so turn on translucency:

1. **Settings → Appearance:** pick a Neon Glass theme for dark and for light.
2. **Settings → Terminal:** set the terminal theme to Neon Glass Dark / Light.
3. **Settings → Terminal → Background Opacity:** `0.75` to `0.85` works well. Lower is glassier; higher is easier to read.
4. For the **Clear** themes on macOS, also set **Window Material** to **Blurred** and restart Orca. Your desktop then shows through, frosted.

Turning on Reduce Visual Effects, or the system Reduce Transparency setting, turns the glass off.

## Design notes

Orca checks every theme before painting it and drops colors that would be hard to read, including
any translucent panel fill. So the panels are solid, layered like stacked panes, and the glass comes
from:

- thin, translucent light edges instead of solid borders,
- translucent neon pink washes on the current workspace, the host badge and your chat messages,
- a pre-blurred glow image under translucent terminals and chats (Orca never blurs it, so it is drawn soft).

Every text color meets WCAG AA (4.5:1) on its surface, git colors meet 3:1, and every syntax color
meets 3:1 on the editor, so Orca keeps all of them.

## Develop

The theme files are generated. Edit the palettes in `tools/build.py`, then:

```sh
python3 -I tools/build.py      # writes themes/ and terminal/, fails if Orca would drop a color
uv run --no-project --with numpy --with pillow python -I tools/backgrounds.py   # renders images/
orca plugin validate .
orca plugin dev watch .        # loads this folder into Orca; Ctrl-C unloads it
```

## License

MIT
