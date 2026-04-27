"""
Craftora GPT Engine
Handles both text-prompt generation and image-to-pattern (GPT Vision).
"""

import os
import json
import base64
import re
from typing import Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL  = os.getenv("OPENAI_MODEL", "gpt-4o")


# ── System prompts per craft ───────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "crochet": """You are an expert crochet pattern writer with 20 years of experience.
You write patterns that are clear, accurate, and beginner-friendly when needed.
Rules:
- Always use {terminology} terminology exclusively
- Every row/round MUST end with the stitch count in parentheses e.g. (24 sts)
- Use standard abbreviations only
- Include setup (foundation chain or magic ring) in Row 1
- Include 'Fasten off' as the final step
- Never mix US and UK terms
- For increases: state exact placement
- For decreases: state exact stitch to work into
Output ONLY valid JSON with the exact structure provided.""",

    "knitting": """You are an expert knitting pattern designer with 20+ years experience.
You write precise, mathematically correct patterns.
Rules:
- Always use {terminology} terminology
- Every row MUST end with stitch count in brackets e.g. [24 sts]
- Use standard abbreviations: k, p, k2tog, ssk, m1, co, bo, etc.
- Always specify RS (right side) and WS (wrong side) rows
- Include cast-on in Row 1
- End with bind-off instruction
- Specify needle size and yarn weight
Output ONLY valid JSON with the exact structure provided.""",

    "embroidery": """You are a master embroidery pattern designer.
You write clear, step-by-step embroidery instructions.
Rules:
- Always specify thread colors with DMC numbers
- State exact stitch types: satin stitch, stem stitch, French knot, backstitch, etc.
- Give directional guidance for each element
- Specify hoop size and fabric type
- Order instructions logically: stems first, then large fills, then details
- Include thread prep instructions
Output ONLY valid JSON with the exact structure provided.""",

    "cross_stitch": """You are an expert cross stitch pattern designer.
You write precise, grid-based cross stitch instructions.
Rules:
- Always use DMC thread color codes
- Specify fabric count (14-count Aida, 28-count evenweave, etc.)
- Give exact grid coordinates or relative positioning
- Order: full crosses first, then 3/4, half, quarter, then backstitching
- Include needle size (usually 24 or 26 tapestry)
- Start from center of fabric
Output ONLY valid JSON with the exact structure provided.""",
}


JSON_STRUCTURE = """
Return this exact JSON structure (no markdown, no extra text):
{
  "title": "pattern name",
  "description": "2-3 sentence description",
  "estimated_time": "X-Y hours",
  "hook_or_needle": "size",
  "gauge": "X sts x Y rows = 10cm",
  "finished_size": "WxH cm",
  "materials": [
    {"name": "material name", "quantity": "amount", "notes": "optional"}
  ],
  "abbreviations": {
    "abbr": "full meaning"
  },
  "rows": [
    {
      "row_number": 1,
      "instruction": "full instruction text (X sts)",
      "stitch_count": 0,
      "notes": "optional tip",
      "is_repeat": false,
      "repeat_times": null
    }
  ],
  "finishing": [
    "finishing step 1",
    "finishing step 2"
  ],
  "tips": [
    "helpful tip 1"
  ]
}
"""


# ── Extract parameters from prompt ────────────────────────────────────────────

async def extract_parameters(prompt: str, craft_type: str) -> dict:
    """Use GPT to extract structured parameters from a free-text prompt."""
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Extract pattern parameters from the user prompt for a {craft_type} pattern.
Return ONLY valid JSON with these fields (use null if not mentioned):
{{
  "title": "descriptive pattern name",
  "width_cm": null,
  "height_cm": null,
  "yarn_weight": null,
  "hook_size": null,
  "needle_size": null,
  "gauge_sts": null,
  "gauge_rows": null,
  "color_count": null,
  "main_colors": [],
  "style": null
}}"""
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=300,
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        return {}


# ── Generate pattern from text prompt ─────────────────────────────────────────

async def generate_from_prompt(
    prompt:      str,
    craft_type:  str,
    skill_level: str,
    terminology: str = "US",
    gauge_sts:   Optional[int]   = None,
    gauge_rows:  Optional[int]   = None,
    width_cm:    Optional[float] = None,
    height_cm:   Optional[float] = None,
    yarn_weight: Optional[str]   = None,
    hook_size:   Optional[str]   = None,
    needle_size: Optional[str]   = None,
) -> dict:
    """Generate a full pattern JSON from a text description."""

    system = SYSTEM_PROMPTS[craft_type].format(terminology=terminology)

    gauge_hint = ""
    if gauge_sts and gauge_rows:
        gauge_hint = f"\nGauge: {gauge_sts} sts x {gauge_rows} rows = 10cm square."
    size_hint = ""
    if width_cm and height_cm:
        size_hint = f"\nTarget finished size: {width_cm}cm wide x {height_cm}cm tall."
    tool_hint = ""
    if hook_size:
        tool_hint = f"\nHook size: {hook_size}."
    elif needle_size:
        tool_hint = f"\nNeedle size: {needle_size}."
    if yarn_weight:
        tool_hint += f"\nYarn weight: {yarn_weight}."

    user_message = f"""Create a {skill_level} level {craft_type} pattern.
Request: {prompt}
{gauge_hint}{size_hint}{tool_hint}
Skill level: {skill_level}
Terminology: {terminology}

{JSON_STRUCTURE}"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.4,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


# ── Generate pattern from image ───────────────────────────────────────────────

async def generate_from_image(
    image_bytes: bytes,
    image_mime:  str,
    craft_type:  str,
    skill_level: str,
    terminology: str = "US",
    prompt:      str = "",
) -> dict:
    """Analyze an image and generate a matching craft pattern."""

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    system = SYSTEM_PROMPTS[craft_type].format(terminology=terminology)

    extra = f"\nAdditional instructions from user: {prompt}" if prompt else ""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this image and create a {skill_level} {craft_type} pattern inspired by it.
Extract: colors, shapes, textures, patterns, dimensions if visible.
Create a complete, accurate, error-free pattern.{extra}

{JSON_STRUCTURE}""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_mime};base64,{b64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        temperature=0.4,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


# ── Polish raw instructions into human-readable text ──────────────────────────

async def polish_instructions(pattern_json: dict, craft_type: str, skill_level: str) -> str:
    """Take pattern JSON and write it as beautiful, clear human-readable instructions."""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""You are a professional {craft_type} pattern editor.
Convert the JSON pattern into beautifully formatted, clear written instructions.
- Write in second person (you, your)
- Include all rows with exact stitch counts
- Add helpful notes where appropriate
- Use proper section headers: Materials, Gauge, Pattern, Finishing
- Be encouraging but precise
- Skill level: {skill_level}""",
            },
            {
                "role": "user",
                "content": f"Convert this pattern to written instructions:\n{json.dumps(pattern_json, indent=2)}",
            },
        ],
        temperature=0.5,
        max_tokens=3000,
    )

    return response.choices[0].message.content.strip()
