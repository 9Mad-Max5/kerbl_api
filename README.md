# Kerbl API Client

Python-Client für die Kerbl-IoT-API. Der Client verwendet das Kerbl-Backend für die Anmeldung und den Zugriff auf Geräte, Events, Messwerte und Gerätebefehle.

Das Projekt ist ein inoffizieller Client. Die API-Endpunkte wurden aus der Kerbl-Anwendung abgeleitet und können sich ändern.

## Voraussetzungen

- Python
- Ein Kerbl-IoT-Konto
- Zugriff auf das Kerbl-Backend

## Installation

```bash
git clone <DEINE-GITHUB-URL>
cd kerbl_api
python -m pip install requests
```

Optional kann eine virtuelle Umgebung verwendet werden:

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

## Zugangsdaten

Im Repository liegt [credentials_example.py](credentials_example.py) als Vorlage:

```python
mail = "your-email@example.com"
password = "your-password"
```

Die Vorlage lokal kopieren:

```powershell
Copy-Item credentials_example.py credentials.py
```

Danach die Platzhalter in `credentials.py` durch die eigenen Kerbl-Zugangsdaten ersetzen. Die Datei `credentials.py` ist in `.gitignore` eingetragen und darf nicht veröffentlicht werden.

## Schnellstart

```python
from credentials import mail, password
from kerbl_api import KerblClient

client = KerblClient(
    email=mail,
    password=password,
)

client.login()
devices = client.list_devices()
print(devices)
```

## Geräte finden

Die API liefert Geräte gruppiert nach Typ. Mit `find_devices` kann nach dem Anzeigenamen gesucht werden:

```python
matches = client.find_devices("Hühnerstall")

for device in matches:
    print(device["id"], device.get("description"))
```

Der Typ kann zusätzlich angegeben werden:

```python
coop = client.get_device_by_name(
    "Hühnerstall",
    device_type="smart-coop",
)

print(coop["id"])
print(coop.get("description"))
print(coop.get("isOnline"))
```

Unterstützte Typbezeichnungen für die Namenssuche sind:

| Schreibweise | Gerät |
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

Für eine Detailabfrage benötigt `get_device` den Typ und die ID:

```python
device = client.get_device(
    device_type="smart-coop",
    device_id=coop["id"],
)
```

Für Smart Coop gibt es außerdem:

```python
coop_id = coop["id"]

details = client.get_coop(coop_id)
log = client.get_coop_log(coop_id)
events = client.get_coop_events(coop_id)
values = client.get_coop_continuous_values(
    coop_id,
    "AIR_TEMPERATURE",
)
```

## Schreibzugriffe

Der Client kann auch Befehle und Parameter an Geräte senden:

```python
result = client.send_coop_command(
    coop["id"],
    "openDoor",
)
```

Weitere vorhandene Methoden für Smart Coop sind unter anderem `set_coop_parameter`, `refresh_coop` und `reset_coop_desired_state`. Diese Methoden können den Gerätezustand verändern. Die verfügbaren Befehle können von Gerät und Firmware abhängen.

## Weitere vorhandene Methoden

Der Client enthält außerdem Methoden für:

- Smart Energizer
- Smart Satellite
- Smart Chickendoor
- Smart Tracker
- allgemeine kontinuierliche Messwerte
- Benutzerprofil und Prepaid-Guthaben
- Passwort- und E-Mail-Funktionen
- Maintenance-Ping und Deployment-Informationen

Die konkreten Methoden befinden sich in [kerbl_api.py](kerbl_api.py).

## Development-Backend

Das Development-Backend kann beim Erstellen des Clients verwendet werden:

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

Das vorhandene Beispielprogramm ausführen:

```bash
python test_api.py
```

`test_api.py` verwendet `credentials.py` und führt echte API-Aufrufe aus. Vor dem Start müssen deshalb lokale Zugangsdaten eingerichtet sein.

## Dateien

```text
kerbl_api/
├── kerbl_api.py            # KerblClient und API-Methoden
├── credentials_example.py  # Vorlage ohne echte Zugangsdaten
├── credentials.py          # Lokale Zugangsdaten, nicht veröffentlichen
├── .gitignore
└── README.md
```

## Sicherheit

- Keine echten Zugangsdaten in Git committen.
- `credentials.py` niemals auf GitHub veröffentlichen.
- Keine Access- oder Refresh-Tokens in Logs ausgeben.
- Bei versehentlich veröffentlichten Zugangsdaten das Passwort ändern.

## Lizenz

Für dieses Projekt ist derzeit keine Lizenz festgelegt.
