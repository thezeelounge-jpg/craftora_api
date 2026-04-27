"""
Local test — runs the generators and validator WITHOUT needing OpenAI or Firebase.
Run: python test_local.py
"""

import asyncio
import json
from generators.crochet_generator import build_crochet_structure
from generators.knitting_generator import build_knitting_structure
from generators.embroidery_generator import build_embroidery_structure
from generators.cross_stitch_generator import build_cross_stitch_structure
from core.validator import PatternValidator
from models.schemas import PatternRow


def test_crochet():
    print("\n" + "="*60)
    print("TESTING CROCHET GENERATOR")
    print("="*60)
    data = build_crochet_structure(
        skill_level="beginner", yarn_weight="worsted",
        gauge_sts=18, gauge_rows=20,
        width_cm=20, height_cm=20,
        hook_size="4mm", terminology="US",
        pattern_type="flat",
    )
    rows = [PatternRow(**r) for r in data["rows"]]
    v = PatternValidator(terminology="US")
    result = v.validate(rows=rows, finishing=data["finishing"],
                        craft_type="crochet", gauge_sts=18, gauge_rows=20,
                        width_cm=20, height_cm=20)

    print(f"  Rows generated:  {len(rows)}")
    print(f"  First row:       {rows[0].instruction[:80]}...")
    print(f"  Validation:      {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"  Quality score:   {result.score}/100")
    print(f"  Errors:          {len(result.errors)}")
    print(f"  Warnings:        {len(result.warnings)}")
    for e in result.errors:
        print(f"    ❌ [{e.rule}] {e.message}")
    for w in result.warnings:
        print(f"    ⚠  [{w.rule}] {w.message}")


def test_knitting():
    print("\n" + "="*60)
    print("TESTING KNITTING GENERATOR")
    print("="*60)
    data = build_knitting_structure(
        skill_level="intermediate", yarn_weight="dk",
        gauge_sts=20, gauge_rows=28,
        width_cm=15, height_cm=20,
        needle_size="3.75mm", terminology="US",
    )
    rows = [PatternRow(**r) for r in data["rows"]]
    v = PatternValidator(terminology="US")
    result = v.validate(rows=rows, finishing=data["finishing"], craft_type="knitting",
                        gauge_sts=20, gauge_rows=28, width_cm=15, height_cm=20)
    print(f"  Rows generated:  {len(rows)}")
    print(f"  Cast-on:         {data['cast_on_sts']} sts")
    print(f"  Validation:      {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"  Quality score:   {result.score}/100")
    for e in result.errors:
        print(f"    ❌ [{e.rule}] {e.message}")
    for w in result.warnings:
        print(f"    ⚠  [{w.rule}] {w.message}")


def test_embroidery():
    print("\n" + "="*60)
    print("TESTING EMBROIDERY GENERATOR")
    print("="*60)
    data = build_embroidery_structure(
        skill_level="beginner", width_cm=15, height_cm=15,
        terminology="US", color_theme="floral",
    )
    rows = [PatternRow(**r) for r in data["rows"]]
    v = PatternValidator(terminology="US")
    result = v.validate(rows=rows, finishing=data["finishing"], craft_type="embroidery")
    print(f"  Steps generated: {len(rows)}")
    print(f"  Validation:      {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"  Quality score:   {result.score}/100")
    for e in result.errors:
        print(f"    ❌ [{e.rule}] {e.message}")
    for w in result.warnings:
        print(f"    ⚠  [{w.rule}] {w.message}")


def test_cross_stitch():
    print("\n" + "="*60)
    print("TESTING CROSS STITCH GENERATOR")
    print("="*60)
    data = build_cross_stitch_structure(
        skill_level="intermediate", width_cm=12, height_cm=12,
        terminology="US", color_theme="floral",
    )
    rows = [PatternRow(**r) for r in data["rows"]]
    v = PatternValidator(terminology="US")
    result = v.validate(rows=rows, finishing=data["finishing"], craft_type="cross_stitch")
    print(f"  Steps generated: {len(rows)}")
    print(f"  Grid size:       {data['grid_width']} x {data['grid_height']} squares")
    print(f"  Validation:      {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"  Quality score:   {result.score}/100")
    for e in result.errors:
        print(f"    ❌ [{e.rule}] {e.message}")
    for w in result.warnings:
        print(f"    ⚠  [{w.rule}] {w.message}")


def test_validator_catches_errors():
    print("\n" + "="*60)
    print("TESTING VALIDATOR ERROR DETECTION")
    print("="*60)
    # Deliberately broken pattern
    bad_rows = [
        PatternRow(row_number=1, instruction="Ch 20. Sc in 2nd ch. (19 sts)", stitch_count=18),  # count mismatch
        PatternRow(row_number=3, instruction="Ch 1. Sc across.", stitch_count=18),               # row 2 missing
        PatternRow(row_number=4, instruction="x", stitch_count=18),                              # too short
    ]
    v = PatternValidator(terminology="US")
    result = v.validate(rows=bad_rows, finishing=[], craft_type="crochet")
    print(f"  Errors found:    {len(result.errors)} (expected > 0)")
    print(f"  Quality score:   {result.score}/100 (expected < 70)")
    for e in result.errors:
        print(f"    ❌ [{e.rule}] {e.message}")
    for w in result.warnings:
        print(f"    ⚠  [{w.rule}] {w.message}")
    assert not result.passed, "Validator should have caught errors!"
    print("  ✅ Validator correctly caught all errors")


if __name__ == "__main__":
    test_crochet()
    test_knitting()
    test_embroidery()
    test_cross_stitch()
    test_validator_catches_errors()
    print("\n" + "="*60)
    print("ALL LOCAL TESTS COMPLETE")
    print("="*60)
    print("\nTo start the API server:")
    print("  pip install -r requirements.txt")
    print("  cp .env.example .env  (then add your OpenAI key)")
    print("  python main.py")
    print("\nAPI docs will be at: http://localhost:8000/docs")
