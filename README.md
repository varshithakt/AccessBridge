# AccessBridge

AccessBridge is an accessible, guided public-service application MVP. Its catalog contains realistic **demonstration** forms; it does not submit to official government portals.

## Included

- React/Vite single-page application with register, login, accessibility onboarding, dashboard, service search, and guided dynamic forms.
- Visual-assistance mode using browser text-to-speech and Web Speech recognition when the browser supports it, with a visible text fallback.
- Hearing-friendly visual-first form flow, high-contrast control, enlarged text, keyboard focus styles, labels, error announcements, and a skip link.
- English, Kannada, and Hindi language preferences with fallback core guidance.
- Flask REST API, JWT authentication, bcrypt password hashes, server-side validation, draft/history support, fallback contextual help, document-upload foundation, and real PDF downloads.
- MongoDB persistence when `MONGO_URI` is configured and reachable. For a no-setup local demonstration only, the backend reports and uses an in-memory fallback (data resets when restarted).

## Run locally

Terminal 1 (backend):

```powershell
cd Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Terminal 2 (frontend):

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`).

## Environment variables

Create `Backend/.env` from `.env.example`:

```env
MONGO_URI=mongodb://localhost:27017/accessbridge
JWT_SECRET=use-a-long-random-production-secret
AI_API_KEY=
PORT=5000
```

`MONGO_URI` is required for durable MongoDB storage. `AI_API_KEY` is reserved for a future provider adapter; this MVP intentionally supplies service-aware fallback responses when no AI provider is configured.

## Main demo

Register → choose **Visual Assistance** and English/Kannada → browse or voice-search “income certificate” → answer the generated questions by voice or text → review → complete → download the server-generated PDF. Switch accessibility preferences by returning to onboarding (after sign-in) to demonstrate a visual-first hearing-oriented flow.

## Known MVP boundaries

- Speech recognition depends on the browser (Chrome/Edge generally support it); text inputs remain fully usable everywhere.
- The document endpoint safely accepts PDFs/images and reports processing status, but OCR/extraction is deferred.
- An external LLM adapter is intentionally not enabled until an API provider is selected; fallback help is used instead.

## Karnataka official-portal assistance

`portal-extension/` contains a Chrome/Edge extension for the Nadakacheri portal. It detects visible fields, reads them aloud, accepts spoken answers, and fills the active field after the user explicitly starts the guide. Load it at `chrome://extensions` → enable **Developer mode** → **Load unpacked** → select `portal-extension`.

The extension intentionally excludes Aadhaar, password, OTP, CAPTCHA and submit controls. Users complete identity verification, payment and final submission directly on the official portal.
