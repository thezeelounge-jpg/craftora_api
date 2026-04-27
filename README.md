# Craftora Pattern Generation API

AI-powered craft pattern generator — Python structures + GPT language polish + 10-rule validation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Test locally (no API keys needed)
python test_local.py

# 4. Start the server
python main.py
# API runs at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crochet/generate` | Generate crochet from text prompt |
| POST | `/api/v1/crochet/generate-from-image` | Generate crochet from image |
| POST | `/api/v1/knitting/generate` | Generate knitting from text prompt |
| POST | `/api/v1/knitting/generate-from-image` | Generate knitting from image |
| POST | `/api/v1/embroidery/generate` | Generate embroidery from text prompt |
| POST | `/api/v1/embroidery/generate-from-image` | Generate embroidery from image |
| POST | `/api/v1/cross_stitch/generate` | Generate cross stitch from text prompt |
| POST | `/api/v1/cross_stitch/generate-from-image` | Generate cross stitch from image |
| GET  | `/health` | Service health check |
| GET  | `/docs` | Swagger UI |

## Example Request (Flutter → API)

```json
POST /api/v1/crochet/generate
{
  "craft_type": "crochet",
  "skill_level": "beginner",
  "prompt": "A cozy granny square blanket in autumn colors, 50cm x 50cm",
  "terminology": "US",
  "yarn_weight": "worsted",
  "hook_size": "4mm",
  "gauge_sts": 18,
  "gauge_rows": 20,
  "width_cm": 50,
  "height_cm": 50,
  "export_pdf": false
}
```

## How It Works

```
User Input (text or image)
        ↓
GPT Engine (gpt-4o)
   - Extracts parameters from prompt
   - Generates pattern JSON structure
        ↓
Python Structure Builder (per craft)
   - Calculates exact stitch counts
   - Builds mathematically correct rows
   - Gauge validation
        ↓
10-Rule Validator
   1. Stitch Count Consistency
   2. Repeat Logic Must Be Exact
   3. Clear Construction Flow
   4. Gauge Validation
   5. Measurement Checkpoints
   6. Increase/Decrease Placement
   7. Terminology Consistency (US/UK)
   8. Instruction Completeness
   9. Assembly Accuracy
   10. Edge Case Testing
        ↓
GPT Polish Pass
   - Converts JSON to beautiful human-readable instructions
        ↓
Output: JSON + PDF (optional) + Firestore save
```

## Validation Score

| Score | Meaning |
|-------|---------|
| 90-100 | Excellent — ready to publish |
| 70-89  | Good — minor warnings only |
| 50-69  | Review needed — has warnings |
| 0-49   | Errors found — must fix before use |

## Firebase Setup

1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate new private key → download JSON
3. Save as `firebase_credentials.json` in project root
4. Add `FIREBASE_CREDENTIALS_PATH=firebase_credentials.json` to `.env`

## Flutter Integration

```dart
// In your Flutter app:
final response = await http.post(
  Uri.parse('https://your-api.com/api/v1/crochet/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'craft_type': 'crochet',
    'skill_level': 'beginner',
    'prompt': 'A small flower coaster, 10cm diameter',
    'terminology': 'US',
    'export_pdf': false,
  }),
);
final pattern = PatternResponse.fromJson(jsonDecode(response.body));
```

## Deploy for Free

### Railway (Recommended)
```bash
railway login
railway init
railway up
```

### Render
- Connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Fly.io
```bash
flyctl launch
flyctl deploy
```
