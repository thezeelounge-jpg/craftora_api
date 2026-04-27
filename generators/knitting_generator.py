"""
Craftora Knitting Pattern Generator
Builds mathematically correct knitting structure.
"""

import math
from typing import Optional, List
from models.schemas import PatternRow, Material


class KnittingStructureBuilder:

    GAUGE_DEFAULTS = {
        "lace": (28, 38), "fingering": (26, 36), "sport": (22, 30),
        "dk":   (20, 28), "worsted":   (18, 24), "aran":  (16, 22),
        "bulky": (12, 16), "super_bulky": (8, 11),
    }

    NEEDLE_DEFAULTS = {
        "lace": "2mm", "fingering": "2.5mm", "sport": "3.25mm",
        "dk": "3.75mm", "worsted": "4.5mm", "aran": "5mm",
        "bulky": "6.5mm", "super_bulky": "10mm",
    }

    def __init__(
        self,
        skill_level:  str   = "beginner",
        yarn_weight:  str   = "worsted",
        gauge_sts:    Optional[int]   = None,
        gauge_rows:   Optional[int]   = None,
        width_cm:     Optional[float] = None,
        height_cm:    Optional[float] = None,
        needle_size:  Optional[str]   = None,
        terminology:  str   = "US",
    ):
        self.skill_level = skill_level
        self.yarn_weight = yarn_weight.lower().replace(" ", "_")
        self.terminology = terminology

        default_gs, default_gr = self.GAUGE_DEFAULTS.get(self.yarn_weight, (18, 24))
        self.gauge_sts  = gauge_sts  or default_gs
        self.gauge_rows = gauge_rows or default_gr

        self.width_cm  = width_cm  or 20.0
        self.height_cm = height_cm or 20.0

        self.cast_on_sts = max(4, round((self.width_cm  / 10) * self.gauge_sts))
        self.total_rows  = max(4, round((self.height_cm / 10) * self.gauge_rows))

        # Make cast-on even for k2p2 rib
        if self.cast_on_sts % 4 != 0:
            self.cast_on_sts += (4 - self.cast_on_sts % 4)

        self.needle_size = needle_size or self.NEEDLE_DEFAULTS.get(self.yarn_weight, "4.5mm")

    # ── Stockinette rows ──────────────────────────────────────────────────────
    def build_stockinette(self) -> List[PatternRow]:
        rows = []
        # Cast on
        rows.append(PatternRow(
            row_number=1,
            instruction=f"Cast on {self.cast_on_sts} sts using long-tail cast on. [{self.cast_on_sts} sts]",
            stitch_count=self.cast_on_sts,
            notes="Leave a 15cm tail for seaming if needed.",
        ))
        # Ribbing rows (6 rows)
        rib_rows = 6 if self.skill_level != "beginner" else 4
        for r in range(2, rib_rows + 2):
            if r % 2 == 0:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(RS) *K2, p2; rep from * to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                    notes="RS = right side (public-facing side).",
                ))
            else:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(WS) *P2, k2; rep from * to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                ))

        # Main body
        body_start = rib_rows + 2
        body_end   = self.total_rows - 3
        for r in range(body_start, body_end + 1):
            notes = None
            if r == body_start:
                notes = "Begin stockinette body."
            elif r == self.total_rows // 2:
                notes = f"Piece should measure approx {self.height_cm / 2:.1f}cm from cast-on."

            if r % 2 == 0:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(RS) Knit to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                    notes=notes,
                ))
            else:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(WS) Purl to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                    notes=notes,
                ))

        # Final rib
        for r in range(body_end + 1, self.total_rows + 1):
            if r % 2 == 0:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(RS) *K2, p2; rep from * to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                    notes=f"Work measures approx {self.height_cm}cm." if r == self.total_rows - 1 else None,
                ))
            else:
                rows.append(PatternRow(
                    row_number=r,
                    instruction=f"(WS) *P2, k2; rep from * to end. [{self.cast_on_sts} sts]",
                    stitch_count=self.cast_on_sts,
                ))

        # Bind off
        rows.append(PatternRow(
            row_number=self.total_rows + 1,
            instruction=f"(RS) Bind off all {self.cast_on_sts} sts knitwise. Cut yarn leaving 15cm tail.",
            stitch_count=0,
            notes="Bind off loosely — use a needle one size larger if needed.",
        ))
        return rows

    # ── Garter stitch (beginner) ──────────────────────────────────────────────
    def build_garter(self) -> List[PatternRow]:
        rows = []
        rows.append(PatternRow(
            row_number=1,
            instruction=f"Cast on {self.cast_on_sts} sts. [{self.cast_on_sts} sts]",
            stitch_count=self.cast_on_sts,
        ))
        for r in range(2, self.total_rows + 1):
            notes = None
            if r == self.total_rows // 2:
                notes = f"Piece should measure approx {self.height_cm / 2:.1f}cm."
            rows.append(PatternRow(
                row_number=r,
                instruction=f"Knit to end. [{self.cast_on_sts} sts]",
                stitch_count=self.cast_on_sts,
                notes=notes,
            ))
        rows.append(PatternRow(
            row_number=self.total_rows + 1,
            instruction=f"Bind off all {self.cast_on_sts} sts. Weave in ends.",
            stitch_count=0,
        ))
        return rows

    def build_finishing(self) -> List[str]:
        return [
            "Weave in all ends on the wrong side using a tapestry needle.",
            "Block: wet-block or steam-block depending on yarn fiber.",
            f"Pin to {self.width_cm}cm x {self.height_cm}cm and allow to dry completely.",
            "Seam pieces together using mattress stitch for an invisible join (if applicable).",
        ]

    def build_materials(self) -> List[Material]:
        area = self.width_cm * self.height_cm
        yarn_g = max(50, round(area * 0.4))
        return [
            Material(name=f"{self.yarn_weight.replace('_',' ').title()} yarn",
                     quantity=f"Approx {yarn_g}g / {yarn_g * 2}m"),
            Material(name=f"{self.needle_size} straight or circular needles",
                     quantity="1 pair or 1 circular",
                     notes="Or size needed to obtain gauge"),
            Material(name="Tapestry needle", quantity="1"),
            Material(name="Scissors",        quantity="1"),
            Material(name="Stitch markers",  quantity="4"),
            Material(name="Tape measure",    quantity="1"),
        ]

    def build_abbreviations(self) -> dict:
        base = {
            "k":    "knit",
            "p":    "purl",
            "co":   "cast on",
            "bo":   "bind off",
            "rs":   "right side",
            "ws":   "wrong side",
            "sts":  "stitches",
            "rep":  "repeat",
            "pm":   "place marker",
            "sm":   "slip marker",
            "wyif": "with yarn in front",
            "wyib": "with yarn in back",
        }
        if self.skill_level in ["intermediate", "advanced"]:
            base.update({
                "k2tog": "knit 2 stitches together (right-leaning decrease)",
                "ssk":   "slip, slip, knit (left-leaning decrease)",
                "kfb":   "knit into front and back (increase)",
                "m1":    "make 1 stitch (increase)",
                "m1r":   "make 1 right",
                "m1l":   "make 1 left",
                "yo":    "yarn over (increase, creates eyelet)",
            })
        if self.skill_level == "advanced":
            base.update({
                "cn":   "cable needle",
                "c4f":  "cable 4 front",
                "c4b":  "cable 4 back",
                "dpn":  "double-pointed needles",
                "cdd":  "central double decrease",
            })
        return base


