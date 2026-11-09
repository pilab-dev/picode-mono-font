# Monospace Font Engineering & Compilation Guide
**Progressive Innovation LAB (PiLAB)**  
*Architecture, Mathematical Principles, and Pipeline Specification for Developer Programming Fonts*

---

## 1. Executive Summary & Purpose

Modern developer environments—terminals, text editors (VS Code, Cursor, Neovim), IDEs, and browser-based coding canvases—rely fundamentally on **monospaced (fixed-pitch) typography**. In a monospace typeface, every character, whether a narrow punctuation dot (`.`), an accent, a digit, or a broad glyph (`M`, `W`, `@`), occupies an **identical horizontal advance width**.

Proportional (variable-width) typefaces cannot be used directly in terminal emulators or coding editors:
1. Columns do not align vertically, breaking tabular formatting, indentation levels, and ASCII/Unicode diagrams.
2. Terminal emulators (macOS Terminal, iTerm2, Alacritty, Kitty, Ghostty) reject fonts lacking explicit monospace OpenType/TrueType flags (`post.isFixedPitch`, `OS/2.panose.bProportion`).
3. Accent marks, composite glyphs, and box-drawing elements break when forced into arbitrary grids.

This guide documents the **PiLAB Monospace Font Engineering Pipeline** implemented in [`build.py`](../build.py). It provides the mathematical foundations, outline decomposition rules, optical scaling algorithms, and table sanitization protocols needed to transform any proportional typeface into a high-performance, production-ready programming font.

---

## 2. Mathematical Foundations of Monospacing

### 2.1 The Golden Monospace Aspect Ratio

TrueType fonts define outlines within a coordinate grid determined by `unitsPerEm` (typically **2048** for TrueType or **1000** for PostScript OpenType).

Industry-standard developer fonts (such as JetBrains Mono, Consolas, Fira Code, and Cascadia Code) converge on a width-to-em aspect ratio between **0.55 and 0.62**:

$$\text{Aspect Ratio} = \frac{\text{Advance Width}}{\text{unitsPerEm}} \approx 0.60$$

For a font with $\text{unitsPerEm} = 2048$:

$$\text{Target Advance Width} = \text{round}(2048 \times 0.60) = 1228 \text{ font units}$$

```
+-------------------------------------------------------------+  y = 1638 (Ascender)
|                                                             |
|                          Glyph Cell                         |  y = 1024 (Cap Height)
|                     (Width = 1228 units)                    |  y = 512  (x-Height)
|                                                             |
+-------------------------------------------------------------+  y = 0    (Baseline)
|                                                             |  y = -410 (Descender)
+-------------------------------------------------------------+
x = 0                      Midline = 614                  x = 1228
```

At `1228` units:
- Characters have sufficient horizontal breathing room for distinct legibility.
- Line lengths remain compact for split-pane code editing.
- Column alignment is exact across all glyphs.

---

## 3. Outline Processing & Contour Decomposition

### 3.1 The Composite Glyph Problem

In TrueType fonts, accented characters (e.g., `á`, `é`, `ő`, `ű`, `ñ`, `č`) are stored as **composite glyphs**:
- Instead of raw Bézier curves, a composite glyph contains references to a base glyph (e.g., `o`) and a diacritic glyph (e.g., `hungarumlaut` / double acute `˝`) plus $(dx, dy)$ translation offsets.

If a script adjusts the advance width or bounding box of the base glyph without flattening the composite structure:
1. The relative offsets break.
2. Accents shift out of place, detach, or collide with adjacent lines.
3. Optical scaling distorts the accent position.

### 3.2 Automated Contour Flattening

The PiLAB pipeline solves this using `fontTools.pens.recordingPen.DecomposingRecordingPen`:

```python
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

# 1. Unpack composite glyph into independent quadratic Bézier curves
rec = DecomposingRecordingPen(glyph_set)
glyph_set[glyph_name].draw(rec)

# 2. Record outlines into a clean TrueType pen
pen = TTGlyphPen(None)
```

By decomposing 100% of composite glyphs into discrete quadratic Bézier curves, **every single character in the font becomes an independent, self-contained vector outline** that can be scaled, shifted, or modified without unintended side effects.

---

## 4. Optical Glyph Normalization & Geometric Transforms

Not all characters naturally fit into a fixed `1228`-unit cell. The pipeline classifies glyphs into three optical tiers based on their natural width $gw = xMax - xMin$:

```
Tier 1: Wide Glyphs       (M, W, m, w, @, %, etc.)   -> gw > max_w  (Scale & Pad)
Tier 2: Slender Glyphs    (i, l, 1, !, |, :, ;, etc.) -> gw <= max_w (Center)
Tier 3: Non-printing      (space, nbspace)            -> Empty     (Advance Only)
```

