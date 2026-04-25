# Ai-competitor-system

Streamlit is the dashboard. FastAPI is the backend API. The dashboard must be able to reach the backend URL.

## Run Locally

Start the backend:

```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the dashboard:

```bash
python3 -m streamlit run frontend/dashboard.py
```

Local dashboard API URL defaults to:

```text
http://127.0.0.1:8000
```

## Deploy Backend

If the dashboard runs on Streamlit Cloud, `127.0.0.1` is Streamlit Cloud itself, not your laptop. Deploy the FastAPI backend to a public host first.

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

## Connect Streamlit Cloud

In Streamlit Cloud, open the app settings and add this secret:

```toml
API_BASE_URL = "https://your-fastapi-backend-url"
```

Then reboot or redeploy the Streamlit app.
