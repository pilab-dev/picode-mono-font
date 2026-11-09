#!/usr/bin/env python3
"""
PiLAB Ligaturizer — Programming Ligature Injection Pipeline
============================================================
Developed by Progressive Innovation LAB (PiLAB)
https://pilab.hu

Extracts programming ligatures (from Fira Code / OpenType calt engines) and
injects them into any fixed-pitch monospace developer font.

Supported Ligatures Include:
- Multi-char arrows:   ->  -->  ->>  ->|  <-  <--  <<-  |<-
- Fat/lambda arrows:   =>  ==>  =>>  <=  <==  <=>
- Comparisons:         ===  !==  ==  !=  /=  <=  >=  =:=  :=
- Logical / Bitwise:   &&  ||  ||=  &&=
- Web / XML comments:  <!--  -->  </  />  </>
- Scope & Ranges:      ::  :::  ..  ...  ..<
- Markdown & Code:     /*  */  /**  ///  ??  ?:  ??=
"""

import argparse
import copy
import os
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform


def find_default_donor(is_bold=False):
    """
    Locates an available ligature donor font from environment or system font paths.
    """
    env_var = "PILAB_LIGATURE_DONOR_BOLD" if is_bold else "PILAB_LIGATURE_DONOR_REGULAR"
    if env_var in os.environ and os.path.exists(os.environ[env_var]):
        return os.environ[env_var]

    search_dirs = [
        os.path.expanduser("~/Library/Fonts"),
        "/Library/Fonts",
        os.path.join(os.path.dirname(__file__), "source")
    ]
    target_pattern = "bold" if is_bold else "regular"
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            fl = fname.lower()
            if fl.endswith(".ttf") and ("liga" in fl or "fira" in fl):
                if is_bold and ("bold" in fl or "-b" in fl):
                    return os.path.join(d, fname)
                elif not is_bold and ("bold" not in fl):
                    return os.path.join(d, fname)
    return ""


