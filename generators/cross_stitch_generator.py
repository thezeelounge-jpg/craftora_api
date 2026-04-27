"""
Craftora Cross Stitch Pattern Generator
"""
import math
from typing import Optional, List
from models.schemas import PatternRow, Material


DMC_COLORS = {
    "red":     [("321","Crimson"),("347","Dark Red"),("3801","Bright Red")],
    "blue":    [("820","Navy"),("334","Medium Blue"),("3761","Sky Blue")],
    "green":   [("699","Dark Green"),("704","Bright Green"),("3348","Light Green")],
    "purple":  [("550","Deep Violet"),("553","Violet"),("211","Lavender")],
    "neutral": [("310","Black"),("blanc","White"),("3865","Winter White"),("3371","Dark Brown")],
    "floral":  [("3831","Raspberry"),("3608","Pale Violet"),("907","Parrot Green"),("444","Lemon"),("blanc","White")],
    "pastel":  [("3689","Mauve"),("3755","Baby Blue"),("3817","Celadon"),("3823","Yellow Cream"),("819","Baby Pink")],
}

FABRIC_COUNT = {
    "beginner":     ("14-count Aida", 14),
    "intermediate": ("18-count Aida", 18),
    "advanced":     ("28-count evenweave", 28),
}


class CrossStitchStructureBuilder:

    def __init__(
        self,
        skill_level:  str   = "beginner",
        width_cm:     Optional[float] = None,
        height_cm:    Optional[float] = None,
        color_theme:  str   = "floral",
        terminology:  str   = "US",
    ):
        self.skill_level = skill_level
        self.width_cm    = width_cm  or 15.0
        self.height_cm   = height_cm or 15.0
        self.color_theme = color_theme if color_theme in DMC_COLORS else "floral"
        self.terminology = terminology

        self.fabric_name, self.count = FABRIC_COUNT[skill_level]
        self.colors = DMC_COLORS[self.color_theme]

        # Grid dimensions
        self.grid_w = math.ceil(self.width_cm  * (self.count / 2.54))
        self.grid_h = math.ceil(self.height_cm * (self.count / 2.54))

        # Center coordinates
        self.center_x = self.grid_w // 2
        self.center_y = self.grid_h // 2

    def build_steps(self) -> List[PatternRow]:
        steps = []

        # Step 1: Setup
        steps.append(PatternRow(
            row_number=1,
            instruction=(
                f"Cut a piece of {self.fabric_name} to {int(self.width_cm + 8)}cm x "
                f"{int(self.height_cm + 8)}cm. Fold in half horizontally, then vertically "
                f"to find center. Mark center point with a removable basting stitch."
            ),
            stitch_count=0,
            notes="Always start from the center — this ensures your design stays centered.",
        ))

        # Step 2: Thread prep
        steps.append(PatternRow(
            row_number=2,
            instruction=(
                "Cut stranded cotton to 45cm (18\") lengths. Separate into individual strands "
                f"and use {'2 strands' if self.count <= 14 else '1 strand'} in a size "
                f"{'24' if self.count <= 18 else '26'} tapestry needle."
            ),
            stitch_count=0,
            notes="Never knot your thread — secure by running under existing stitches.",
        ))

        # Steps per color
        for step_num, (dmc_num, color_name) in enumerate(self.colors, 3):
            if step_num == 3:
                area_desc = "the main focal element of your design, starting from the center"
            elif step_num == 4:
                area_desc = "background fills and large color blocks"
            else:
                area_desc = "accent areas and fine details"

            steps.append(PatternRow(
                row_number=step_num,
                instruction=(
                    f"Thread needle with DMC {dmc_num} ({color_name}). "
                    f"Work full cross stitches (×) for {area_desc}. "
                    f"Complete all stitches of this color before moving to next. "
                    f"Grid area: {self.grid_w} x {self.grid_h} = {self.grid_w * self.grid_h} squares total."
                ),
                stitch_count=self.grid_w * self.grid_h // max(1, len(self.colors)),
                notes=f"Always stitch all bottom diagonals (/) first, then cross with top diagonals (\\)."
                      if step_num == 3 else None,
            ))

        step_num = len(self.colors) + 3

        # Backstitch outlining (intermediate/advanced)
        if self.skill_level in ["intermediate", "advanced"]:
            outline_color = self.colors[-1]
            steps.append(PatternRow(
                row_number=step_num,
                instruction=(
                    f"Using 1 strand of DMC {outline_color[0]} ({outline_color[1]}): "
                    "add backstitch outlines around key design elements for definition. "
                    "Work backstitches AFTER all cross stitches are complete."
                ),
                stitch_count=0,
                notes="Use 1 strand for fine outlines — 2 strands will overpower the cross stitches.",
            ))
            step_num += 1

        # French knots (advanced)
        if self.skill_level == "advanced":
            steps.append(PatternRow(
                row_number=step_num,
                instruction=(
                    "Add French knot accents using 2 strands wrapped twice around needle. "
                    "Work knots at marked points on pattern chart."
                ),
                stitch_count=0,
                notes="Pull thread through slowly while holding it close to fabric.",
            ))
            step_num += 1

        return steps

    def build_finishing(self) -> List[str]:
        return [
            "Secure all thread ends by running under existing stitches on the WS — no knots.",
            "Wash gently in cool water with mild detergent if fabric is soiled.",
            "Press from the wrong side on a thick towel to protect the stitches.",
            "Frame or display: use a professional framer or a clip frame for best results.",
            "If using a hoop as frame: leave in hoop and tighten evenly. Back with felt.",
        ]

    def build_materials(self) -> List[Material]:
        mats = [
            Material(name=self.fabric_name,
                     quantity=f"{int(self.width_cm + 8)}cm x {int(self.height_cm + 8)}cm",
                     notes=f"Grid size: {self.grid_w} x {self.grid_h} squares"),
            Material(name=f"Size {'24' if self.count <= 18 else '26'} tapestry needle",
                     quantity="2-3"),
            Material(name="Embroidery scissors",   quantity="1"),
            Material(name="Water-soluble marker",  quantity="1", notes="For marking center"),
            Material(name="Frame or hoop",         quantity="1",
                     notes=f"Minimum {max(self.width_cm, self.height_cm) + 5:.0f}cm"),
        ]
        for dmc_num, color_name in self.colors:
            mats.append(Material(
                name=f"DMC Stranded Cotton {dmc_num}",
                quantity="1 skein", notes=color_name,
            ))
        return mats

    def build_abbreviations(self) -> dict:
        return {
            "×":    "full cross stitch",
            "½×":   "half cross stitch (bottom diagonal only)",
            "¼×":   "quarter cross stitch",
            "BS":   "backstitch",
            "FK":   "French knot",
            "RS":   "right side (front of fabric)",
            "WS":   "wrong side (back of fabric)",
            "1s":   "1 strand of thread",
            "2s":   "2 strands of thread",
            "DMC":  "thread brand and color code",
            "ct":   "count (fabric thread count per inch)",
        }


def build_cross_stitch_structure(
    skill_level:  str,
    width_cm:     Optional[float],
    height_cm:    Optional[float],
    terminology:  str,
    color_theme:  str = "floral",
) -> dict:
    builder = CrossStitchStructureBuilder(
        skill_level=skill_level, width_cm=width_cm,
        height_cm=height_cm, color_theme=color_theme, terminology=terminology,
    )
    return {
        "hook_or_needle": f"Size {'24' if builder.count <= 18 else '26'} tapestry needle",
        "yarn_weight":    "stranded cotton (DMC 6-strand)",
        "gauge":          f"{builder.count}-count fabric = {builder.count} squares per 2.54cm",
        "finished_size":  f"{builder.width_cm}cm x {builder.height_cm}cm",
        "grid_width":     builder.grid_w,
        "grid_height":    builder.grid_h,
        "rows":           [r.model_dump() for r in builder.build_steps()],
        "finishing":      builder.build_finishing(),
        "materials":      [m.model_dump() for m in builder.build_materials()],
        "abbreviations":  builder.build_abbreviations(),
    }