### 4.1 Bounding Box Calculation

The bounding box is calculated using `BoundsPen`:

```python
from fontTools.pens.boundsPen import BoundsPen

bp = BoundsPen(glyph_set)
rec.replay(bp)

xMin, yMin, xMax, yMax = bp.bounds
gw = xMax - xMin  # Glyph visual width
```

### 4.2 Bounding and Scaling Wide Glyphs

Wide glyphs (`M`, `W`, `m`, `w`, `@`, `%`) can exceed the cell width (e.g., 1400–1600 units). If placed unscaled, their outlines would collide with adjacent characters.

The pipeline defines a protective margin $M$ ($75$ units for Bold, $80$ units for Regular):

$$\text{max\_w} = \text{TARGET\_WIDTH} - 2 \times M = 1228 - 160 = 1068 \text{ units}$$

If $gw > \text{max\_w}$:

$$s_x = \frac{\text{max\_w}}{gw} \quad (< 1.0)$$

$$sw = gw \times s_x$$

$$\text{target\_lsb} = \text{round}\left(\frac{\text{TARGET\_WIDTH} - sw}{2}\right)$$

$$dx = \text{target\_lsb} - \text{round}(xMin \times s_x)$$

$$\mathbf{T} = \begin{bmatrix} s_x & 0 & dx \\ 0 & 1.0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$$

This applies an **optical horizontal compression** while leaving vertical stroke weights and ascender/descender heights completely untouched.

### 4.3 Centering Slender Glyphs

For slender characters ($gw \le \text{max\_w}$):

$$s_x = 1.0$$

$$\text{target\_lsb} = \text{round}\left(\frac{\text{TARGET\_WIDTH} - gw}{2}\right)$$

$$dx = \text{target\_lsb} - xMin$$

$$\mathbf{T} = \begin{bmatrix} 1.0 & 0 & dx \\ 0 & 1.0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$$

This places brackets `[]`, braces `{}`, parentheses `()`, quotes, and slender letters (`i`, `l`, `1`) precisely in the optical center of the cell.

---

## 5. Programming-Specific Glyph Enhancements

### 5.1 Continuous Underscores (`_`)

In proportional fonts, the underscore glyph has left and right side bearings ($lsb > 0$, $rsb > 0$). In code, consecutive underscores (`__init__`, `__proto__`, `snake_case_variable`) appear disjointed:

$$\text{Proportional Underscore:} \quad \_\quad \_\quad \_ \quad \text{(Broken)}$$
$$\text{PiLAB Underscore:} \quad \_\_\_\_\_ \quad \text{(Continuous)}$$

**Engineering Solution**:
1. Measure the existing underscore width.
2. Scale and stretch the horizontal dimension so the visual outline spans from $-5$ units to $\text{TARGET\_WIDTH} + 5$ ($1233$ units):

```python
if name == 'underscore':
    target_w = TARGET_WIDTH + 10  # 1238 units
    sx = target_w / gw
    dx = -5 - round(xMin * sx)
    t = Transform(sx, 0, 0, 1.0, dx, 0)
    # Result: outline starts at x = -5, ends at x = 1233
    # Left Side Bearing set to -5, Advance Width set to 1228
```

Consecutive underscore cells overlap by $10$ units at their boundaries, producing an unbroken, solid underline rule.

### 5.2 Zero-Gap Unicode Box-Drawing Alignment

CLI tools, Docker/Kubernetes dashboards, and TUI applications use Unicode box-drawing characters (U+2500–U+257F) and block elements (U+2580–U+259F).

```
┌───────┬───────┐
│ Code  │ Status│
├───────┼───────┤
│ 200   │ OK    │
└───────┴───────┘
```

If horizontal lines (`─`, `━`, `═`) have gaps, or vertical lines (`│`, `┃`, `║`) are off-center, tables render disjointed.

**Alignment Rules**:
- **Horizontal elements (`uni2500`, `uni2501`, `uni2550`)**: Scaled with a $5$-unit boundary overlap ($[-5, 1233]$), identical to underscores.
- **Vertical elements (`uni2502`, `uni2503`, `uni2551`)**: Centered mathematically on the $614$-unit midline ($\frac{1228}{2}$):

$$dx = \text{round}\left(614 - \frac{xMin + xMax}{2}\right)$$

---

## 6. OpenType & TrueType Table Specifications for Monospace Compliance

Operating systems, terminal emulators, and code editors interrogate specific binary tables to determine if a font is a valid monospace:

