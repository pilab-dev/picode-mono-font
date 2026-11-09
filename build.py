#!/usr/bin/env python3
"""
PiCode Mono — Monospace Font Engineering & Compilation Pipeline
================================================================
Developed by Progressive Innovation LAB (PiLAB)
https://pilab.hu

A universal font transformation and monospacing pipeline for developer
programming fonts. Converts proportional TrueType glyph outlines into exact,
fixed-pitch monospace font binaries optimized for code editors (VS Code, Cursor,
JetBrains, Neovim), terminal emulators, and web applications.

Key Capabilities:
- True fixed-pitch normalization (100% of glyphs share identical advance width).
- Composite glyph decomposition to eliminate coordinate shifts during scaling.
- Optical horizontal scaling for wide glyphs (M, W, m, w, @, %) to prevent collision.
- Automatic optical horizontal centering for slender characters (i, l, 1, punctuation).
- Continuous underscores (___) spanning bounding cell margins for gapless snake_case.
- Precision box-drawing alignment (U+2500-U+257F) for seamless TUI/CLI borders.
- PANOSE monospaced classification and post.isFixedPitch compliance.
- Complete table sanitization: strips obsolete hinting bytecode and digital signatures.
- Dual output: Desktop TrueType (TTF) and Brotli-compressed Webfont (WOFF2).
"""

import argparse
import os
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.transform import Transform

# Golden aspect ratio for programming monospace fonts (0.60 * unitsPerEm)
DEFAULT_TARGET_WIDTH = 1228  # for unitsPerEm = 2048


def transform_glyph_outline(name, gs, glyf, target_width, max_w, box_center_x):
    """
    Decomposes, scales, and aligns a single glyph into a fixed-pitch cell.
    """
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)

    bp = BoundsPen(gs)
    rec.replay(bp)

    pen = TTGlyphPen(None)

    # 1. Whitespace or empty non-printing glyphs
    if bp.bounds is None or name in ('space', 'nbspace', 'uni00A0'):
        rec.replay(pen)
        glyf[name] = pen.glyph()
        return target_width, 0

    xMin, yMin, xMax, yMax = bp.bounds
    gw = xMax - xMin

    # 2. Continuous underscore concatenation (e.g. __init__, snake_case)
    if name == 'underscore':
        target_w = target_width + 10
        sx = target_w / gw
        dx = -5 - round(xMin * sx)
        t = Transform(sx, 0, 0, 1.0, dx, 0)
        tpen = TransformPen(pen, t)
        rec.replay(tpen)
        glyf[name] = pen.glyph()
        return target_width, -5

    # 3. Horizontal box-drawing (─, ━, ═) gapless joining
    elif name in ('uni2500', 'uni2501', 'uni2550'):
        target_w = target_width + 10
        sx = target_w / gw
        dx = -5 - round(xMin * sx)
        t = Transform(sx, 0, 0, 1.0, dx, 0)
        tpen = TransformPen(pen, t)
        rec.replay(tpen)
        glyf[name] = pen.glyph()
        return target_width, -5

    # 4. Vertical box-drawing (│, ┃, ║) centered alignment
    elif name in ('uni2502', 'uni2503', 'uni2551'):
        current_center = (xMin + xMax) / 2
        dx = round(box_center_x - current_center)
        t = Transform(1.0, 0, 0, 1.0, dx, 0)
        tpen = TransformPen(pen, t)
        rec.replay(tpen)
        glyf[name] = pen.glyph()
        return target_width, round(xMin + dx)

    # 5. Standard typographic characters & symbols
    if gw > max_w:
        # Optically condense wide characters to fit comfortably inside cell
        sx = max_w / gw
        sw = gw * sx
        target_lsb = round((target_width - sw) / 2)
        dx = target_lsb - round(xMin * sx)
    else:
        # Center slender or standard characters inside the cell
        sx = 1.0
        target_lsb = round((target_width - gw) / 2)
        dx = target_lsb - xMin

    t = Transform(sx, 0, 0, 1.0, dx, 0)
    tpen = TransformPen(pen, t)
    rec.replay(tpen)

    glyf[name] = pen.glyph()
    return target_width, target_lsb


