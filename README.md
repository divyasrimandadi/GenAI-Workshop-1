# Backend: Setup, Run and Troubleshooting (Windows)

Step-by-step commands to get the Ingestion Firewall API running on Windows PowerShell, plus how to diagnose the most common failure. Run every command from the `backend` folder unless a step says otherwise.

## 1. Add your Groq API key

Create `backend\.env` from the example (the repo only ships `.env.example`):

```powershell
copy .env.example .env
notepad .env
```

Set both values. No quotes, no spaces around `=`:

```env
GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Get a key at https://console.groq.com/keys. Never commit `.env`.

> **Model note:** the original default, `llama-3.3-70b-versatile`, no longer exists on Groq and causes every request to fail. Use `openai/gpt-oss-120b`, or another model from the list in step 8.

## 2. Create the virtual environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks `Activate.ps1`, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Run the tests

```powershell
pytest -q
```

Expected: `4 passed`. These tests only check the Pydantic schemas; they do not call the LLM.

## 4. Start the backend (terminal 1)

```powershell
uvicorn app.main:app --reload --port 8000
```

Check it: http://127.0.0.1:8000/health should return `{"status":"ok",...}`.

## 5. Start the frontend (terminal 2)

From the project root (one level above `backend`):

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

## 6. Open in the browser

```powershell
Start-Process http://127.0.0.1:5500        # frontend
Start-Process http://127.0.0.1:8000/docs   # interactive API docs
```

## 7. Send a test request

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/analyze `
  -ContentType "application/json" `
  -Body '{"message":"Where is my order?"}'
```

Expected response:

```json
{
  "intent": "order_tracking",
  "risk_profile": "medium",
  "priority": "medium",
  "requires_action": true,
  "summary": "User is asking for the status/location of their order.",
  "token_metadata": { "estimated_input_tokens": 5, "note": "..." }
}
```

Exact `summary` wording varies between runs.

## 8. Troubleshooting: `502 LLM request failed`

The API hides the real cause behind this generic message. Call the service directly to see the actual error (venv active):

```powershell
python -c "from app.services.llm_service import analyze_message; print(analyze_message('Hi'))"
```

| Error shown | Meaning | Fix |
|---|---|---|
| `401` / invalid API key | Key is wrong or revoked | Fix `GROQ_API_KEY` in `.env` |
| `404 model_not_found` | Model retired or not available to your key | Pick a model from the list below |
| `GROQ_API_KEY is missing` | `.env` not found or empty | Check `backend\.env` exists and is not `.env.txt` |
| Connection / timeout | No internet or Groq is down | Check network |

List the models your key can use:

```powershell
python -c "from groq import Groq; from app.config import GROQ_API_KEY; [print(m.id) for m in Groq(api_key=GROQ_API_KEY).models.list().data]"
```

To try a model without editing `.env` (the environment variable overrides the file for that terminal only):

```powershell
$env:GROQ_MODEL='openai/gpt-oss-120b'
uvicorn app.main:app --reload --port 8000
```

Restart `uvicorn` after any `.env` change.

## API reference

### `GET /health`

Returns `{"status": "ok", "message": "Ingestion Firewall API is running"}`. Does not call the LLM.

### `POST /api/analyze`

Request body:

```json
{ "message": "My payment was deducted twice." }
```

- `message`: 1–5000 characters, trimmed; whitespace-only is rejected. No other fields allowed.

Response fields:

| Field | Type / allowed values |
|---|---|
| `intent` | `greeting`, `order_tracking`, `payment_issue`, `current_time`, `general_question`, `unknown` |
| `risk_profile` | `low`, `medium`, `high`, `unknown` |
| `priority` | `low`, `medium`, `high` |
| `requires_action` | `true` if a follow-up service or tool would be needed to complete the request |
| `summary` | 1–500 characters describing the request |
| `token_metadata.estimated_input_tokens` | Local tiktoken estimate of the message, not billing data |

Status codes:

| Code | When |
|---|---|
| `200` | Valid, schema-checked result |
| `422` | Invalid request body (empty, too long, extra fields) |
| `502` | LLM call failed or output never passed validation (see troubleshooting) |

## Code walkthrough

| File | Role |
|---|---|
| `app/config.py` | Loads `GROQ_API_KEY` and `GROQ_MODEL` from `backend/.env`. Real environment variables take priority over the file. |
| `app/schemas/ingestion.py` | `IngestionRequest` (input) and `IngestionResult` (output) Pydantic models. `Literal` types restrict allowed values; `extra="forbid"` rejects unknown fields. |
| `app/services/llm_service.py` | System prompt with category and risk definitions. Wraps the Groq client with Instructor in JSON mode so the reply is parsed into `IngestionResult`; `temperature=0`, up to 2 retries on validation failure. |
| `app/utils/token_counter.py` | Counts tokens with tiktoken `cl100k_base`; falls back to word count × 2 if tiktoken fails. |
| `app/main.py` | FastAPI app, open CORS for local dev, `/health` and `/api/analyze`. Maps any failure to `502`. |
| `tests/test_ingestion.py` | 4 schema unit tests. No endpoint or LLM tests. |

## Known limitations