| Table | Field | Value | Purpose |
| :--- | :--- | :--- | :--- |
| `post` | `isFixedPitch` | `1` (Non-zero) | Tells macOS CoreText, FreeType, and DirectWrite that the font is fixed-pitch. |
| `OS/2` | `panose.bProportion` | `9` (Monospaced) | Required by macOS Terminal, iTerm2, and Windows Console to include the font in the Monospace picker. |
| `OS/2` | `xAvgCharWidth` | `1228` | Must equal the uniform advance width. |
| `OS/2` | `usWeightClass` | `400` / `700` | Standard weight identifier (Regular vs Bold). |
| `OS/2` | `fsSelection` | Bit 5 (Bold) or Bit 6 (Regular) | Selection flags for styling engines. |
| `hhea` | `advanceWidthMax` | `1228` | Maximum horizontal advance width in the font. |
| `hhea` | `numberOfHMetrics` | Count of glyphs | Ensures all glyphs have explicit metrics records in `hmtx`. |
| `hmtx` | `metrics[glyph]` | `(1228, lsb)` | 100% of glyph records must have an advance width of exactly 1228. |

---

## 7. Central & Eastern European (Latin-2) Internationalization

Standard Latin fonts frequently omit or misrender Central and Eastern European diacritics. In programming, identifiers, comments, localized log messages, and UI tests require full Latin-2 coverage:

- **Hungarian Double Acutes**: `ő`, `Ő`, `ű`, `Ű` (U+0150, U+0151, U+0170, U+0171)
- **Polish Ogoneks & Diacritics**: `ą`, `ę`, `ć`, `ł`, `ń`, `ś`, `ź`, `ż`
- **Czech & Slovak Háčeks**: `č`, `ď`, `ě`, `ň`, `ř`, `š`, `ť`, `ž`, `ů`, `ĺ`, `ľ`
- **Romanian Comma-Below**: `ș`, `ț`, `ă`, `â`, `î`

### 7.1 OS/2 Code Page Flags

To ensure Windows and Linux fonts register the dedicated Latin-2 character set:

```python
# Bit 1 = Latin-2 (Central Europe / ISO-8859-2 / CP-1250)
font['OS/2'].ulCodePageRange1 |= (1 << 1)
```

The font is emitted under two family names:
1. `PiCode Mono` (Standard Developer Family)
2. `PiCode Mono Latin2` (Dedicated Central & Eastern European Family)

---

## 8. Table Sanitization & Obsolete Bytecode Stripping

When converting a font, legacy tables that assume proportional metrics or store obsolete device hints must be stripped:

```python
tables_to_strip = [
    'hdmx',  # Horizontal Device Metrics (device-dependent advance widths)
    'LTSH',  # Linear Threshold table
    'VDMX',  # Vertical Device Metrics
    'fpgm',  # Font Program bytecode (tuned for proportional outlines)
    'prep',  # Control Value Program
    'cvt ',  # Control Value Table
    'DSIG',  # Digital Signature table (contains obsolete corporate certificates)
]

for tag in tables_to_strip:
    if tag in font:
        del font[tag]
```

### Benefits of Stripping:
1. **Prevents Hinting Distortion**: Legacy TTF hinting instructions were calculated for original proportional coordinates. Leaving them in causes low-DPI distortion on adjusted outlines.
2. **File Size Reduction**: Stripping legacy bytecode reduces TTF file size by ~10–15 KB.
3. **Clean Licensing & Metadata**: Drops old digital signature certificates and references.

---

## 9. Modern Webfont Packaging (WOFF2 & Brotli)

For web deployment, desktop TrueType (`.ttf`) fonts are converted to WOFF2 using Google's Brotli compressor:

```python
font.flavor = 'woff2'
font.save(output_woff2_path)
```

### Compression Results

| Format | Uncompressed TrueType | WOFF2 (Brotli) | Savings |
| :--- | :--- | :--- | :--- |
| **PiCode Mono Regular** | 109,044 bytes | **41,868 bytes** | **-61.6%** |
| **PiCode Mono Bold** | 109,748 bytes | **43,068 bytes** | **-60.8%** |
| **PiCode Mono Latin2 Regular** | 109,188 bytes | **41,920 bytes** | **-61.6%** |
| **PiCode Mono Latin2 Bold** | 109,892 bytes | **43,056 bytes** | **-60.8%** |

At ~42 KB, the font loads instantly on mobile and low-latency network connections with zero FOIT (*Flash of Invisible Text*) when paired with `font-display: swap`.

---

## 10. Playbook: Engineering New Monospace Fonts

To create another programming monospace font using the PiLAB pipeline:

