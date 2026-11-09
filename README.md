# PokéVault prototype 0.1

A local-only FastAPI family Pokémon card collection prototype. Manual entry only; no camera recognition or live prices yet.

## Setup (Windows PowerShell)

```powershell
cd path\to\pokevault
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 on the same PC.

## Data

The SQLite database `pokevault.db` is created next to `app.py`. Back up that file to preserve your collection.

## Security

This prototype has no login or access controls. Keep it on 127.0.0.1; do not expose it to the internet or LAN. Phone access will be added only after authentication and HTTPS are implemented.

## Next steps

1. Add login and HTTPS for mobile access.
2. Add camera capture and recognition API with a confirmation screen.
3. Add verified card catalog identifiers and daily price cache.
4. Add duplicate consolidation, export, and backups.