def ligaturize_font(base_font_path, donor_font_path, output_ttf_path, output_woff2_path,
                    family_suffix="Liga"):
    """
    Injects ligature glyphs and the GSUB 'calt' table from a donor font into a base monospace font.
    """
    print(f"\n[+] Ligaturizing font:")
    print(f"    Base Font:   {base_font_path}")
    print(f"    Donor Font:  {donor_font_path}")

    if not os.path.exists(base_font_path):
        raise FileNotFoundError(f"Base font not found: {base_font_path}")
    if not os.path.exists(donor_font_path):
        raise FileNotFoundError(f"Ligature donor font not found: {donor_font_path}")

    base = TTFont(base_font_path)
    donor = TTFont(donor_font_path)

    if 'GSUB' not in donor:
        raise ValueError(f"Donor font does not contain a GSUB table: {donor_font_path}")

    # Determine metric ratios
    target_advance = base['hhea'].advanceWidthMax
    donor_advance = donor['hhea'].advanceWidthMax

    # Compute horizontal scaling factor
    scale_x = target_advance / donor_advance if donor_advance > 0 else 1.0
    # Keep vertical dimension proportional to preserve operator alignment
    scale_y = scale_x

    print(f"    Target Advance: {target_advance} | Donor Advance: {donor_advance} | Scale: {scale_x:.4f}")

    donor_gs = donor.getGlyphSet()
    base_glyf = base['glyf']
    base_hmtx = base['hmtx'].metrics

    # Collect ligature glyphs: any glyph starting with lig. or CR.
    donor_order = donor.getGlyphOrder()
    ligature_glyphs = [g for g in donor_order if g.startswith('lig.') or g.startswith('CR.')]

    if not ligature_glyphs:
        raise ValueError("No ligature glyphs (lig.* / CR.*) detected in donor font.")

    print(f"    Injecting {len(ligature_glyphs)} ligature glyphs into base font...")

    for name in ligature_glyphs:
        rec = DecomposingRecordingPen(donor_gs)
        donor_gs[name].draw(rec)

        pen = TTGlyphPen(None)
        t = Transform(scale_x, 0, 0, scale_y, 0, 0)
        tpen = TransformPen(pen, t)
        rec.replay(tpen)

        base_glyf[name] = pen.glyph()

        orig_w, orig_lsb = donor['hmtx'][name]
        # In fixed-pitch monospace ligatures, advance width is always cell width
        base_hmtx[name] = (target_advance, round(orig_lsb * scale_x))

    # Update glyph order in base font
    existing_order = list(base.getGlyphOrder())
    new_glyphs = [g for g in ligature_glyphs if g not in existing_order]
    base.setGlyphOrder(existing_order + new_glyphs)

    # Inject and deep-copy GSUB table
    base['GSUB'] = copy.deepcopy(donor['GSUB'])

    # Update metadata to reflect ligature support
    if family_suffix:
        name_table = base['name']
        for record in name_table.names:
            txt = record.toUnicode()
            # If family name record (1, 4, 16)
            if record.nameID in (1, 4, 16):
                if family_suffix not in txt:
                    # e.g. "PiCode Mono" -> "PiCode Mono Liga"
                    # e.g. "PiCode Mono Latin2" -> "PiCode Mono Liga Latin2"
                    if "Latin2" in txt:
                        new_txt = txt.replace("Latin2", f"{family_suffix} Latin2")
                    else:
                        new_txt = f"{txt} {family_suffix}"
                    record.string = new_txt.encode(record.getEncoding())
            elif record.nameID in (3, 6):  # Unique ID & PostScript name
                if family_suffix not in txt:
                    if "Latin2" in txt:
                        new_txt = txt.replace("Latin2", f"{family_suffix}Latin2")
                    else:
                        new_txt = txt.replace("-Regular", f"{family_suffix}-Regular").replace("-Bold", f"{family_suffix}-Bold")
                    record.string = new_txt.encode(record.getEncoding())

    # Export Desktop TTF
    os.makedirs(os.path.dirname(os.path.abspath(output_ttf_path)), exist_ok=True)
    base.save(output_ttf_path)
    ttf_size = os.path.getsize(output_ttf_path)
    total_glyphs = len(base.getGlyphOrder())
    print(f"  ✓ Exported Ligaturized TTF:   {output_ttf_path} ({ttf_size:,} bytes, {total_glyphs} glyphs)")

    # Export Webfont WOFF2
    os.makedirs(os.path.dirname(os.path.abspath(output_woff2_path)), exist_ok=True)
    base.flavor = 'woff2'
    base.save(output_woff2_path)
    woff2_size = os.path.getsize(output_woff2_path)
    print(f"  ✓ Exported Ligaturized WOFF2: {output_woff2_path} ({woff2_size:,} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="PiLAB Ligaturizer — Programming Ligature Injection Tool"
    )
    parser.add_argument(
        "--base",
        help="Path to base monospace TTF font (e.g. fonts/PiCodeMono-Regular.ttf)"
    )
    parser.add_argument(
        "--donor",
        help="Path to ligature donor TTF font (e.g. FiraCode or ligaturized donor)"
    )
    parser.add_argument(
        "--output-ttf",
        help="Path for output ligaturized TTF"
    )
    parser.add_argument(
        "--output-woff2",
        help="Path for output ligaturized WOFF2"
    )
    parser.add_argument(
        "--suffix",
        default="Liga",
        help="Family name suffix for ligaturized font (default: 'Liga')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Batch-process all 4 PiCode Mono fonts (Regular, Bold, Latin2-Regular, Latin2-Bold)"
    )

    args = parser.parse_args()

    print("=" * 72)
    print("  PILAB LIGATURIZER — PROGRAMMING LIGATURE ENGINE")
    print("  Progressive Innovation LAB (PiLAB) Typography Engineering")
    print("=" * 72)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")

    donor_reg = args.donor or find_default_donor(is_bold=False)
    donor_bold = args.donor or find_default_donor(is_bold=True)

    if args.all or not args.base:
        # Batch mode: generate all 4 editions
        targets = [
            {
                "base": os.path.join(fonts_dir, "PiCodeMono-Regular.ttf"),
                "donor": donor_reg,
                "out_ttf": os.path.join(fonts_dir, "PiCodeMonoLiga-Regular.ttf"),
                "out_woff2": os.path.join(fonts_dir, "PiCodeMonoLiga-Regular.woff2"),
            },
            {
                "base": os.path.join(fonts_dir, "PiCodeMono-Bold.ttf"),
                "donor": donor_bold,
                "out_ttf": os.path.join(fonts_dir, "PiCodeMonoLiga-Bold.ttf"),
                "out_woff2": os.path.join(fonts_dir, "PiCodeMonoLiga-Bold.woff2"),
            },
            {
                "base": os.path.join(fonts_dir, "PiCodeMono-Latin2-Regular.ttf"),
                "donor": donor_reg,
                "out_ttf": os.path.join(fonts_dir, "PiCodeMonoLiga-Latin2-Regular.ttf"),
                "out_woff2": os.path.join(fonts_dir, "PiCodeMonoLiga-Latin2-Regular.woff2"),
            },
            {
                "base": os.path.join(fonts_dir, "PiCodeMono-Latin2-Bold.ttf"),
                "donor": donor_bold,
                "out_ttf": os.path.join(fonts_dir, "PiCodeMonoLiga-Latin2-Bold.ttf"),
                "out_woff2": os.path.join(fonts_dir, "PiCodeMonoLiga-Latin2-Bold.woff2"),
            },
        ]

        for t in targets:
            ligaturize_font(
                base_font_path=t["base"],
                donor_font_path=t["donor"],
                output_ttf_path=t["out_ttf"],
                output_woff2_path=t["out_woff2"],
                family_suffix=args.suffix
            )

        print("\n[✔] Batch ligaturization completed successfully. All 4 Liga targets generated.")
    else:
        out_ttf = args.output_ttf or args.base.replace(".ttf", "Liga.ttf")
        out_woff2 = args.output_woff2 or out_ttf.replace(".ttf", ".woff2")
        donor = args.donor or DEFAULT_DONOR_REGULAR

        ligaturize_font(
            base_font_path=args.base,
            donor_font_path=donor,
            output_ttf_path=out_ttf,
            output_woff2_path=out_woff2,
            family_suffix=args.suffix
        )
        print("\n[✔] Ligaturization completed successfully.")


if __name__ == "__main__":
    main()
