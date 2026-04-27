from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from models.schemas import PatternRequest, PatternResponse, GeneratedPattern, ValidationResult, CraftType, TerminologySystem
from generators.crochet_generator import build_crochet_structure
from core.validator import PatternValidator
from core.gpt_engine import generate_from_prompt, generate_from_image, polish_instructions, extract_parameters
from core.firebase_client import save_pattern
from core.pdf_exporter import generate_pdf
import json

router = APIRouter(prefix="/crochet", tags=["Crochet"])


async def _process_pattern(gpt_data: dict, req_dict: dict, export_pdf: bool) -> PatternResponse:
    """Shared processing: merge GPT output with structure, validate, save, return."""
    from models.schemas import PatternRow, Material

    rows_raw = gpt_data.get("rows", [])
    rows = []
    for r in rows_raw:
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

    # Validate
    validator = PatternValidator(terminology=req_dict.get("terminology", "US"))
    validation = validator.validate(
        rows=rows, finishing=finishing, craft_type="crochet",
        gauge_sts=req_dict.get("gauge_sts"), gauge_rows=req_dict.get("gauge_rows"),
        width_cm=req_dict.get("width_cm"), height_cm=req_dict.get("height_cm"),
    )

    # Polish instructions
    raw_instructions = await polish_instructions(gpt_data, "crochet", req_dict.get("skill_level", "beginner"))

    pattern = GeneratedPattern(
        title=gpt_data.get("title", "Crochet Pattern"),
        description=gpt_data.get("description", ""),
        craft_type=CraftType.crochet,
        skill_level=req_dict.get("skill_level"),
        terminology=TerminologySystem(req_dict.get("terminology", "US")),
        yarn_weight=req_dict.get("yarn_weight") or gpt_data.get("yarn_weight"),
        hook_or_needle=gpt_data.get("hook_or_needle") or req_dict.get("hook_size"),
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

    # Save to Firestore
    pattern_dict = json.loads(pattern.model_dump_json())
    firestore_id  = await save_pattern(pattern_dict)
    pattern.firestore_id = firestore_id

    # PDF export
    if export_pdf:
        try:
            pdf_path = generate_pdf(pattern_dict)
            pattern.pdf_url = pdf_path
        except Exception as e:
            print(f"PDF generation failed: {e}")

    return PatternResponse(success=True, pattern=pattern, message="Pattern generated successfully!")


@router.post("/generate", response_model=PatternResponse, summary="Generate crochet pattern from text prompt")
async def generate_crochet(req: PatternRequest):
    try:
        gpt_data = await generate_from_prompt(
            prompt=req.prompt, craft_type="crochet",
            skill_level=req.skill_level.value, terminology=req.terminology.value,
            gauge_sts=req.gauge_sts, gauge_rows=req.gauge_rows,
            width_cm=req.width_cm, height_cm=req.height_cm,
            yarn_weight=req.yarn_weight, hook_size=req.hook_size,
        )
        return await _process_pattern(gpt_data, req.model_dump(), req.export_pdf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-image", response_model=PatternResponse, summary="Generate crochet pattern from image")
async def generate_crochet_from_image(
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
            craft_type="crochet", skill_level=skill_level,
            terminology=terminology, prompt=prompt,
        )
        req_dict = {"skill_level": skill_level, "terminology": terminology, "export_pdf": export_pdf}
        return await _process_pattern(gpt_data, req_dict, export_pdf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-pdf/{filename}", summary="Download generated PDF")
async def download_pdf(filename: str):
    import os
    path = f"generated_pdfs/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)
