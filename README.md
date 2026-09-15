# Kerbl API Client

Ein kleiner Python-Client für die Kerbl-IoT-Backend-API. Der Client übernimmt die Anmeldung, Token-Erneuerung und den Zugriff auf Geräte, Events, Messwerte und Gerätebefehle.

> **Hinweis:** Dieses Projekt ist ein inoffizieller Client. Die verwendeten Endpoints wurden aus der Kerbl-Anwendung abgeleitet und können sich ohne Vorankündigung ändern.

## Funktionen

- Anmeldung mit E-Mail und Passwort
- Automatische Erneuerung des Access-Tokens
- Produktions- und Development-Backend
- Geräte über Namen und optionalen Gerätetyp finden
- Smart Coop, Smart Energizer, Smart Satellite und weitere Gerätetypen
- Events mit Zeit-, Level- und Bestätigungsfiltern
- Kontinuierliche Messwerte abrufen
- Gerätebefehle und Parameter setzen
- Maintenance-Endpunkte wie Ping und Branch-Information

## Voraussetzungen

- Python 3.10 oder neuer
- Ein Kerbl-IoT-Konto
- Zugriff auf das Kerbl-Backend

## Installation

Repository klonen und in das Projektverzeichnis wechseln:

```bash
git clone <DEINE-GITHUB-URL>
cd kerbl_api
```

Abhängigkeit installieren:

```bash
python -m pip install requests
```

Optional empfiehlt sich eine virtuelle Umgebung:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install requests
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install requests
```

## Zugangsdaten konfigurieren

Die Datei `credentials.py` wird durch `.gitignore` vom Repository ausgeschlossen. Lege sie lokal im Projektverzeichnis an:

```python
mail = "deine-email@example.com"
password = "dein-passwort"
```

**Wichtig:** Zugangsdaten niemals committen oder öffentlich auf GitHub hochladen. Prüfen kannst du das mit:

```bash
git status --ignored
```

## Schnellstart

```python
from credentials import mail, password
from kerbl_api import KerblClient

client = KerblClient(
    email=mail,
    password=password,
)

client.login()
print("Erfolgreich angemeldet")

# Alle Geräte und Gerätetypen abrufen
devices = client.list_devices()
print(devices.keys())
```

## Gerät über Namen finden

`get_device_by_name` sucht in den von `list_devices()` gelieferten Listen. Der Anzeigename wird gegen `description` beziehungsweise `name` geprüft. Der Gerätetyp ist optional, aber empfehlenswert, wenn Namen mehrfach vorkommen können.

```python
coop = client.get_device_by_name(
    "Hühnerstall",
    device_type="smart-coop",
)

print("ID:", coop["id"])
print("Name:", coop.get("description"))
print("Online:", coop.get("isOnline"))
```

Folgende Schreibweisen werden akzeptiert:

| Typ für `get_device_by_name` | API-Kategorie |
| --- | --- |
| `smart-coop` oder `smartCoop` | Smart Coop |
| `smart-energizer` oder `smartEnergizer` | Smart Energizer |
| `smart-satellite` oder `smartSatellite` | Smart Satellite |
| `smart-weather` oder `smartWeather` | Smart Weather Station |
| `smart-tracker` oder `smartTracker` | Smart Tracker |
| `smart-mousetrap` oder `smartMouseTrap` | Smart Mousetrap |
| `smart-sos` oder `smartSos` | Smart SOS |
| `smart-light` oder `smartLight` | Smart Light |
| `smart-chickendoor` oder `smartChickenDoor` | Smart Chickendoor |
| `smart-rat-gun` oder `smartRatGun` | Smart Rat Gun |

Nur suchen, ohne direkt die Detaildaten abzurufen:

```python
matches = client.find_devices("Hühnerstall")

for device in matches:
    print(device["id"], device.get("description"))
```

Bei keinem Treffer oder mehreren Treffern wirft `get_device_by_name` einen `LookupError`. In diesem Fall den Namen prüfen oder den Gerätetyp angeben.

## Gerät direkt über ID abrufen

Für Detailabfragen benötigt die API sowohl den Typ als auch die ID:

```python
coop = client.get_coop("DEINE_COOP_ID")

# Allgemein:
device = client.get_device(
    device_type="smart-coop",
    device_id="DEINE_COOP_ID",
)
```

Ein Aufruf wie `get_device("DEINE_ID")` reicht nicht aus, da der API-Pfad typbezogen ist.

## Smart Coop

```python
coop_id = coop["id"]

# Aktuelle Gerätedaten
coop = client.get_coop(coop_id)

# Ereignisprotokoll
log = client.get_coop_log(coop_id)

# Ereignisse mit Zeitraum
from datetime import datetime, timezone

start = datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()
end = datetime(2026, 1, 2, tzinfo=timezone.utc).isoformat()
events = client.get_coop_events(
    coop_id,
    from_time=start,
    to_time=end,
)

# Befehl senden
result = client.send_coop_command(
    coop_id,
    "openDoor",
)

# Kontinuierliche Werte abrufen
values = client.get_coop_continuous_values(
    coop_id,
    "AIR_TEMPERATURE",
    from_time=start,
    to_time=end,
)
```

Schreibbefehle wie `send_coop_command`, `set_coop_parameter` oder `reset_coop_desired_state` verändern den Gerätezustand. Verwende sie zunächst nur mit einem Testgerät und prüfe die verfügbaren Befehlsnamen für deine Firmware.

## Weitere Gerätetypen

Für unterstützte Gerätetypen stehen typbezogene Methoden zur Verfügung:

```python
energizer = client.get_energizer("ENERGIZER_ID")
satellite = client.get_satellite("SATELLITE_ID")
chickendoor = client.get_chickendoor("CHICKENDOOR_ID")
```

Zusätzlich gibt es unter anderem:

- `get_energizer_events`
- `send_energizer_command`
- `get_satellite_events`
- `send_satellite_command`
- `get_chickendoor_events`
- `send_chickendoor_command`
- `get_chickendoor_pending_commands`
- `get_smart_tracker_continuous_values`
- `get_continuous_values`

## Development-Backend

Für das Development-Backend kann die URL explizit gesetzt werden:

```python
client = KerblClient(
    email=mail,
    password=password,
    base_url=KerblClient.DEV_URL,
    environment="dev",
)
```

## Testen

Syntaxprüfung:

```bash
python -m py_compile kerbl_api.py
```

Das mitgelieferte Beispiel ausführen:

```bash
python test_api.py
```

Das Beispiel benötigt eine lokale `credentials.py` und führt echte API-Aufrufe aus. Es sollte daher nur in einer Umgebung mit passenden Zugangsdaten ausgeführt werden.

## Projektstruktur

```text
kerbl_api/
├── kerbl_api.py       # KerblClient und API-Methoden
├── credentials.py     # Lokale Zugangsdaten, nicht versionieren
├── .gitignore
└── README.md
```

## Sicherheit

- `credentials.py`, `.env` und lokale Logs sind in `.gitignore` eingetragen.
- Keine Access- oder Refresh-Tokens in Logs ausgeben.
- Keine Zugangsdaten in Issues, Screenshots oder Beispielen veröffentlichen.
- Bei versehentlich veröffentlichten Zugangsdaten das Passwort sofort ändern.

## Lizenz

Es ist aktuell keine Lizenz festgelegt. Wenn du das Projekt öffentlich weitergeben möchtest, ergänze eine passende Lizenzdatei, zum Beispiel MIT.
