"""
Craftora Pattern Validator
Enforces all 10 validation rules for error-free patterns.
"""

from typing import List, Tuple
from models.schemas import PatternRow, ValidationResult, ValidationIssue

# ── US / UK stitch abbreviation dictionaries ──────────────────────────────────
US_ABBREVIATIONS = {
    "ch", "sl st", "sc", "hdc", "dc", "tr", "dtr", "trtr",
    "sc2tog", "dc2tog", "inc", "dec", "blo", "flo", "sp",
    "yo", "pm", "sm", "rnd", "rep", "sk", "st", "sts",
    "k", "p", "k2tog", "ssk", "m1", "m1r", "m1l", "co", "bo",
    "kfb", "pfb", "wyif", "wyib", "cn",
}

UK_ABBREVIATIONS = {
    "ch", "ss", "dc", "htr", "tr", "dtr", "trtr",
    "dc2tog", "tr2tog", "inc", "dec", "blo", "flo", "sp",
    "yo", "pm", "sm", "rnd", "rep", "sk", "st", "sts",
}

# Terminology conflicts: US term -> UK equivalent
TERMINOLOGY_CONFLICTS_US = {"sc": "dc", "dc": "tr", "hdc": "htr", "tr": "dtr"}
TERMINOLOGY_CONFLICTS_UK = {v: k for k, v in TERMINOLOGY_CONFLICTS_US.items()}


