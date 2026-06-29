# Dashboard

Streamlit analytics dashboard for the Circular Battery Decision Twin runtime logs and digital battery passports.

## Run

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The dashboard reads:

- `../outputs/inspection_log.csv`
- `../outputs/battery_passports.json`
- `../outputs/latest_decision.json`

Use the sidebar auto-refresh toggle during a Unity demo to watch KPIs update as batteries are inspected.