### Step 1: Prepare Source Files
Place the source font files in a directory (e.g., `source/myfont-regular.ttf` and `source/myfont-bold.ttf`). Ensure the outlines use quadratic Bézier curves (TrueType `.ttf`).

### Step 2: Configure CLI Arguments

```bash
python3 build.py \
  --input-regular path/to/source-regular.ttf \
  --input-bold path/to/source-bold.ttf \
  --family "MyCode Mono" \
  --target-width 1228 \
  --output-dir fonts/
```

### Step 3: Verify Output Metrics

Run a validation script with `fontTools`:

```bash
python3 -c "
from fontTools.ttLib import TTFont
font = TTFont('fonts/MyCodeMono-Regular.ttf')
widths = set(font['hmtx'].metrics[g][0] for g in font.getGlyphOrder())
assert widths == {1228}, f'Non-uniform advance widths found: {widths}'
assert font['post'].isFixedPitch == 1, 'post.isFixedPitch not set'
assert font['OS/2'].panose.bProportion == 9, 'PANOSE monospace flag not set'
print('✓ Font validation passed 100%!')
"
```

### Step 4: Test in Target Environments
1. **VS Code / Cursor**: Add `'MyCode Mono', monospace` to `editor.fontFamily`.
2. **Terminal**: Install TTF in system Font Book, select in Terminal profiles.
3. **Web**: Load via `@font-face` and inspect in Chrome DevTools via `document.fonts.check()`.

---

## 11. Programming Ligature Architecture (`ligaturize.py`)

A premier requirement for contemporary developer typefaces is support for **programming ligatures**—visual replacements that render multi-character syntax tokens (such as `->`, `=>`, `===`, `!==`, `<=`, `>=`, `<!--`, `-->`, `::`, `:=`) as single, beautifully connected symbolic glyphs.

The PiLAB Ligaturizer ([`ligaturize.py`](../ligaturize.py)) implements an OpenType `calt` (*Contextual Alternates*) injection pipeline.

### 11.1 The Multi-Cell Contextual Alternates Mechanism

In fixed-pitch fonts, characters cannot simply be replaced by a single wide glyph because the text layout engine would lose track of character positions and cursor movements. If a cursor is placed inside `===`, the terminal or editor must still navigate three discrete character cells.

To preserve strict fixed-pitch cursor alignment, the pipeline uses a **multi-cell replacement protocol**:

1. **Intermediate Cells (`CR.*`)**:
   - The initial characters in the sequence are substituted with specialized non-spacing or space-holding glyphs that share the exact cell advance width ($1228$ units).
2. **Terminal Cell (`lig.*`)**:
   - The final character in the sequence is substituted with a wide composite glyph that carries the complete visual representation of the connected ligature.
   - It utilizes negative left side bearings ($lsb < 0$) to draw backwards across all preceding cells in the sequence without changing the layout engine's advance cursor position.

```
Input Tokens:      [ = ]          [ = ]          [ = ]
Cell Metrics:    (adv: 1228)    (adv: 1228)    (adv: 1228)
Substitution:     [CR.1.0]       [CR.1.0]       [lig.1]
Visual Draw:        |              |         <--- Draws across all 3 cells
```

### 11.2 Horizontal Scaling of Ligature Outlines

Ligature donors (e.g. Fira Code) may use an advance width different from the target font ($W_{\text{donor}} = 1116$ vs $W_{\text{target}} = 1228$).

The pipeline calculates the exact horizontal scale factor:

$$s_x = \frac{W_{\text{target}}}{W_{\text{donor}}} = \frac{1228}{1116} \approx 1.10036$$

Every ligature glyph's quadratic Bézier outline is scaled horizontally and its left side bearing is adjusted:

$$\text{lsb}_{\text{target}} = \text{round}(\text{lsb}_{\text{donor}} \times s_x)$$

$$\text{adv}_{\text{target}} = W_{\text{target}} = 1228$$

This guarantees that two-character ligatures span exactly $2 \times 1228 = 2456$ units, three-character ligatures span $3684$ units, and four-character ligatures span $4912$ units with zero visual seams or gaps.

### 11.3 CLI Usage of the Ligaturizer

```bash
# Ligaturize all 4 PiCode Mono fonts (Regular, Bold, Latin-2 Regular, Latin-2 Bold):
python3 ligaturize.py --all

# Or ligaturize an individual monospace font:
python3 ligaturize.py \
  --base fonts/MyFont-Regular.ttf \
  --donor path/to/donor.ttf \
  --output-ttf fonts/MyFontLiga-Regular.ttf \
  --output-woff2 fonts/MyFontLiga-Regular.woff2 \
  --suffix "Liga"
```

