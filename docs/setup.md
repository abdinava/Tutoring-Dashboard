# Setup

## Raspberry Pi (as user `neftali`)

1. Check the system: `cat /etc/os-release`, `python3 --version`, `lsusb | grep 0acd`.
   Stop the old prototype if it's running: `pkill -f main.py`.
2. Install and get the code:
   ```bash
   sudo apt install -y git python3-venv python3-tk
   git clone git@github.com:<you>/tutoring-checkin.git ~/tutoring-checkin
   cd ~/tutoring-checkin/kiosk
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   ```
3. Card reader access without sudo:
   ```bash
   sudo cp deploy/99-rcard-reader.rules /etc/udev/rules.d/
   sudo udevadm control --reload-rules && sudo udevadm trigger
   sudo usermod -aG input neftali        # log out and back in
   ls -l /dev/rcard-reader               # should exist
   ```
4. Settings:
   ```bash
   mkdir -p ~/.config/tutoring-kiosk
   cp .env.example ~/.config/tutoring-kiosk/kiosk.env
   chmod 600 ~/.config/tutoring-kiosk/kiosk.env    # then fill in real values
   ```
5. Test in a window: `set -a; . ~/.config/tutoring-kiosk/kiosk.env; set +a; .venv/bin/python -m tutoring_kiosk.app`
   (Ctrl+Shift+Q quits). Swipe your card; you should see "Is this you?".
6. Start at boot: turn on desktop autologin and turn off screen blanking in
   `sudo raspi-config`, then:
   ```bash
   sudo cp deploy/tutoring-kiosk.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now tutoring-kiosk
   journalctl -u tutoring-kiosk -f
   ```

## Relay (UCR-approved server)

```bash
cd relay
cp .env.example .env && chmod 600 .env     # fill in real values
docker build -t checkin-relay .
docker run -d --restart unless-stopped --env-file .env -p 127.0.0.1:8000:8000 checkin-relay
```

Put an HTTPS reverse proxy (e.g. Caddy or nginx) in front of port 8000.

## Qualtrics

1. Confirm with the professor that UCR's Qualtrics is approved for student records.
2. Use a service account. Note the Datacenter ID and API token (Account Settings > Qualtrics IDs).
3. Create a survey with no questions. In Survey Flow add Embedded Data fields:
   `event_id`, `event_type`, `method`, `student_id`, `course`, `timestamp`, `device_id`.
4. Turn on *Anonymize responses*. Share results with instructors view-only; never use public report links.
