from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from models.schemas import (PatternRequest, PatternResponse, GeneratedPattern,
    CraftType, TerminologySystem, PatternRow, Material)
from core.validator import PatternValidator
from core.gpt_engine import generate_from_prompt, generate_from_image, polish_instructions
from core.firebase_client import save_pattern
from core.pdf_exporter import generate_pdf
import json

router = APIRouter(prefix="/knitting", tags=["Knitting"])


async def _process(gpt_data: dict, req_dict: dict, export_pdf: bool) -> PatternResponse:
    rows = []
    for r in gpt_data.get("rows", []):
        try:
            rows.append(PatternRow(
                row_number=int(r.get("row_number", 0)),
                instruction=str(r.get("instruction", "")),
                stitch_count=int(r.get("stitch_count", 0)),
                notes=r.get("notes"),
                is_repeat=bool(r.get("is_repeat", False)),
                repeat_times=r.get("repeat_times"),
            ))
        except Exception:
            continue

    finishing = gpt_data.get("finishing", [])
    materials = [Material(**m) if isinstance(m, dict) else m for m in gpt_data.get("materials", [])]

    validator  = PatternValidator(terminology=req_dict.get("terminology", "US"))
    validation = validator.validate(
        rows=rows, finishing=finishing, craft_type="knitting",
        gauge_sts=req_dict.get("gauge_sts"), gauge_rows=req_dict.get("gauge_rows"),
        width_cm=req_dict.get("width_cm"),   height_cm=req_dict.get("height_cm"),
    )

    raw_instructions = await polish_instructions(gpt_data, "knitting", req_dict.get("skill_level", "beginner"))

    pattern = GeneratedPattern(
        title=gpt_data.get("title", "Knitting Pattern"),
        description=gpt_data.get("description", ""),
        craft_type=CraftType.knitting,
        skill_level=req_dict.get("skill_level"),
        terminology=TerminologySystem(req_dict.get("terminology", "US")),
        yarn_weight=req_dict.get("yarn_weight") or gpt_data.get("yarn_weight"),
        hook_or_needle=gpt_data.get("hook_or_needle"),
        gauge=gpt_data.get("gauge"),
        finished_size=gpt_data.get("finished_size"),
        estimated_time=gpt_data.get("estimated_time", "2-4 hours"),
        materials=materials,
        abbreviations=gpt_data.get("abbreviations", {}),
        rows=rows,
        finishing=finishing,
        tips=gpt_data.get("tips", []),
        validation=validation,
        raw_instructions=raw_instructions,
    )

    pattern_dict = json.loads(pattern.model_dump_json())
    firestore_id = await save_pattern(pattern_dict)
    pattern.firestore_id = firestore_id

    if export_pdf:
        try:
            pdf_path = generate_pdf(pattern_dict)
            pattern.pdf_url = pdf_path
        except Exception as e:
            print(f"PDF generation failed: {e}")

    return PatternResponse(success=True, pattern=pattern, message="Pattern generated successfully!")


@router.post("/generate", response_model=PatternResponse, summary="Generate knitting pattern from text prompt")
async def generate(req: PatternRequest):
    try:
        gpt_data = await generate_from_prompt(
            prompt=req.prompt, craft_type="knitting",
            skill_level=req.skill_level.value, terminology=req.terminology.value,
            gauge_sts=req.gauge_sts, gauge_rows=req.gauge_rows,
            width_cm=req.width_cm, height_cm=req.height_cm,
            yarn_weight=req.yarn_weight,
        )
        return await _process(gpt_data, req.model_dump(), req.export_pdf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-image", response_model=PatternResponse, summary="Generate knitting pattern from image")
async def generate_from_image_endpoint(
    image:       UploadFile = File(...),
    skill_level: str  = Form("beginner"),
    terminology: str  = Form("US"),
    prompt:      str  = Form(""),
    export_pdf:  bool = Form(False),
):
    try:
        image_bytes = await image.read()
        gpt_data = await generate_from_image(
            image_bytes=image_bytes, image_mime=image.content_type,
            craft_type="knitting", skill_level=skill_level,
            terminology=terminology, prompt=prompt,
        )
        req_dict = {"skill_level": skill_level, "terminology": terminology, "export_pdf": export_pdf}
        return await _process(gpt_data, req_dict, export_pdf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
