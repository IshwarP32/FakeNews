# Free Deployment: Render + Vercel

This project can run on the free plans as two separate services:

- **Render Free Web Service:** FastAPI backend and Gemini verification pipeline
- **Vercel Hobby project:** React/Vite frontend

## Important ML model step

The repository ignores `models/*.joblib` and the training CSVs. The existing `models/model.joblib` is about 12 MB and can be stored in GitHub, but the two CSV files are about 116 MB combined and should remain out of Git.

For ML probabilities on Render, choose one option before deploying:

### Option A: Track the tested model artifact

Use this only if the model does not contain sensitive data:

```powershell
git add -f models/model.joblib
git commit -m "Add production ML model artifact"
git push origin main
```

After that, Render can load the model during deployment. Do not commit API keys or the CSV datasets.

### Option B: Host the model externally

Upload `models/model.joblib` to private object storage and download it during the Render build. Update `render.yaml` or the Render build command to fetch it securely using an environment variable. This is better for long-term maintenance.

Without either option, the AI verifier still works, but `ml_prediction` will be `null` because the model file is unavailable in the fresh Render checkout.

## 1. Deploy the backend to Render Free

1. Push the repository to GitHub.
2. Open Render and choose **New > Blueprint**.
3. Select the GitHub repository. Render will read [`render.yaml`](render.yaml).
4. Choose the **Free** plan if Render asks for a plan.
5. Add these environment variables to the backend service:

```text
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=*
```

`CORS_ORIGINS=*` is convenient for the first deployment. After Vercel is deployed, replace it with the exact Vercel URL, for example:

```text
CORS_ORIGINS=https://veriscan-ai.vercel.app
```

6. Deploy and wait for the service to become live.
7. Test the backend:

```text
https://YOUR-RENDER-SERVICE.onrender.com/api/health
https://YOUR-RENDER-SERVICE.onrender.com/docs
```

The free service uses:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

The free Render instance may sleep after inactivity. The first request after sleeping can take longer. Render's free filesystem is ephemeral, so learned examples in `backend/history_logs/ml_feedback.jsonl` are not durable across redeploys or instance replacement.

## 2. Deploy the frontend to Vercel Hobby

1. Open Vercel and choose **Add New > Project**.
2. Import the same GitHub repository.
3. Set **Root Directory** to `frontend`.
4. Use these settings:
   - Framework preset: `Vite`
   - Build command: `npm run build`
   - Output directory: `dist`
5. Add this environment variable:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

6. Deploy the project.
7. Copy the Vercel production URL.
8. Return to Render, replace `CORS_ORIGINS=*` with that exact Vercel URL, and redeploy the backend.

The Vite development proxy is used only locally. In production, `VITE_API_URL` makes the browser call Render directly.

## 3. Verify the deployed app

1. Open the Vercel URL.
2. Run a quick sample claim.
3. Confirm the API returns the AI verdict and grounded sources.
4. If the model artifact was deployed, confirm the response includes:

```json
{
  "ml_prediction": {
    "fake_probability": 12.3,
    "baseline_fake_probability": 12.3,
    "learned_examples": 0
  }
}
```

5. Run one undated historical claim and one explicitly current claim to check temporal reasoning.

## Free-tier limitations

- Render Free can sleep when idle.
- Render local files are not persistent storage for learning history.
- Vercel Hobby is suitable for the static Vite frontend; the backend remains on Render.
- Keep Gemini usage within the provider's free quota and rate limits.
