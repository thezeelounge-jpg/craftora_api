"""
Craftora Embroidery Pattern Generator
"""
from typing import Optional, List
from models.schemas import PatternRow, Material


STITCH_TYPES = {
    "beginner":     ["running stitch", "backstitch", "satin stitch", "French knot", "lazy daisy"],
    "intermediate": ["stem stitch", "chain stitch", "long-and-short stitch", "fishbone stitch", "couching"],
    "advanced":     ["goldwork", "raised satin stitch", "stumpwork", "ribbon embroidery", "crewelwork"],
}

DMC_PALETTES = {
    "floral":    [("321", "Red"), ("3708", "Pink"), ("444", "Yellow"), ("469", "Green"), ("blanc", "White")],
    "nature":    [("469", "Forest Green"), ("3854", "Rust"), ("780", "Deep Gold"), ("3371", "Dark Brown"), ("762", "Silver")],
    "geometric": [("820", "Navy"), ("3607", "Purple"), ("3846", "Teal"), ("blanc", "White"), ("310", "Black")],
    "pastel":    [("3689", "Pale Pink"), ("3761", "Sky Blue"), ("955", "Mint"), ("3823", "Cream"), ("209", "Lavender")],
}


class EmbroideryStructureBuilder:

    HOOP_SIZES = {
        "small":  ("10cm (4\")", "6\" hoop"),
        "medium": ("15cm (6\")", "8\" hoop"),
        "large":  ("20cm (8\")", "10\" hoop"),
    }

    def __init__(
        self,
        skill_level: str = "beginner",
        width_cm:    Optional[float] = None,
        height_cm:   Optional[float] = None,
        color_theme: str = "floral",
        terminology: str = "US",
    ):
        self.skill_level = skill_level
        self.width_cm    = width_cm  or 15.0
        self.height_cm   = height_cm or 15.0
        self.color_theme = color_theme if color_theme in DMC_PALETTES else "floral"
        self.terminology = terminology
        self.colors      = DMC_PALETTES[self.color_theme]
        self.stitches    = STITCH_TYPES[self.skill_level]

        # Hoop size based on dimensions
        if max(self.width_cm, self.height_cm) <= 12:
            self.hoop = "15cm (6\") embroidery hoop"
        elif max(self.width_cm, self.height_cm) <= 18:
            self.hoop = "20cm (8\") embroidery hoop"
        else:
            self.hoop = "25cm (10\") embroidery hoop"

    def build_steps(self) -> List[PatternRow]:
        steps = []
        step_num = 1

        # Setup
        steps.append(PatternRow(
            row_number=step_num,
            instruction=(
                f"Transfer the design to your fabric using a light box or transfer paper. "
                f"Place fabric in the {self.hoop}, keeping the grain straight and fabric taut."
            ),
            stitch_count=0,
            notes="Fabric should be drum-tight in the hoop — no slack.",
        ))
        step_num += 1

        # Thread prep
        steps.append(PatternRow(
            row_number=step_num,
            instruction=(
                "Cut thread lengths of approx 45cm (18\"). Separate the strands "
                "and use 2 strands unless otherwise stated."
            ),
            stitch_count=0,
            notes="Longer lengths cause tangling and splitting.",
        ))
        step_num += 1

        # Main stitching steps based on color palette
        for i, (dmc_num, color_name) in enumerate(self.colors):
            stitch = self.stitches[i % len(self.stitches)]
            steps.append(PatternRow(
                row_number=step_num,
                instruction=(
                    f"Using DMC {dmc_num} ({color_name}): work {stitch} for the "
                    f"{'outlines and main stems' if i == 0 else 'fill areas' if i == 1 else 'detail and accent elements'}. "
                    f"Use 2 strands throughout."
                ),
                stitch_count=0,
                notes=f"Tip: work from the center outward for best results." if i == 0 else None,
            ))
            step_num += 1

        # Detail work
        if self.skill_level in ["intermediate", "advanced"]:
            steps.append(PatternRow(
                row_number=step_num,
                instruction=(
                    "Add shading by overlapping long-and-short stitches. "
                    "Work lighter colors first, then add darker shades on top."
                ),
                stitch_count=0,
                notes="Use 1 strand for finer shading details.",
            ))
            step_num += 1

        # Finishing
        steps.append(PatternRow(
            row_number=step_num,
            instruction=(
                "Secure all thread ends on the wrong side by running under 4-5 stitches "
                "in different directions. Trim excess thread close to fabric."
            ),
            stitch_count=0,
        ))
        return steps

    def build_finishing(self) -> List[str]:
        return [
            "Secure all thread tails on the wrong side.",
            "Remove from hoop and press gently with a damp cloth on the wrong side — never iron directly on embroidery.",
            "If displaying in a hoop: cut fabric leaving 4cm around hoop edge.",
            "Run a gathering stitch around the edge, pull tight, and secure at the back.",
            "Optional: back the hoop with felt or cardstock for a neat finish.",
        ]

    def build_materials(self) -> List[Material]:
        mats = [
            Material(name="28-count evenweave linen or cotton fabric",
                     quantity=f"{int(self.width_cm + 10)}cm x {int(self.height_cm + 10)}cm",
                     notes="Add 10cm extra on all sides for hooping"),
            Material(name=self.hoop, quantity="1", notes="Wood or plastic both work"),
            Material(name="Size 24-26 embroidery needle", quantity="2-3"),
            Material(name="Embroidery scissors",          quantity="1", notes="Sharp, small scissors"),
            Material(name="Water-soluble marker or transfer paper", quantity="1"),
        ]
        for dmc_num, color_name in self.colors:
            mats.append(Material(
                name=f"DMC Stranded Cotton {dmc_num}", quantity="1 skein",
                notes=color_name,
            ))
        return mats

    def build_abbreviations(self) -> dict:
        return {
            "RS":   "right side (front of fabric)",
            "WS":   "wrong side (back of fabric)",
            "2s":   "2 strands of thread",
            "1s":   "1 strand of thread",
            "BS":   "backstitch",
            "SS":   "satin stitch",
            "FK":   "French knot",
            "LD":   "lazy daisy stitch",
            "RS_st":"running stitch",
            "ChS":  "chain stitch",
            "StS":  "stem stitch",
            "L&S":  "long-and-short stitch",
        }


def build_embroidery_structure(
    skill_level:  str,
    width_cm:     Optional[float],
    height_cm:    Optional[float],
    terminology:  str,
    color_theme:  str = "floral",
) -> dict:
    builder = EmbroideryStructureBuilder(
        skill_level=skill_level, width_cm=width_cm,
        height_cm=height_cm, color_theme=color_theme, terminology=terminology,
    )
    return {
        "hook_or_needle": "Size 24-26 embroidery needle",
        "yarn_weight":    "stranded cotton thread",
        "gauge":          "N/A — embroidery is not gauge-dependent",
        "finished_size":  f"{builder.width_cm}cm x {builder.height_cm}cm",
        "rows":           [r.model_dump() for r in builder.build_steps()],
        "finishing":      builder.build_finishing(),
        "materials":      [m.model_dump() for m in builder.build_materials()],
        "abbreviations":  builder.build_abbreviations(),
    }
