from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class CraftType(str, Enum):
    crochet      = "crochet"
    knitting     = "knitting"
    embroidery   = "embroidery"
    cross_stitch = "cross_stitch"


class SkillLevel(str, Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"


class TerminologySystem(str, Enum):
    us = "US"
    uk = "UK"


class PatternRequest(BaseModel):
    craft_type:  CraftType
    skill_level: SkillLevel
    prompt:      str         = Field(..., min_length=10)
    terminology: TerminologySystem = TerminologySystem.us
    yarn_weight: Optional[str]   = "worsted"
    hook_size:   Optional[str]   = None
    needle_size: Optional[str]   = None
    gauge_sts:   Optional[int]   = None
    gauge_rows:  Optional[int]   = None
    width_cm:    Optional[float] = None
    height_cm:   Optional[float] = None
    export_pdf:  bool = False


class ValidationIssue(BaseModel):
    rule:     str
    severity: Literal["error", "warning", "info"]
    message:  str
    row:      Optional[int] = None


class ValidationResult(BaseModel):
    passed:   bool
    errors:   List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    score:    int = Field(..., ge=0, le=100)


class PatternRow(BaseModel):
    row_number:   int
    instruction:  str
    stitch_count: int
    notes:        Optional[str] = None
    is_repeat:    bool = False
    repeat_times: Optional[int] = None


class Material(BaseModel):
    name:     str
    quantity: str
    notes:    Optional[str] = None


class GeneratedPattern(BaseModel):
    id:               Optional[str] = None
    title:            str
    description:      str
    craft_type:       CraftType
    skill_level:      SkillLevel
    terminology:      TerminologySystem
    yarn_weight:      Optional[str]  = None
    hook_or_needle:   Optional[str]  = None
    gauge:            Optional[str]  = None
    finished_size:    Optional[str]  = None
    estimated_time:   str
    materials:        List[Material]
    abbreviations:    dict
    rows:             List[PatternRow]
    finishing:        List[str]
    tips:             List[str]
    validation:       ValidationResult
    pdf_url:          Optional[str]  = None
    firestore_id:     Optional[str]  = None
    raw_instructions: str


class PatternResponse(BaseModel):
    success: bool
    pattern: Optional[GeneratedPattern] = None
    error:   Optional[str] = None
    message: str