class PatternValidator:
    def __init__(self, terminology: str = "US"):
        self.terminology = terminology
        self.issues: List[ValidationIssue] = []

    def _add_error(self, rule: str, message: str, row: int = None):
        self.issues.append(ValidationIssue(
            rule=rule, severity="error", message=message, row=row))

    def _add_warning(self, rule: str, message: str, row: int = None):
        self.issues.append(ValidationIssue(
            rule=rule, severity="warning", message=message, row=row))

    def _add_info(self, rule: str, message: str, row: int = None):
        self.issues.append(ValidationIssue(
            rule=rule, severity="info", message=message, row=row))

    # ── Rule 1: Stitch Count Consistency ─────────────────────────────────────
    def check_stitch_counts(self, rows: List[PatternRow]):
        for i, row in enumerate(rows):
            if row.stitch_count < 0:
                self._add_error(
                    "Stitch Count Consistency",
                    f"Row {row.row_number} has negative stitch count ({row.stitch_count}).",
                    row.row_number,
                )
            if row.stitch_count == 0 and "fasten off" not in row.instruction.lower():
                self._add_warning(
                    "Stitch Count Consistency",
                    f"Row {row.row_number} has 0 stitches but no fasten-off instruction.",
                    row.row_number,
                )
            # Check instruction contains numeric reference that matches count
            import re
            counts_in_text = re.findall(r"\((\d+)\s*(?:sts?)?\)", row.instruction)
            if counts_in_text:
                declared = int(counts_in_text[-1])
                if declared != row.stitch_count:
                    self._add_error(
                        "Stitch Count Consistency",
                        f"Row {row.row_number}: instruction says ({declared} sts) but stitch_count is {row.stitch_count}.",
                        row.row_number,
                    )

    # ── Rule 2: Repeat Logic Must Be Exact ───────────────────────────────────
    def check_repeat_logic(self, rows: List[PatternRow]):
        import re
        for row in rows:
            repeats = re.findall(r"\*(.+?)\*(?:\s*(\d+)\s*(?:more\s*)?times?)?", row.instruction)
            for repeat_body, times in repeats:
                if not times:
                    self._add_warning(
                        "Repeat Logic Must Be Exact",
                        f"Row {row.row_number}: repeat section found without explicit repeat count.",
                        row.row_number,
                    )

    # ── Rule 3: Clear Construction Flow ──────────────────────────────────────
    def check_construction_flow(self, rows: List[PatternRow]):
        if not rows:
            self._add_error("Clear Construction Flow", "Pattern has no rows.")
            return

        numbers = [r.row_number for r in rows]
        for i in range(1, len(numbers)):
            if numbers[i] != numbers[i - 1] + 1:
                self._add_error(
                    "Clear Construction Flow",
                    f"Gap detected: Row {numbers[i-1]} is followed by Row {numbers[i]} (missing rows in between).",
                )

        last = rows[-1]
        closing_words = ["fasten off", "bind off", "cast off", "seam", "join"]
        if not any(w in last.instruction.lower() for w in closing_words):
            self._add_warning(
                "Clear Construction Flow",
                "Last row does not contain a closing instruction (fasten off / bind off / seam).",
            )

    # ── Rule 4: Gauge Validation ──────────────────────────────────────────────
    def check_gauge(self, rows: List[PatternRow], gauge_sts: int, gauge_rows: int,
                    width_cm: float, height_cm: float):
        if not all([gauge_sts, gauge_rows, width_cm, height_cm]):
            self._add_info("Gauge Validation", "Gauge or dimensions not provided — skipping gauge check.")
            return

        expected_sts  = round((width_cm  / 10) * gauge_sts)
        expected_rows = round((height_cm / 10) * gauge_rows)

        if rows:
            actual_sts  = rows[0].stitch_count if rows[0].stitch_count > 0 else rows[1].stitch_count
            actual_rows = len(rows)

            sts_diff  = abs(actual_sts  - expected_sts)
            rows_diff = abs(actual_rows - expected_rows)

            if sts_diff > max(2, expected_sts * 0.05):
                self._add_error(
                    "Gauge Validation",
                    f"Stitch count mismatch: gauge expects ~{expected_sts} sts for {width_cm}cm, "
                    f"pattern starts with {actual_sts} sts (diff: {sts_diff}).",
                )
            if rows_diff > max(2, expected_rows * 0.10):
                self._add_warning(
                    "Gauge Validation",
                    f"Row count mismatch: gauge expects ~{expected_rows} rows for {height_cm}cm, "
                    f"pattern has {actual_rows} rows (diff: {rows_diff}).",
                )

    # ── Rule 5: Measurement Checkpoints ──────────────────────────────────────
    def check_measurement_checkpoints(self, rows: List[PatternRow], height_cm: float):
        if not height_cm:
            return
        checkpoint_rows = [r for r in rows if "cm" in r.instruction or "inch" in r.instruction]
        if not checkpoint_rows and len(rows) > 10:
            self._add_warning(
                "Measurement Checkpoints",
                "Pattern has more than 10 rows but no measurement checkpoints (e.g. 'work until piece measures X cm').",
            )

    # ── Rule 6: Increase / Decrease Placement ────────────────────────────────
    def check_inc_dec_balance(self, rows: List[PatternRow]):
        import re
        for i in range(1, len(rows)):
            prev = rows[i - 1]
            curr = rows[i]
            delta = curr.stitch_count - prev.stitch_count

            text = curr.instruction.lower()
            inc_count = len(re.findall(r"\binc\b|\bm1\b|\bkfb\b|\bincrease\b", text))
            dec_count = len(re.findall(r"\bdec\b|\bk2tog\b|\bssk\b|\bsc2tog\b|\bdecrease\b", text))
            net_change = inc_count - dec_count

            if delta != 0 and net_change == 0:
                self._add_warning(
                    "Increase/Decrease Placement Clarity",
                    f"Row {curr.row_number}: stitch count changes by {delta:+d} but no inc/dec found in instruction.",
                    curr.row_number,
                )
            if delta == 0 and net_change != 0:
                self._add_warning(
                    "Increase/Decrease Placement Clarity",
                    f"Row {curr.row_number}: inc/dec found but stitch count stays the same — check if they cancel out intentionally.",
                    curr.row_number,
                )

    # ── Rule 7: Terminology Consistency ──────────────────────────────────────
    def check_terminology(self, rows: List[PatternRow]):
        conflicts = (TERMINOLOGY_CONFLICTS_UK
                     if self.terminology == "US" else TERMINOLOGY_CONFLICTS_US)
        found_conflicts = []
        for row in rows:
            text_lower = row.instruction.lower()
            for wrong_term in conflicts:
                if f" {wrong_term} " in f" {text_lower} ":
                    found_conflicts.append((row.row_number, wrong_term, conflicts[wrong_term]))

        for row_num, wrong, correct in found_conflicts:
            self._add_error(
                "Terminology Consistency (US vs UK)",
                f"Row {row_num}: '{wrong}' is a {('UK' if self.terminology == 'US' else 'US')} term. "
                f"Use '{correct}' for {self.terminology} terminology.",
                row_num,
            )

    # ── Rule 8: Instruction Completeness ─────────────────────────────────────
    def check_completeness(self, rows: List[PatternRow], craft_type: str):
        setup_keywords = {
            "crochet":      ["chain", "ch ", "magic ring", "magic circle"],
            "knitting":     ["cast on", "co "],
            "embroidery":   ["transfer", "hoop", "thread needle"],
            "cross_stitch": ["find center", "start from center", "mark center"],
        }
        keywords = setup_keywords.get(craft_type, [])
        if rows:
            first_row = rows[0].instruction.lower()
            if not any(kw in first_row for kw in keywords):
                self._add_warning(
                    "Instruction Completeness",
                    f"First row may be missing a setup instruction (e.g. {keywords[0] if keywords else 'setup step'}).",
                    1,
                )

    # ── Rule 9: Assembly Accuracy ─────────────────────────────────────────────
    def check_assembly(self, finishing: List[str]):
        if not finishing:
            self._add_warning(
                "Assembly Accuracy",
                "No finishing instructions provided. Add seaming, weaving-in-ends, or blocking steps.",
            )
        else:
            text = " ".join(finishing).lower()
            if "weave" not in text and "end" not in text:
                self._add_info(
                    "Assembly Accuracy",
                    "Consider adding 'weave in all ends' to finishing instructions.",
                )

    # ── Rule 10: Edge Case Testing ────────────────────────────────────────────
    def check_edge_cases(self, rows: List[PatternRow]):
        if not rows:
            self._add_error("Edge Case Testing", "Pattern has no rows at all.")
            return
        if len(rows) == 1:
            self._add_warning("Edge Case Testing",
                              "Pattern has only 1 row — likely incomplete.")
        max_count = max(r.stitch_count for r in rows)
        if max_count > 500:
            self._add_warning(
                "Edge Case Testing",
                f"Very high stitch count detected ({max_count}) — verify this is intentional.",
            )
        for row in rows:
            if len(row.instruction) < 5:
                self._add_error(
                    "Edge Case Testing",
                    f"Row {row.row_number} instruction is too short ('{row.instruction}') — likely incomplete.",
                    row.row_number,
                )

    # ── Master Validate ───────────────────────────────────────────────────────
    def validate(
        self,
        rows:      List[PatternRow],
        finishing: List[str],
        craft_type: str,
        gauge_sts:  int   = None,
        gauge_rows: int   = None,
        width_cm:   float = None,
        height_cm:  float = None,
    ) -> ValidationResult:
        self.issues = []

        self.check_stitch_counts(rows)
        self.check_repeat_logic(rows)
        self.check_construction_flow(rows)
        self.check_gauge(rows, gauge_sts, gauge_rows, width_cm, height_cm)
        self.check_measurement_checkpoints(rows, height_cm)
        self.check_inc_dec_balance(rows)
        self.check_terminology(rows)
        self.check_completeness(rows, craft_type)
        self.check_assembly(finishing)
        self.check_edge_cases(rows)

        errors   = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]

        # Score: start at 100, -10 per error, -3 per warning
        score = max(0, 100 - len(errors) * 10 - len(warnings) * 3)
        passed = len(errors) == 0

        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            score=score,
        )
