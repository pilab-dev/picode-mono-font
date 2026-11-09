# PiCode Mono & Latin2

> A true fixed-pitch, monospaced developer programming font engineered for supreme legibility, terminal workflows, and code clarity. Normalized to an exact 1228 units advance width, with optical horizontal scaling for wide glyphs, continuous box-drawing alignment, and full **Latin-2 (Central & Eastern European / ISO-8859-2 / Windows-1250)** support.

Developed by **Progressive Innovation LAB (PiLAB)** — [https://pilab.hu](https://pilab.hu).

---

## Highlights

- **100% Fixed Pitch**: Every single glyph (ASCII, numerals, punctuation, accented Latin, Cyrillic, Greek, and box-drawing) is normalized to an exact `1228` units advance width (0.60 aspect ratio relative to 2048 UPM, matching standard programming monospace geometry).
- **Full Latin-2 (Central & Eastern European)**: Complete coverage for Hungarian (`ő`, `Ő`, `ű`, `Ű`, `á`, `é`, `í`, `ó`, `ö`, `ú`, `ü`), Polish (`ą`, `ć`, `ę`, `ł`, `ń`, `ó`, `ś`, `ź`, `ż`), Czech & Slovak (`č`, `ď`, `ě`, `ľ`, `ň`, `ř`, `š`, `ť`, `ž`, `ů`), Romanian (`ș`, `ț`, `ă`, `â`, `î`), and Croatian/Slovenian (`đ`, `ć`, `č`, `š`, `ž`).
- **Dual Weights**: Includes both **Regular (400)** and **Bold (700)** weights.
- **Continuous Underscores**: The underscore (`_`) is expanded to span `[-5, 1233]` so multiple underscores (`__init__`, `snake_case_variable`) connect seamlessly without visual gaps.
- **Zero-Gap Box Drawing**: Unicode box-drawing characters (`┌─┐└┘├┤┬┴┼`) align precisely on the 614-unit midline with horizontal edge overlaps, creating pixel-perfect CLI/TUI tables.
- **Terminal Emulator Compatibility**: Complies with `post.isFixedPitch = 1` and `OS/2.panose.bProportion = 9` (Monospaced), natively recognized by macOS Terminal, iTerm2, Alacritty, Kitty, Ghostty, and WezTerm.
- **Ultra-Lightweight Webfonts**: Compiled with Brotli compression (`.woff2`) weighing only ~**41 KB** per weight.

---

## Repository Structure

```text
picode-mono/
├── fonts/
│   ├── PiCodeMono-Regular.woff2          # 41.8 KB (Standard Webfont Regular)
│   ├── PiCodeMono-Regular.ttf            # 109.0 KB (Standard Desktop TTF Regular)
│   ├── PiCodeMono-Bold.woff2             # 43.0 KB (Standard Webfont Bold)
│   ├── PiCodeMono-Bold.ttf               # 109.7 KB (Standard Desktop TTF Bold)
│   │
│   ├── PiCodeMono-Latin2-Regular.woff2   # 41.8 KB (Latin-2 Dedicated Webfont Regular)
│   ├── PiCodeMono-Latin2-Regular.ttf     # 109.1 KB (Latin-2 Dedicated Desktop TTF Regular)
│   ├── PiCodeMono-Latin2-Bold.woff2      # 43.1 KB (Latin-2 Dedicated Webfont Bold)
│   └── PiCodeMono-Latin2-Bold.ttf        # 109.8 KB (Latin-2 Dedicated Desktop TTF Bold)
├── css/
│   └── picode-mono.css                   # Ready-to-use @font-face CSS bundle
├── docs/
│   └── FONT_ENGINEERING_GUIDE.md         # Comprehensive guide to the font pipeline & future builds
├── index.html                            # Interactive live test playground & Latin-2 showcase
├── build.py                              # Python fontTools compiler pipeline
└── README.md
```

---

## Web Integration

### 1. Link CSS
Add the stylesheet to your `<head>`:

```html
<link rel="stylesheet" href="css/picode-mono.css">
```

### 2. Apply in CSS

```css
/* Standard family */
code, pre, textarea {
  font-family: 'PiCode Mono', monospace;
}

/* Dedicated Latin-2 family */
.code-latin2 {
  font-family: 'PiCode Mono Latin2', 'PiCode Mono', monospace;
}
```

---

## Editor Configuration

### VS Code / Cursor
Add to your `settings.json`:
```json
{
  "editor.fontFamily": "'PiCode Mono Latin2', 'PiCode Mono', monospace",
  "editor.fontSize": 15,
  "editor.lineHeight": 1.6,
  "editor.fontLigatures": true
}
```

### macOS Terminal / iTerm2 / Ghostty
1. Double-click `fonts/PiCodeMono-Latin2-Regular.ttf` and `fonts/PiCodeMono-Latin2-Bold.ttf` to install in macOS **Font Book**.
2. Open Terminal Preferences → Profiles → Font → Select **PiCode Mono Latin2**.

---

## Build Pipeline & Documentation

The font compilation pipeline is fully automated and written in Python using `fontTools` and `brotli`.

To rebuild the fonts or create new font families, refer to the in-depth documentation:
- 📖 **[Font Engineering Guide](docs/FONT_ENGINEERING_GUIDE.md)**: Mathematical principles, glyph decomposition, optical transforms, box-drawing alignment, table sanitization, and step-by-step instructions for producing new monospace fonts.

### Quick Build

```bash
# Install dependencies
pip install fonttools brotli

# Run build pipeline
python3 build.py
```

---

## License

Developed by **Progressive Innovation LAB (PiLAB)**.  
Released under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL) / MIT compatible terms for developer tools and applications. Free to use for personal and commercial software development.
