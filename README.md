# ULA Tutoring Check-In

Students swipe their R'Card at a Raspberry Pi kiosk. Each check-in is saved on
the Pi, sent to a small relay service, and stored in Qualtrics, where
instructors see attendance reports.

```
Pi kiosk (Tkinter + card reader) --HTTPS--> Relay (FastAPI) --> Qualtrics
       saves to local SQLite first          checks token + data
```

## Files

```
kiosk/                     runs on the Raspberry Pi
  tutoring_kiosk/
    app.py                 starts everything
    config.py              reads settings
    rcard.py               gets the student ID from a swipe
    reader.py              reads the card reader
    flow.py                check-in steps (no GUI code)
    ui.py                  the screens
    outbox.py              local queue so nothing is lost offline
    sync.py                sends the queue to the relay
  deploy/                  udev rule + systemd service for the Pi
relay/                     runs on a server
  app/
    main.py                the API
    config.py              reads settings
    models.py              what a valid check-in looks like
    auth.py                checks the kiosk's token
    qualtrics.py           sends to Qualtrics
  Dockerfile
tests/                     automated tests (fake data only)
docs/setup.md              Pi, relay, and Qualtrics setup
```

## Run it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt      # Linux also needs: sudo apt install python3-tk
pytest -q && ruff check .
```

Make a device token and its hash:

```bash
python3 -c "import secrets,hashlib; t=secrets.token_urlsafe(32); print(t); print(hashlib.sha256(t.encode()).hexdigest())"
```

Terminal 1 (relay, not sending to Qualtrics):

```bash
cd relay
export DRY_RUN=true ALLOWED_COURSES='["CS 10A","CS 61"]' DEVICE_TOKEN_HASHES='{"dev-pi":"<hash>"}'
uvicorn app.main:app --port 8001
```

Terminal 2 (kiosk with a fake card reader; press F2 to "swipe"):

```bash
cd kiosk
export RELAY_URL=http://localhost:8001 ALLOW_INSECURE_RELAY=1 DEVICE_ID=dev-pi \
       DEVICE_TOKEN=<token> COURSES="CS 10A,CS 61" DATA_DIR=./data
python -m tutoring_kiosk.app --simulate
```

## Rules

- Keep this repo **private**.
- Never commit `.env` files, `.json` keys, or real student data (`.gitignore` blocks them).
- Never log student IDs, names, or swipe data.
- Commit each small working change; CI runs lint and tests on every push.