def compile_monospace_font(input_path, output_ttf_path, output_woff2_path,
                           family_name="PiCode Mono", is_bold=False, is_latin2=False,
                           target_width=DEFAULT_TARGET_WIDTH):
    """
    Transforms a source TrueType font into a fixed-pitch monospace developer font.
    """
    variant_tag = "Latin-2" if is_latin2 else "Standard"
    weight_name = "Bold" if is_bold else "Regular"
    weight_class = 700 if is_bold else 400
    fs_selection = 32 if is_bold else 64  # Bit 5 = Bold, Bit 6 = Regular

    print(f"\n[+] Compiling: {family_name} {weight_name} [{variant_tag}]")
    print(f"    Source:  {input_path}")
    print(f"    Target Advance Width: {target_width} units")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Source font file not found: {input_path}")

    font = TTFont(input_path)
    glyph_order = font.getGlyphOrder()
    gs = font.getGlyphSet()
    glyf = font['glyf']

    full_family_name = f"{family_name} Latin2" if is_latin2 else family_name
    full_name = f"{full_family_name} {weight_name}"
    ps_suffix = "Latin2-" if is_latin2 else ""
    ps_name = f"{family_name.replace(' ', '')}-{ps_suffix}{weight_name}"

    if is_latin2:
        desc = (f"{full_family_name} is an engineered fixed-pitch developer programming font "
                "with full Central & Eastern European (ISO-8859-2 / Windows-1250) character coverage.")
    else:
        desc = (f"{full_family_name} is an engineered fixed-pitch developer programming font "
                "optimized for code editors, terminals, and high-readability development.")

    # Side margin for bounding wide glyphs
    margin = 75 if is_bold else 80
    max_w = target_width - 2 * margin
    box_center_x = target_width // 2

    # Strip legacy hinting tables & digital signatures
    tables_to_strip = ['hdmx', 'LTSH', 'VDMX', 'fpgm', 'prep', 'cvt ', 'DSIG']
    for tag in tables_to_strip:
        if tag in font:
            del font[tag]

    new_hmtx = {}
    transformed_count = 0

    for name in glyph_order:
        adv_w, lsb = transform_glyph_outline(name, gs, glyf, target_width, max_w, box_center_x)
        new_hmtx[name] = (adv_w, lsb)
        transformed_count += 1

    # Update horizontal metrics table (hmtx)
    font['hmtx'].metrics = new_hmtx

    # Flag fixed pitch in post table
    font['post'].isFixedPitch = 1

    # Update OS/2 table for Monospace classification
    font['OS/2'].xAvgCharWidth = target_width
    font['OS/2'].panose.bProportion = 9  # 9 = Monospaced in PANOSE spec
    font['OS/2'].usWeightClass = weight_class
    font['OS/2'].fsSelection = fs_selection

    if is_latin2:
        # Enable Latin-2 (CP-1250 / ISO-8859-2) code page bits in OS/2 table
        # Bit 1 = Latin 2 (Central Europe)
        font['OS/2'].ulCodePageRange1 |= (1 << 1)

    # Update horizontal header table (hhea)
    all_lsbs = [lsb for _, lsb in new_hmtx.values()]
    font['hhea'].advanceWidthMax = target_width
    font['hhea'].minLeftSideBearing = min(all_lsbs)
    font['hhea'].numberOfHMetrics = len(new_hmtx)

    # Clean and reconstruct name table
    name_records = [
        (0, "Copyright © 2026 Progressive Innovation LAB (PiLAB). All rights reserved."),
        (1, full_family_name),                   # Family Name
        (2, weight_name),                        # Subfamily Name
        (3, f"1.000;PILAB;{ps_name}"),           # Unique identifier
        (4, full_name),                          # Full Name
        (5, "Version 1.000; 2026; PILAB build"), # Version string
        (6, ps_name),                            # PostScript name
        (8, "Progressive Innovation LAB"),       # Manufacturer
        (9, "PiLAB Typography & Systems Engineering"),
        (10, desc),
        (11, "https://pilab.hu"),
        (16, full_family_name),                  # Typographic Family
        (17, weight_name),                       # Typographic Subfamily
    ]

    name_table = font['name']
    name_table.names = []

    for nameID, text in name_records:
        # Windows / Unicode (Platform 3, Encoding 1, Lang 1033)
        name_table.setName(text, nameID, platformID=3, platEncID=1, langID=0x0409)
        # Macintosh (Platform 1, Encoding 0, Lang 0)
        name_table.setName(text, nameID, platformID=1, platEncID=0, langID=0)

    # 1. Export Desktop TTF
    os.makedirs(os.path.dirname(os.path.abspath(output_ttf_path)), exist_ok=True)
    font.save(output_ttf_path)
    ttf_size = os.path.getsize(output_ttf_path)
    print(f"  ✓ Exported Desktop TTF:  {output_ttf_path} ({ttf_size:,} bytes, {transformed_count} glyphs)")

    # 2. Export Webfont WOFF2
    os.makedirs(os.path.dirname(os.path.abspath(output_woff2_path)), exist_ok=True)
    font.flavor = 'woff2'
    font.save(output_woff2_path)
    woff2_size = os.path.getsize(output_woff2_path)
    print(f"  ✓ Exported Webfont WOFF2: {output_woff2_path} ({woff2_size:,} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="PiCode Mono Monospace Font Engineering & Compilation Pipeline"
    )
    parser.add_argument(
        "--input-regular",
        default=os.environ.get("PILAB_FONT_SOURCE_REGULAR", os.path.join(os.path.dirname(__file__), "source", "regular.ttf")),
        help="Path to source regular TrueType font (or set PILAB_FONT_SOURCE_REGULAR env var)"
    )
    parser.add_argument(
        "--input-bold",
        default=os.environ.get("PILAB_FONT_SOURCE_BOLD", os.path.join(os.path.dirname(__file__), "source", "bold.ttf")),
        help="Path to source bold TrueType font (or set PILAB_FONT_SOURCE_BOLD env var)"
    )
    parser.add_argument(
        "--family",
        default="PiCode Mono",
        help="Base font family name (default: 'PiCode Mono')"
    )
    parser.add_argument(
        "--target-width",
        type=int,
        default=DEFAULT_TARGET_WIDTH,
        help=f"Target advance width in font units (default: {DEFAULT_TARGET_WIDTH})"
    )
    parser.add_argument(
        "--output-dir",
        default="fonts",
        help="Output directory for generated fonts (default: 'fonts')"
    )

    args = parser.parse_args()

    print("=" * 72)
    print("  PICODE MONO — MONOSPACE FONT COMPILATION PIPELINE")
    print("  Progressive Innovation LAB (PiLAB) Typography Engineering")
    print("=" * 72)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, args.output_dir)

    build_targets = [
        # Standard Family
        {
            "src": args.input_regular,
            "ttf": os.path.join(out_dir, "PiCodeMono-Regular.ttf"),
            "woff2": os.path.join(out_dir, "PiCodeMono-Regular.woff2"),
            "bold": False,
            "latin2": False,
        },
        {
            "src": args.input_bold,
            "ttf": os.path.join(out_dir, "PiCodeMono-Bold.ttf"),
            "woff2": os.path.join(out_dir, "PiCodeMono-Bold.woff2"),
            "bold": True,
            "latin2": False,
        },
        # Latin-2 Dedicated Family (ISO-8859-2 / CP-1250)
        {
            "src": args.input_regular,
            "ttf": os.path.join(out_dir, "PiCodeMono-Latin2-Regular.ttf"),
            "woff2": os.path.join(out_dir, "PiCodeMono-Latin2-Regular.woff2"),
            "bold": False,
            "latin2": True,
        },
        {
            "src": args.input_bold,
            "ttf": os.path.join(out_dir, "PiCodeMono-Latin2-Bold.ttf"),
            "woff2": os.path.join(out_dir, "PiCodeMono-Latin2-Bold.woff2"),
            "bold": True,
            "latin2": True,
        },
    ]

    for target in build_targets:
        compile_monospace_font(
            input_path=target["src"],
            output_ttf_path=target["ttf"],
            output_woff2_path=target["woff2"],
            family_name=args.family,
            is_bold=target["bold"],
            is_latin2=target["latin2"],
            target_width=args.target_width
        )

    print("\n[✔] Font pipeline finished successfully. All font targets generated.")


if __name__ == "__main__":
    main()
