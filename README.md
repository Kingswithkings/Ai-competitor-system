# Ai-competitor-system

Streamlit is the dashboard. It can run the audit engine directly, or call a separate FastAPI backend if `API_BASE_URL` is configured.

## Run Locally

Option 1: run the dashboard directly:

```bash
python3 -m streamlit run frontend/dashboard.py
```

Option 2: run with a separate backend:

```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then start Streamlit with an API URL:

```bash
API_BASE_URL=http://127.0.0.1:8000 \
python3 -m streamlit run frontend/dashboard.py
```

## Streamlit Cloud

For the simplest Streamlit Cloud deployment, do not set `API_BASE_URL`. Add this secret only:

```toml
OPENAI_API_KEY = "your_openai_key"
```

The app will run audits directly inside Streamlit Cloud.

## Optional: Deploy Backend

If you want a separate FastAPI backend, deploy it to a public host first. In hosted apps, `127.0.0.1` means the hosting container itself, not your laptop.

Render setup:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service from this repo.
3. Use the included `render.yaml`, or set:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Add this Render environment variable:

```text
OPENAI_API_KEY=your_openai_key
```

5. After deploy, copy the Render backend URL. It should look like:

```text
https://ai-competitor-system-api.onrender.com
```

## Connect Streamlit Cloud To Backend

If you deployed the optional backend, open Streamlit Cloud app settings and add:

```toml
API_BASE_URL = "https://your-fastapi-backend-url"
OPENAI_API_KEY = "your_openai_key"
```

Then reboot or redeploy the Streamlit app.
