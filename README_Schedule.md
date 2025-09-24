## Streamlit UI
```bash
make ui
# then open the local URL streamlit prints (usually http://localhost:8501)
```

Google Sheets export
• Always writes out/picks/picks_latest.csv.
• To push to a Google Sheet (optional):
1. Create a Service Account in GCP; download JSON key.
2. export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
3. Share your target Sheet with the service account email.
4. make sheets-push (or call the script with --sheet "Your Sheet Name").

---

### quick run (no creds needed)

```bash
make init
make schedule
make preslate
make ui            # optional UI
make sheets        # always writes CSV; Sheets push is optional
```
