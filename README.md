# PiCode Mono, Latin2 & Liga Editions

> A true fixed-pitch, monospaced developer programming font engineered for supreme legibility, terminal workflows, and code clarity. Normalized to an exact 1228 units advance width, with optical horizontal scaling for wide glyphs, continuous box-drawing alignment, full **Latin-2 (Central & Eastern European / ISO-8859-2 / Windows-1250)** support, and optional **Programming Ligatures (`calt`)**.

Developed by **Progressive Innovation LAB (PiLAB)** — [https://pilab.hu](https://pilab.hu).

---

## Highlights

- **100% Fixed Pitch**: Every single glyph (ASCII, numerals, punctuation, accented Latin, Cyrillic, Greek, and box-drawing) is normalized to an exact `1228` units advance width (0.60 aspect ratio relative to 2048 UPM, matching standard programming monospace geometry).
- **Programming Ligatures (`calt`)**: Includes the complete OpenType contextual alternates ligature set:
  - Arrows & Lambdas: `->`, `-->`, `->>`, `->|`, `<-`, `<--`, `<<-`, `|<-`, `=>`, `==>`, `=>>`, `<=`, `<==`, `<=>`
  - Comparisons: `===`, `!==`, `==`, `!=`, `/=`, `<=`, `>=`, `:=`, `=:=`, `<>`
  - HTML / XML: `<!--`, `-->`, `</`, `/>`, `</>`
  - Logicals & Ranges: `&&`, `||`, `||=`, `&&=`, `::`, `:::`, `..`, `...`, `..<`, `??`, `?:`, `??=`
- **Full Latin-2 (Central & Eastern European)**: Complete coverage for Hungarian (`ő`, `Ő`, `ű`, `Ű`, `á`, `é`, `í`, `ó`, `ö`, `ú`, `ü`), Polish (`ą`, `ć`, `ę`, `ł`, `ń`, `ó`, `ś`, `ź`, `ż`), Czech & Slovak (`č`, `ď`, `ě`, `ľ`, `ň`, `ř`, `š`, `ť`, `ž`, `ů`), Romanian (`ș`, `ț`, `ă`, `â`, `î`), and Croatian/Slovenian (`đ`, `ć`, `č`, `š`, `ž`).
- **Dual Weights**: Includes both **Regular (400)** and **Bold (700)** weights.
- **Continuous Underscores**: The underscore (`_`) is expanded to span `[-5, 1233]` so multiple underscores (`__init__`, `snake_case_variable`) connect seamlessly without visual gaps.
- **Zero-Gap Box Drawing**: Unicode box-drawing characters (`┌─┐└┘├┤┬┴┼`) align precisely on the 614-unit midline with horizontal edge overlaps, creating pixel-perfect CLI/TUI tables.
- **Terminal Emulator Compatibility**: Complies with `post.isFixedPitch = 1` and `OS/2.panose.bProportion = 9` (Monospaced), natively recognized by macOS Terminal, iTerm2, Alacritty, Kitty, Ghostty, and WezTerm.
- **Ultra-Lightweight Webfonts**: Compiled with Brotli compression (`.woff2`) weighing only ~**41–56 KB** per weight.

---

## Repository Structure

```text
picode-mono/
├── fonts/
│   ├── PiCodeMono-Regular.woff2               # 41.8 KB (Standard Webfont Regular)
│   ├── PiCodeMono-Regular.ttf                 # 109.0 KB (Standard Desktop TTF Regular)
│   ├── PiCodeMono-Bold.woff2                  # 43.0 KB (Standard Webfont Bold)
│   ├── PiCodeMono-Bold.ttf                    # 109.7 KB (Standard Desktop TTF Bold)
│   │
│   ├── PiCodeMono-Latin2-Regular.woff2        # 41.8 KB (Latin-2 Dedicated Webfont Regular)
│   ├── PiCodeMono-Latin2-Regular.ttf          # 109.1 KB (Latin-2 Dedicated Desktop TTF Regular)
│   ├── PiCodeMono-Latin2-Bold.woff2           # 43.1 KB (Latin-2 Dedicated Webfont Bold)
│   └── PiCodeMono-Latin2-Bold.ttf             # 109.8 KB (Latin-2 Dedicated Desktop TTF Bold)
│   │
│   ├── PiCodeMonoLiga-Regular.woff2           # 55.7 KB (Ligaturized Webfont Regular)
│   ├── PiCodeMonoLiga-Regular.ttf             # 152.2 KB (Ligaturized Desktop TTF Regular)
│   ├── PiCodeMonoLiga-Bold.woff2              # 56.6 KB (Ligaturized Webfont Bold)
│   ├── PiCodeMonoLiga-Bold.ttf                # 152.6 KB (Ligaturized Desktop TTF Bold)
│   │
│   ├── PiCodeMonoLiga-Latin2-Regular.woff2    # 55.7 KB (Ligaturized Latin-2 Webfont Regular)
│   ├── PiCodeMonoLiga-Latin2-Regular.ttf      # 152.4 KB (Ligaturized Latin-2 Desktop TTF Regular)
│   ├── PiCodeMonoLiga-Latin2-Bold.woff2       # 56.7 KB (Ligaturized Latin-2 Webfont Bold)
│   └── PiCodeMonoLiga-Latin2-Bold.ttf         # 152.7 KB (Ligaturized Latin-2 Desktop TTF Bold)
├── css/
│   └── picode-mono.css                        # Ready-to-use @font-face CSS bundle (all families)
├── docs/
│   └── FONT_ENGINEERING_GUIDE.md              # In-depth guide to the monospace pipeline & ligaturizer
├── index.html                                 # Interactive live playground, ligatures & pangram showcase
├── build.py                                   # Monospace outline compiler
├── ligaturize.py                              # Programming ligature injection tool
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

/* Ligaturized family */
.code-ligatures {
  font-family: 'PiCode Mono Liga', 'PiCode Mono', monospace;
  font-feature-settings: 'calt' 1, 'liga' 1;
}

/* Dedicated Latin-2 Ligaturized family */
.code-latin2-liga {
  font-family: 'PiCode Mono Liga Latin2', 'PiCode Mono Latin2', monospace;
  font-feature-settings: 'calt' 1, 'liga' 1;
}
```

---

## Editor Configuration

### VS Code / Cursor
Add to your `settings.json`:
```json
{
  "editor.fontFamily": "'PiCode Mono Liga Latin2', 'PiCode Mono Liga', 'PiCode Mono', monospace",
  "editor.fontSize": 15,
  "editor.lineHeight": 1.6,
  "editor.fontLigatures": true
}
```

### macOS Terminal / iTerm2 / Ghostty
1. Double-click the TTF file(s) in `fonts/` to install in macOS **Font Book**.
2. Open Terminal Preferences → Profiles → Font → Select **PiCode Mono Liga Latin2** (or **PiCode Mono Latin2**).

---

## Tooling & Pipelines

### 1. Monospace Compiler (`build.py`)

Normalizes any proportional TrueType font into a fixed-pitch programming font:

```bash
python3 build.py --help
```

### 2. Ligaturizer Pipeline (`ligaturize.py`)

Injects OpenType programming ligatures (`calt`) into any monospace font:

```bash
# Batch process all 4 PiCode Mono fonts
python3 ligaturize.py --all

# Or ligaturize a single custom font
python3 ligaturize.py --base path/to/font.ttf --output-ttf path/to/output.ttf
```

For complete architectural details, see 📖 **[Font Engineering Guide](docs/FONT_ENGINEERING_GUIDE.md)**.

---

## License

Developed by **Progressive Innovation LAB (PiLAB)**.  
Released under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL) / MIT compatible terms for developer tools and applications. Free to use for personal and commercial software development.
