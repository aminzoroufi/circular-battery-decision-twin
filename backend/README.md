# Backend

FastAPI service for the Circular Battery Decision Twin. It receives battery images and operator settings from Unity, runs battery form-factor classification, looks up or predicts battery health, scores risk, chooses a lifecycle route, and writes logs/passports for the dashboard.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health`
- `GET /soh-model-metrics`
- `POST /classify-battery`
- `POST /predict-soh`
- `POST /inspect-battery`
- `POST /override-decision`
- `GET /inspection-log`
- `GET /latest-decision`
- `GET /latest-received-image`
- `GET /battery-passport/{battery_id}`
- `GET /battery-passports`

## Notes

The runtime classifier uses image pixels rather than folder or file names. If the trained model artifact is missing, the backend falls back to a simple deterministic image-feature classifier so the local demo can still run.