def build_knitting_structure(
    skill_level:  str,
    yarn_weight:  str,
    gauge_sts:    Optional[int],
    gauge_rows:   Optional[int],
    width_cm:     Optional[float],
    height_cm:    Optional[float],
    needle_size:  Optional[str],
    terminology:  str,
    pattern_type: str = "stockinette",
) -> dict:
    builder = KnittingStructureBuilder(
        skill_level=skill_level, yarn_weight=yarn_weight,
        gauge_sts=gauge_sts, gauge_rows=gauge_rows,
        width_cm=width_cm, height_cm=height_cm,
        needle_size=needle_size, terminology=terminology,
    )
    rows = builder.build_garter() if skill_level == "beginner" else builder.build_stockinette()
    return {
        "hook_or_needle": builder.needle_size,
        "yarn_weight":    yarn_weight,
        "gauge":          f"{builder.gauge_sts} sts x {builder.gauge_rows} rows = 10cm square",
        "finished_size":  f"{builder.width_cm}cm x {builder.height_cm}cm",
        "cast_on_sts":    builder.cast_on_sts,
        "total_rows":     builder.total_rows,
        "rows":           [r.model_dump() for r in rows],
        "finishing":      builder.build_finishing(),
        "materials":      [m.model_dump() for m in builder.build_materials()],
        "abbreviations":  builder.build_abbreviations(),
    }
