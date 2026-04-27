"""
Craftora Pattern Generation API
FastAPI server — generates error-free craft patterns using GPT + Python structure builders.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from routers import crochet, knitting, embroidery, cross_stitch
from models.schemas import PatternResponse

load_dotenv()

app = FastAPI(
    title="Craftora Pattern API",
    description=(
        "AI-powered craft pattern generator for Crochet, Knitting, Embroidery, and Cross Stitch. "
        "Every pattern is mathematically validated for stitch count accuracy, gauge consistency, "
        "and instruction completeness before delivery."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow Flutter app to call the API) ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(crochet.router,     prefix="/api/v1")
app.include_router(knitting.router,    prefix="/api/v1")
app.include_router(embroidery.router,  prefix="/api/v1")
app.include_router(cross_stitch.router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status":  "online",
        "service": "Craftora Pattern API",
        "version": "1.0.0",
        "endpoints": {
            "crochet":      "/api/v1/crochet/generate",
            "knitting":     "/api/v1/knitting/generate",
            "embroidery":   "/api/v1/embroidery/generate",
            "cross_stitch": "/api/v1/cross_stitch/generate",
            "image_input":  "/api/v1/{craft}/generate-from-image",
            "docs":         "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    checks = {
        "api":      True,
        "openai":   bool(os.getenv("OPENAI_API_KEY")),
        "firebase": bool(os.getenv("FIREBASE_CREDENTIALS_PATH")),
    }
    return {"status": "healthy" if all(checks.values()) else "partial", "checks": checks}


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "message": "An unexpected error occurred."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
        log_level="info",
    )