- When Instructor exhausts its retries it raises `InstructorRetryException`, not Pydantic's `ValidationError`, so validation failures reach the generic `502` message rather than the detailed one in `main.py`.
- `token_metadata` is part of the schema sent to the model, so the model may fill it; the token count is overwritten afterwards.
- A new Groq client is created on each request.
- CORS allows all origins; restrict it before deploying anywhere public.


# Frontend

An optional single-page UI for the Ingestion Firewall API. Plain HTML, CSS and JavaScript: no build step, no dependencies. You can skip it entirely and use the API docs at http://127.0.0.1:8000/docs instead.

## Run it

The backend must be running first (see [../backend/README.md](../backend/README.md)). Then, from the project root:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
Start-Process http://127.0.0.1:5500
```

Any static file server works; `http.server` is just the one that ships with Python. Stop it with `Ctrl+C`.

## Using the page

1. Type a message, or click an example button (Greeting, Order tracking, Payment issue, Current time) to fill one in.
2. Click **Analyze message**.
3. The validated JSON appears in the Response panel. **Copy JSON** copies it to the clipboard.

The status line under the button tells you what happened:

| Status | Meaning |
|---|---|
| `Success — response passed the Pydantic schema.` | Request worked |
| `Request failed (422)` | Message was empty or too long (max 5000 characters) |
| `Request failed (502)` | Backend could not get a valid LLM response; see the backend troubleshooting section |
| `Could not connect. Start the FastAPI backend...` | Backend is not running on port 8000 |

## Changing the backend URL

The API address is hardcoded at the top of `script.js`:

```js
const API_URL = "http://127.0.0.1:8000";
```

Change it if you run the backend on another host or port. The backend allows all origins (CORS `*`), so no backend change is needed for local use.

## Files

| File | Purpose |
|---|---|
| `index.html` | Page layout: message box, example buttons, result panel |
| `style.css` | Styling |
| `script.js` | Fills examples, sends `POST /api/analyze`, shows the result or error, handles Copy JSON |


# Enterprise Structured Ingestion Firewall

A beginner-friendly demo that classifies a customer-support message with a cloud LLM (Groq) and validates the structured result with Pydantic before returning it. The backend is FastAPI; the optional frontend is plain HTML/CSS/JavaScript.

The "firewall" is the schema: whatever the model returns must match a fixed set of fields and allowed values, or it is rejected.

## How it works

```text
Browser (frontend/)  ──POST /api/analyze {"message": "..."}──►  FastAPI (backend/app/main.py)
                                                                  │
                     1. IngestionRequest validates the input  ◄───┤  schemas/ingestion.py
                     2. Groq LLM classifies via Instructor    ◄───┤  services/llm_service.py
                     3. IngestionResult validates the output  ◄───┤  schemas/ingestion.py
                     4. Local token estimate is added         ◄───┘  utils/token_counter.py
                                                                  ▼
                                                    validated JSON response
```

Example: `"My payment was deducted twice. Please help urgently."` becomes

```json
{
  "intent": "payment_issue",
  "risk_profile": "high",
  "priority": "high",
  "requires_action": true,
  "summary": "User reports a duplicate payment deduction and requests urgent assistance.",
  "token_metadata": { "estimated_input_tokens": 10, "note": "Estimated locally; may differ from provider token counts." }
}
```

## Requirements

- Python 3.10+ (tested on 3.12)
- A Groq API key: https://console.groq.com/keys
- Internet access for the LLM request

## Quick start (Windows PowerShell)

```powershell
# 1. Backend setup
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env          # set GROQ_API_KEY and GROQ_MODEL=openai/gpt-oss-120b

# 2. Run tests
pytest -q

# 3. Start the API (leave running)
uvicorn app.main:app --reload --port 8000
```

In a second terminal, from the project root:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
Start-Process http://127.0.0.1:5500
```

On macOS/Linux, activate with `source .venv/bin/activate` and use `cp` instead of `copy`.

> **Model note:** `.env.example` still lists `llama-3.3-70b-versatile`, which no longer exists on Groq and makes every request fail with a 502. Set `GROQ_MODEL=openai/gpt-oss-120b` (or another available model) in your `.env`.

## Further docs

| Doc | Covers |
|---|---|
| [backend/README.md](backend/README.md) | Detailed setup, API reference, code walkthrough, troubleshooting the `502` error |
| [frontend/README.md](frontend/README.md) | Running the UI, changing the backend URL, how the page works |

## What this demo does and does not do

- The LLM classifies the message into a fixed set of intents: `greeting`, `order_tracking`, `payment_issue`, `current_time`, `general_question`, `unknown`.
- Instructor asks the model for a Pydantic-shaped result and retries up to 2 times if validation fails; Pydantic validates the final result.
- `tiktoken` estimates input tokens with an approximate tokenizer. It is not Groq billing data.
- It does **not** look up real orders or fetch the current time; it only classifies the request.
- Schema validation checks structure and allowed values, not factual truth or prompt-injection safety.
- No database is required.

## Folder layout

```text
enterprise-ingestion-firewall/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app and routes
│   │   ├── config.py                # loads .env
│   │   ├── schemas/ingestion.py     # request/result Pydantic models
│   │   ├── services/llm_service.py  # prompt + Groq/Instructor call
│   │   └── utils/token_counter.py   # tiktoken estimate
│   ├── tests/test_ingestion.py
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── README.md
└── README.md
```