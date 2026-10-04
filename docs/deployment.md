# Production Deployment

The application is deployed as two services:

- FastAPI backend on Render
- Vite frontend on Vercel

## Before deploying

The verification pipeline requires a `GEMINI_API_KEY`. Do not commit API keys.

## Render backend

1. Push the repository to GitHub.
2. In Render, select **New > Blueprint** and choose the repository. Render will read `render.yaml`.
3. Add `GEMINI_API_KEY` in the service environment settings.
4. Set `CORS_ORIGINS` temporarily to `*`, or set it to the final Vercel URL once it exists, for example `https://truth-signal.vercel.app`.
5. Confirm the health check at `https://YOUR-RENDER-SERVICE.onrender.com/api/health`.
6. Confirm the API docs at `https://YOUR-RENDER-SERVICE.onrender.com/docs`.

The backend start command is:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Render's free service can sleep when idle, so the first request after inactivity may be slow.

## Vercel frontend

1. In Vercel, import the same repository.
2. Set the project root directory to `frontend`.
3. Use these settings:
   - Framework preset: **Vite**
   - Build command: `npm run build`
   - Output directory: `dist`
4. Add this environment variable:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

5. Deploy and copy the resulting Vercel URL.
6. Update Render's `CORS_ORIGINS` to that exact URL and redeploy the backend.

The frontend uses `/api` locally through the Vite proxy. In production, `VITE_API_URL` is prepended automatically, so browser requests go to Render instead of Vercel.

## Local production check

```powershell
# backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# frontend, in another terminal
cd frontend
$env:VITE_API_URL = "http://127.0.0.1:8000"
npm run build
npm run preview
```

Test both a clearly true and clearly false sample. Check that the response contains `verdict` and grounded source evidence.
