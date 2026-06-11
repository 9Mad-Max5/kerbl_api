import requests
import time
from typing import Optional, Dict, Any


class KerblClient:
    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = "https://backend.kerbl-iot.com/api/v0.1",
    ):
        self.base_url = base_url
        self.auth_url = f"{base_url}/auth"

        self.email = email
        self.password = password

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: float = 0

        self.session = requests.Session()

    # ---------------------------
    # AUTH
    # ---------------------------

    def login(self) -> None:
        """Login and store tokens"""
        url = f"{self.auth_url}/sign-in"

        payload = {
            "email": self.email,
            "password": self.password,
        }

        r = self.session.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

        self._store_tokens(data)

    def refresh(self) -> None:
        """Refresh access token"""
        if not self.refresh_token:
            raise RuntimeError("No refresh token available")

        url = f"{self.auth_url}/refresh"

        payload = {
            "refreshToken": self.refresh_token,
        }

        r = self.session.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

        self._store_tokens(data)

    def _store_tokens(self, data: Dict[str, Any]) -> None:
        """
        Expected structure (typical JWT APIs):
        {
            "accessToken": "...",
            "refreshToken": "...",
            "expiresIn": 3600
        }
        """

        self.access_token = data.get("accessToken")
        self.refresh_token = data.get("refreshToken")

        expires_in = data.get("expiresIn", 3600)
        self.token_expiry = time.time() + expires_in - 30  # safety buffer

        if not self.access_token:
            raise RuntimeError("Login failed: no access token received")

    def _ensure_token(self):
        """Auto refresh if needed"""
        if not self.access_token:
            self.login()
        elif time.time() >= self.token_expiry:
            self.refresh()

    # ---------------------------
    # REQUEST HANDLER
    # ---------------------------

    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        self._ensure_token()

        url = f"{self.base_url}{endpoint}"

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        r = self.session.request(method, url, headers=headers, **kwargs)

        # If token expired unexpectedly
        if r.status_code == 401:
            self.refresh()
            headers["Authorization"] = f"Bearer {self.access_token}"
            r = self.session.request(method, url, headers=headers, **kwargs)

        r.raise_for_status()

        if r.text:
            return r.json()
        return {}

    # ---------------------------
    # DEVICE API HELPERS
    # ---------------------------

    def get_device(self, device_id: str):
        return self.request("GET", f"/device/{device_id}")

    def get_coop_log(self, coop_id: str):
        return self.request("GET", f"/device/smart-coop/{coop_id}/log")

    def send_coop_command(self, coop_id: str, command: str):
        return self.request(
            "POST",
            f"/device/smart-coop/{coop_id}/command/{command}",
            json={}
        )

    def get_events(self, device_type: str, device_id: str):
        return self.request(
            "GET",
            f"/device/{device_type}/{device_id}/events"
        )

    def get_continuous_values(self, device_type: str, device_id: str, metric: str):
        return self.request(
            "GET",
            f"/data/{device_type}/{device_id}/{metric}"
        )


# ---------------------------
# EXAMPLE USAGE
# ---------------------------

if __name__ == "__main__":
    from credentials import mail, password
    client = KerblClient(
        email=mail,
        password=password
    )

    client.login()

    # Beispiel: Device holen
    device = client.get_device("DEVICE_ID")
    print(device)

    # Beispiel: Smart Coop Log
    log = client.get_coop_log("COOP_ID")
    print(log)

    # Beispiel: Command senden
    resp = client.send_coop_command("COOP_ID", "openDoor")
    print(resp)