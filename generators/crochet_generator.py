"""
Craftora Crochet Pattern Generator
Builds mathematically correct crochet structure, then GPT polishes it.
"""

import math
from typing import Optional, List
from models.schemas import PatternRow, Material


class CrochetStructureBuilder:
    """
    Builds the mathematical skeleton of a crochet pattern.
    GPT never touches the numbers — only the language.
    """

    # ── Gauge defaults by yarn weight ────────────────────────────────────────
    GAUGE_DEFAULTS = {
        "lace":     (28, 32), "fingering": (26, 30), "sport": (24, 26),
        "dk":       (21, 24), "worsted":   (18, 20), "aran":  (16, 18),
        "bulky":    (12, 14), "super_bulky": (8, 10),
    }

    # ── Hook size by yarn weight ──────────────────────────────────────────────
    HOOK_DEFAULTS = {
        "lace": "1.6mm", "fingering": "2.25mm", "sport": "3mm",
        "dk": "3.5mm", "worsted": "4mm", "aran": "5mm",
        "bulky": "6mm", "super_bulky": "9mm",
    }

    # ── Stitch multiples by skill level ──────────────────────────────────────
    STITCH_PATTERNS = {
        "beginner": {
            "flat": ["sc"],
            "round": ["sc", "sc inc"],
        },
        "intermediate": {
            "flat": ["sc", "hdc", "dc"],
            "round": ["sc", "hdc", "dc"],
        },
        "advanced": {
            "flat": ["sc", "hdc", "dc", "tr", "shell"],
            "round": ["sc", "hdc", "dc", "tr", "shell"],
        },
    }

    def __init__(
        self,
        skill_level:  str   = "beginner",
        yarn_weight:  str   = "worsted",
        gauge_sts:    Optional[int]   = None,
        gauge_rows:   Optional[int]   = None,
        width_cm:     Optional[float] = None,
        height_cm:    Optional[float] = None,
        hook_size:    Optional[str]   = None,
        terminology:  str   = "US",
    ):
        self.skill_level = skill_level
        self.yarn_weight = yarn_weight.lower().replace(" ", "_")
        self.terminology = terminology

        # Resolve gauge
        default_gs, default_gr = self.GAUGE_DEFAULTS.get(self.yarn_weight, (18, 20))
        self.gauge_sts  = gauge_sts  or default_gs
        self.gauge_rows = gauge_rows or default_gr

        # Resolve dimensions
        self.width_cm  = width_cm  or 20.0
        self.height_cm = height_cm or 20.0

        # Calculate stitch counts
        self.cast_on_sts = max(4, round((self.width_cm  / 10) * self.gauge_sts))
        self.total_rows  = max(2, round((self.height_cm / 10) * self.gauge_rows))

        self.hook_size = hook_size or self.HOOK_DEFAULTS.get(self.yarn_weight, "4mm")

    # ── Flat (back-and-forth) structure ───────────────────────────────────────
    def build_flat_rows(self) -> List[PatternRow]:
        rows = []
        stitch = "sc" if self.skill_level == "beginner" else "dc"
        turn_chain = 1 if stitch == "sc" else 3

        # Foundation row
        rows.append(PatternRow(
            row_number=1,
            instruction=(
                f"Foundation: Ch {self.cast_on_sts + (1 if stitch == 'sc' else 3)}. "
                f"{stitch.upper()} in 2nd ch from hook and each ch across. Turn."
            ),
            stitch_count=self.cast_on_sts,
            notes="This is your foundation row. Count your stitches.",
        ))

        for r in range(2, self.total_rows + 1):
            notes = None
            if r == self.total_rows // 2:
                half_h = self.height_cm / 2
                notes  = f"Piece should measure approximately {half_h:.1f}cm from start."
            if r == self.total_rows:
                notes = f"Work should measure approximately {self.height_cm}cm tall."

            rows.append(PatternRow(
                row_number=r,
                instruction=(
                    f"Ch {turn_chain}, {stitch} in each st across. Turn. "
                    f"({self.cast_on_sts} sts)"
                ),
                stitch_count=self.cast_on_sts,
                notes=notes,
            ))

        return rows

    # ── In-the-round (granny / circle) structure ──────────────────────────────
    def build_round_rows(self, rounds: int = 6) -> List[PatternRow]:
        rows = []

        # Round 1: Magic ring
        rows.append(PatternRow(
            row_number=1,
            instruction="Magic ring. Ch 1. 6 sc in ring. Join with sl st to first sc. (6 sts)",
            stitch_count=6,
            notes="Pull the magic ring tight after the 6 sc.",
        ))

        current_count = 6
        for r in range(2, rounds + 1):
            # Inc every other round for beginner, every round for intermediate
            if self.skill_level == "beginner":
                if r % 2 == 0:
                    instruction = f"Ch 1. 2 sc in each st around. Join. ({current_count * 2} sts)"
                    current_count *= 2
                else:
                    instruction = f"Ch 1. Sc in each st around. Join. ({current_count} sts)"
            else:
                # Distribute increases evenly
                increases   = current_count
                new_count   = current_count + increases
                sts_between = (current_count // increases) - 1
                instruction = (
                    f"Ch 1. [Sc in next {sts_between} sts, 2 sc in next st] "
                    f"x{increases}. Join. ({new_count} sts)"
                )
                current_count = new_count

            rows.append(PatternRow(
                row_number=r,
                instruction=instruction,
                stitch_count=current_count,
                is_repeat=(r % 2 == 0),
            ))

        return rows

    # ── Granny square structure ────────────────────────────────────────────────
    def build_granny_square(self, rounds: int = 4) -> List[PatternRow]:
        rows = []
        rows.append(PatternRow(
            row_number=1,
            instruction=(
                "Magic ring. Ch 3 (counts as dc). 2 dc in ring. Ch 2. "
                "[3 dc in ring, ch 2] 3 times. Join with sl st to top of ch-3. (12 dc, 4 ch-2 sps)"
            ),
            stitch_count=12,
            notes="The ch-2 spaces are your corners.",
        ))
        counts = [12, 24, 36, 48, 60]
        for r in range(2, min(rounds + 1, 6)):
            count = counts[r - 1]
            rows.append(PatternRow(
                row_number=r,
                instruction=(
                    f"Sl st to ch-2 corner sp. Ch 3, 2 dc in same sp. Ch 2. 3 dc in same sp. "
                    f"Ch 1. *[3 dc, ch 2, 3 dc] in next ch-2 sp. Ch 1.* Rep from * to * "
                    f"2 more times. Join. ({count} dc)"
                ),
                stitch_count=count,
                is_repeat=True,
                repeat_times=3,
            ))
        return rows

    # ── Finishing steps ───────────────────────────────────────────────────────
    def build_finishing(self) -> List[str]:
        return [
            "Fasten off leaving a 15cm tail.",
            "Weave in all ends using a yarn needle, going under at least 4-5 stitches in different directions.",
            "Block the finished piece by wetting it lightly, pinning to measurements, and allowing to dry flat.",
            "Final measurements: check against pattern dimensions.",
        ]

    # ── Materials list ────────────────────────────────────────────────────────
    def build_materials(self) -> List[Material]:
        # Estimate yarn based on dimensions
        area_cm2 = self.width_cm * self.height_cm
        yarn_grams = max(25, round(area_cm2 * 0.3))
        return [
            Material(name=f"{self.yarn_weight.replace('_', ' ').title()} weight yarn",
                     quantity=f"Approx {yarn_grams}g / {yarn_grams * 3}m",
                     notes="Any fiber — wool, cotton, or acrylic all work"),
            Material(name=f"Crochet hook",
                     quantity=self.hook_size,
                     notes="Or size needed to obtain gauge"),
            Material(name="Yarn needle",        quantity="1",    notes="For weaving in ends"),
            Material(name="Scissors",           quantity="1",    notes=None),
            Material(name="Stitch markers",     quantity="2-4",  notes="Removable type recommended"),
            Material(name="Tape measure",       quantity="1",    notes=None),
        ]

    # ── Abbreviation dict ─────────────────────────────────────────────────────
    def build_abbreviations(self) -> dict:
        base = {
            "ch":   "chain",
            "sl st":"slip stitch",
            "sc":   "single crochet (US)" if self.terminology == "US" else "double crochet (UK)",
            "hdc":  "half double crochet (US)" if self.terminology == "US" else "half treble crochet (UK)",
            "dc":   "double crochet (US)" if self.terminology == "US" else "treble crochet (UK)",
            "tr":   "treble crochet (US)" if self.terminology == "US" else "double treble crochet (UK)",
            "st":   "stitch",
            "sts":  "stitches",
            "inc":  "increase (2 sts in same st)",
            "dec":  "decrease (sc2tog)",
            "sp":   "space",
            "rep":  "repeat",
            "rnd":  "round",
            "RS":   "right side",
            "WS":   "wrong side",
            "blo":  "back loop only",
            "flo":  "front loop only",
            "yo":   "yarn over",
        }
        if self.skill_level == "advanced":
            base.update({
                "sc2tog": "single crochet 2 together (decrease)",
                "dc2tog": "double crochet 2 together (decrease)",
                "FPdc":   "front post double crochet",
                "BPdc":   "back post double crochet",
                "picot":  "ch 3, sl st in 3rd ch from hook",
            })
        return base


def build_crochet_structure(
    skill_level:  str,
    yarn_weight:  str,
    gauge_sts:    Optional[int],
    gauge_rows:   Optional[int],
    width_cm:     Optional[float],
    height_cm:    Optional[float],
    hook_size:    Optional[str],
    terminology:  str,
    pattern_type: str = "flat",
) -> dict:
    """
    Entry point: returns the full mathematical structure for a crochet pattern.
    pattern_type: 'flat', 'round', or 'granny'
    """
    builder = CrochetStructureBuilder(
        skill_level=skill_level, yarn_weight=yarn_weight,
        gauge_sts=gauge_sts, gauge_rows=gauge_rows,
        width_cm=width_cm, height_cm=height_cm,
        hook_size=hook_size, terminology=terminology,
    )

    if pattern_type == "round":
        rows = builder.build_round_rows()
    elif pattern_type == "granny":
        rows = builder.build_granny_square()
    else:
        rows = builder.build_flat_rows()

    return {
        "hook_or_needle": builder.hook_size,
        "yarn_weight":    yarn_weight,
        "gauge":          f"{builder.gauge_sts} sc x {builder.gauge_rows} rows = 10cm square",
        "finished_size":  f"{builder.width_cm}cm x {builder.height_cm}cm",
        "cast_on_sts":    builder.cast_on_sts,
        "total_rows":     builder.total_rows,
        "rows":           [r.model_dump() for r in rows],
        "finishing":      builder.build_finishing(),
        "materials":      [m.model_dump() for m in builder.build_materials()],
        "abbreviations":  builder.build_abbreviations(),
    }
